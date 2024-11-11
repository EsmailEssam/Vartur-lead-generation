from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options

from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import json

from llm import evaluate_lead

# Configure console-only logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InstagramLoginError(Exception):
    """Custom exception for Instagram login failures"""
    pass

class InvalidCredentialsError(InstagramLoginError):
    """Specific exception for invalid credentials"""
    pass

def click_load_more_comments(driver):
    """
    Click 'Load more comments' button until all comments are loaded.
    
    Args:
        driver: Selenium WebDriver instance
    """
    pass


def get_post_content(driver):
    """
    Extract post content including caption, likes, date, and other metadata.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        dict: Post content and metadata
    """
    logger.info("Extracting post content and metadata")
    
    try:
        # Wait for post content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH, 
                "//div[contains(@class, '_aagv')]"  # Post container class
            ))
        )
        
        post_data = {}
        
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
        print(post_data)
        return post_data

    except Exception as e:
        logger.error(f"Error extracting post content: {str(e)}")
        return {}


def scraper(url, username, password):
    """
    Scrape Instagram post comments with enhanced error handling and credential validation.
    
    Args:
        url (str): Instagram post URL to scrape
        username (str): Instagram login username
        password (str): Instagram login password
    
    Returns:
        pandas.DataFrame: Scraped data
    """
    firefox_options = Options()
    # firefox_options.add_argument("--headless")
    firefox_options.add_argument("--disable-gpu")
    firefox_options.add_argument("--no-sandbox")
    
    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=firefox_options
    )

    try:
        # Navigate to Instagram login page
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)
        
        # Handle cookie consent if present
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow essential and optional cookies')]"))
            )
            cookie_button.click()
        except TimeoutException:
            pass
        
        # Wait for and validate login fields
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = driver.find_element(By.NAME, "password")
        except TimeoutException:
            raise InstagramLoginError("Login page elements not found. Possible network issues.")
        
        # Input credentials
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Click login button
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[@type="submit"]')
                )
            )
            login_button.click()
        except TimeoutException:
            raise InstagramLoginError("Login button not clickable")
        
        # Check for login errors
        time.sleep(5)
        try:
            error_message = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//span[contains(@class, 'x1lliihq')]//div[contains(@class, '_ab2z')]"
                ))
            ).text
            raise InvalidCredentialsError(f"Login failed: {error_message}")
        except TimeoutException:
            # No error found, continue with login
            pass
        
        # Additional check to ensure we're logged in
        try:
            WebDriverWait(driver, 10).until(
                lambda x: "login" not in x.current_url
            )
        except TimeoutException:
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
        
        # Navigate to post URL
        driver.get(url)
        time.sleep(5)
        
        # First, get post content
        post_data = get_post_content(driver)
        
        # Then proceed with comments scraping
        # click_load_more_comments(driver)
        
        # Get the page source and create BeautifulSoup object
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract comment data
        df_list = []
        comments = soup.find_all(
            "div",
            {
                "class": "x9f619 xjbqb8w x78zum5 x168nmei x13lgxp2 x5pf9jr xo71vjh x1uhb9sk x1plvlek xryxfnj x1c4vz4f x2lah0s xdt5ytf xqjyukv x1qjc9v5 x1oa3qoh x1nhvcw1"
            }
        )
        
        script_tags = soup.find_all("script", {"type": "application/json", "data-sjs": True})
        
        # Loop through each script tag to find the one containing comments
        comments_data = None
        for script_tag in script_tags:
            json_data = script_tag.string
            parsed_data = json.loads(json_data)  # Parse the JSON data

            # Check if this script contains the comments by looking for the unique path
            try:
                comments = parsed_data["require"][0][3][0]["__bbox"]["require"][0][3][1]["__bbox"]["result"]["data"]["xdt_api__v1__media__media_id__comments__connection"]["edges"]
                comments_data = comments
                break  # Exit the loop once the correct script is found
            except (KeyError, IndexError, TypeError):
                # If the path does not exist in this script, continue to the next one
                continue
        
        logger.info(f"Found {len(comments)} comments to process")
        for comment in comments:
            try:
                node = comment["node"]
                commenter_name = node["user"].get("username")
                commenter_id = node["user"].get("id")
                commenter_url = f"https://www.instagram.com/{node['user'].get('username')}/"
                comment_text = node.get("text")
                
                is_lead, reason = evaluate_lead(post_data['caption'], comment_text)
                
                new_row = {
                    "Name": commenter_name,
                    "ID": commenter_id,
                    "Link": commenter_url,
                    "Comment Content": comment_text,
                    "Is Lead": is_lead,
                    "Reason": reason,
                }
                df_list.append(new_row)
                
            except Exception as comment_exception:
                logger.error(f"Error processing comment: {comment_exception}")
                continue
        
        logger.info(f"Successfully processed {len(df_list)} comments")
        return post_data, pd.DataFrame(df_list)
        
    except InvalidCredentialsError:
        logger.error("Invalid credentials provided")
        raise
    except InstagramLoginError as e:
        logger.error(f"Login error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {str(e)}")
        raise Exception(f"Unexpected error during scraping: {str(e)}")
    finally:
        driver.quit()
