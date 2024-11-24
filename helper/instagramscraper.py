from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from bs4 import BeautifulSoup
import pandas as pd
import time
import json

from .config import init_driver, logger, InstagramLoginError, InvalidCredentialsError
from .llm import evaluate_lead

class InstagramScraper:
    def __init__(self, url, email, password, is_headless):
        self.url = url
        self.email = email
        self.password = password
        self.driver = init_driver(is_headless)
    
    ######################################## Login ########################################
    def _login(self):
        """Log into Instagram and handle potential errors during login."""
        driver = self.driver
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)

        # Handle cookie consent
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow essential and optional cookies')]"))
            )
            cookie_button.click()
        except TimeoutException:
            pass  # Continue if no cookie consent popup

        # Enter credentials
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = driver.find_element(By.NAME, "password")
            username_field.send_keys(self.email)
            password_field.send_keys(self.password)
        except TimeoutException:
            raise InstagramLoginError("Login page elements not found. Possible network issues.")

        # Click login button and check for errors
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
            )
            login_button.click()
            time.sleep(5)

            error_message = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'x1lliihq')]//div[contains(@class, '_ab2z')]"))
            ).text
            raise InvalidCredentialsError(f"Login failed: {error_message}")

        except TimeoutException:
            # Verify successful login by checking URL
            if "login" in driver.current_url:
                raise InstagramLoginError("Login unsuccessful - please check credentials")

        # Wait for any "Save Info" or "Not Now" popups and handle them
        try:
            not_now_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(text(), 'Not Now')]"
                ))
            )
            not_now_button.click()
        except TimeoutException:
            pass
    
    ######################################## Get the content ########################################
    def _get_post_content(self):
        """
        Extracts post content, including caption, likes, and author details.

        Args:
            driver (webdriver): Selenium WebDriver instance.

        Returns:
            dict: Post content and metadata, including author, caption, and likes.
        """
        logger.info("Extracting post content and metadata")
        post_data = {}
        driver = self.driver

        try:
            # Wait for post content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//div[contains(@class, '_aagv')]"  # Post container class
                ))
            )
            
            # Get post author
            try:
                author_element = driver.find_element(
                    By.XPATH,
                    "//span[@class='xt0psk2']//a[contains(@class, 'x1i10hfl')]//span[contains(@class, '_aade')]"
                )
                post_data['author_username'] = author_element.text
                post_data['author_link'] = f"https://www.instagram.com/{post_data['author_username']}/"
            except NoSuchElementException:
                post_data['author_username'] = "Unknown"
                post_data['author_link'] = "N/A"
                logger.warning("Could not find post author")

            # Get post caption
            try:
                caption_element = driver.find_element(
                    By.XPATH,
                    "//span[@class='x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs xt0psk2 x1i0vuye xvs91rp xo1l8bm x5n08af x10wh9bi x1wdrske x8viiok x18hxmgj']"
                )
                post_data['caption'] = caption_element.text
            except NoSuchElementException:
                post_data['caption'] = ""
                logger.warning("Could not find post caption")

            # Get like count
            try:
                likes_element = driver.find_element(
                    By.XPATH,
                    "//span[@class='html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs']"
                )
                post_data['likes_count'] = likes_element.text
            except NoSuchElementException:
                post_data['likes_count'] = None
                logger.warning("Could not find likes count")

            logger.info("Successfully extracted post content and metadata")
            return post_data

        except Exception as e:
            logger.error(f"Error extracting post content: {str(e)}")
            return post_data  # Return what we have, even if incomplete
    
    
    ######################################## Load more comments ########################################
    def _click_load_more_comments(self):
        """Click 'Load more comments' button repeatedly to load all comments"""
        wait_time = 3
        max_attempts = 50
        attempts = 0

        while attempts < max_attempts:
            try:
                load_more_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//button[contains(@class, '_abl-') and contains(.,'Load more comments')]"
                    ))
                )

                if not load_more_button.is_displayed():
                    logger.info("No more comments button visible")
                    break
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", load_more_button)
                logger.info("Clicked 'Load more comments' button")
                time.sleep(wait_time)
                attempts += 1
            except TimeoutException:
                logger.info("No more comments to load")
                break
            except Exception as e:
                logger.error(f"Error loading comments: {str(e)}")
                break
    
    
    ######################################## Extract the comment ########################################
    def _extract_comments(self, soup, post_content):
        """Extracts comments from the BeautifulSoup object and evaluates leads."""
        df_list = []
        script_tags = soup.find_all("script", {"type": "application/json", "data-sjs": True})

        for script_tag in script_tags:
            json_data = script_tag.string
            parsed_data = json.loads(json_data)
            try:
                comments = parsed_data["require"][0][3][0]["__bbox"]["require"][0][3][1]["__bbox"]["result"]["data"]["xdt_api__v1__media__media_id__comments__connection"]["edges"]
                break  # Exit once comments are found
            except (KeyError, IndexError, TypeError):
                continue  # Skip if the path doesn't exist

        for index, comment in enumerate(comments, 1):
            node = comment["node"]
            commenter_name = node["user"].get("username")
            commenter_id = node["user"].get("id")
            commenter_url = f"https://www.instagram.com/{node['user'].get('username')}/"
            comment_text = node.get("text")
            
            is_lead, reason = evaluate_lead(post_content, comment_text, platform='Instagram')
            logger.info(f"Processing comment {index}/{len(comments)}")
            
            df_list.append({
                "Name": commenter_name,
                "ID": commenter_id,
                "Link": commenter_url,
                "Comment Content": comment_text,
                "Is Lead": is_lead,
                "Reason": reason,
            })
        return pd.DataFrame(df_list)

    
    ######################################## Main scraping function ########################################
    def scrape(self):
        """
        Main function to scrape Instagram post and comments.
        
        Args:
            url (str): Instagram post URL.
            email (str): Instagram login email.
            password (str): Instagram login password.
        """
        driver = self.driver
        try:
            self._login()
            driver.get(self.url)
            time.sleep(5)
            post_data = self._get_post_content()
            
            self._click_load_more_comments()

            soup = BeautifulSoup(driver.page_source, "html.parser")
            comments_df = self._extract_comments(soup, post_data['caption'])

            logger.info(f"Successfully processed {len(comments_df)} comments")
            return comments_df

        except (InvalidCredentialsError, InstagramLoginError) as e:
            logger.error(f"Login error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {str(e)}")
            raise
        finally:
            driver.quit()
            logger.info("Browser closed")