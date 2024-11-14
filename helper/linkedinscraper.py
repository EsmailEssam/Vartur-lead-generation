import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from bs4 import BeautifulSoup
import pandas as pd
import time

from .config import logger, LinkedInLoginError, InvalidCredentialsError
from .llm import evaluate_lead

def initialize_driver(headless=False):
    """Initialize undetected Chrome driver with specified options"""
    options = uc.ChromeOptions()
    
    if headless:
        options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    logger.info("Initializing Chrome driver...")
    return uc.Chrome(options=options)

class LinkedInScraper:
    def __init__(self, url, email, password, headless):
        self.url = url
        self.email = email
        self.password = password
        self.driver = initialize_driver(headless)

    ######################################## Login ########################################
    def _login(self):
        """Perform login on LinkedIn"""
        logger.info("Navigating to LinkedIn login page...")
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)

        try:
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            username_field.send_keys(self.email)
            password_field.send_keys(self.password)
            sign_in_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
            )
            sign_in_button.click()
            
            # Check for successful login or error
            WebDriverWait(self.driver, 30).until(
                lambda x: "feed" in x.current_url or 
                x.find_elements(By.ID, "error-for-username") or 
                x.find_elements(By.ID, "error-for-password")
            )
            
            error_elements = self.driver.find_elements(By.CLASS_NAME, "alert-content")
            if error_elements:
                raise InvalidCredentialsError(error_elements[0].text)
                
            logger.info("Successfully logged in")
        except TimeoutException:
            raise LinkedInLoginError("Login process timeout")
        except InvalidCredentialsError as e:
            logger.error(f"Login error: {e}")
            raise
    
    ######################################## Go to the post ########################################
    def _navigate_to_post(self, url):
        """Navigate to the specific LinkedIn post"""
        logger.info(f"Navigating to post: {url}")
        self.driver.get(url)
        time.sleep(5)

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
                        "//button[contains(@class, 'comments-comments-list__load-more-comments-button') and contains(.,'Load more comments')]"
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
    def _extract_comments(self):
        """Extract comments data from the post"""
        logger.info("Extracting comment data...")
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        comments = soup.find_all("article", {"class": "comments-comment-entity"})
        logger.info(f"Found {len(comments)} comments")

        data = []
        for index, comment in enumerate(comments, 1):
            try:
                name = comment.find("span", class_="comments-comment-meta__description-title").text.strip()
                header = comment.find("div", class_="comments-comment-meta__description-subtitle").text.strip()
                link = comment.find("a", class_="app-aware-link")
                link = link["href"] if link else "N/A"
                content = comment.find("span", class_="comments-comment-item__main-content").text.strip()
                
                logger.info(f"Processing comment {index}/{len(comments)}")
                is_lead, reason = evaluate_lead(header, content, platform='LinkedIn')
                
                data.append({
                    "Name": name,
                    "Link": link,
                    "Header": header,
                    "Comment Content": content,
                    "Is Lead": is_lead,
                    "Reason": reason
                })
            except Exception as e:
                logger.error(f"Error processing comment {index}: {str(e)}")
                continue

        logger.info("Successfully processed all comments")
        return pd.DataFrame(data)

    ######################################## Main scraping function ########################################
    def scrape(self):
        """Main function to perform the scraping process"""
        try:
            self._login()
            self._navigate_to_post(self.url)
            self._click_load_more_comments()
            return self._extract_comments()
        finally:
            self.driver.quit()
            logger.info("Browser closed")

