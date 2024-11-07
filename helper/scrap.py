from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import time
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
import logging
from llm import evaluate_lead

# Configure console-only logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInLoginError(Exception):
    """Custom exception for LinkedIn login failures"""
    pass

class InvalidCredentialsError(LinkedInLoginError):
    """Specific exception for invalid credentials"""
    pass


def click_load_more_comments(driver):
    """
    Click 'Load more comments' button until all comments are loaded.
    
    Args:
        driver: Selenium WebDriver instance
    """
    logger.info("Checking for additional comments to load")
    
    # Initial wait time between clicks (in seconds)
    wait_time = 3
    max_attempts = 50  # Maximum number of attempts to prevent infinite loops
    attempts = 0
    
    while attempts < max_attempts:
        try:
            # Wait for either the button to be clickable or determine it doesn't exist
            load_more_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//button[contains(@class, 'comments-comments-list__load-more-comments-button--cr') and contains(.,'Load more comments')]"
                ))
            )
            
            # Check if button is visible and enabled
            if not load_more_button.is_displayed() or not load_more_button.is_enabled():
                logger.info("No more comments to load")
                break
                
            # Scroll button into view
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            time.sleep(1)  # Short pause after scrolling
            
            # Click the button
            try:
                load_more_button.click()
                logger.info("Clicked 'Load more comments' button")
                time.sleep(wait_time)  # Wait for new comments to load
                attempts += 1
            except Exception as click_error:
                # If regular click fails, try JavaScript click
                try:
                    driver.execute_script("arguments[0].click();", load_more_button)
                    logger.info("Clicked 'Load more comments' button using JavaScript")
                    time.sleep(wait_time)
                    attempts += 1
                except Exception as js_click_error:
                    logger.error(f"Failed to click button: {str(js_click_error)}")
                    break
                    
        except TimeoutException:
            logger.info("No more 'Load more comments' button found")
            break
        except Exception as e:
            logger.error(f"Error while loading more comments: {str(e)}")
            break
            
    if attempts >= max_attempts:
        logger.warning(f"Reached maximum number of attempts ({max_attempts}) to load comments")


def scraper(url, email, password):
    """
    Scrape LinkedIn post comments with enhanced error handling and credential validation.
    
    Args:
        url (str): LinkedIn post URL to scrape
        email (str): LinkedIn login email
        password (str): LinkedIn login password
    
    Returns:
        pandas.DataFrame: Scraped data
    """

    # Set up Firefox options for headless operation
    firefox_options = Options()
    # firefox_options.add_argument("--headless")
    firefox_options.add_argument("--disable-gpu")
    firefox_options.add_argument("--no-sandbox")

    # Initialize the WebDriver with GeckoDriverManager
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=firefox_options)


    try:
        # Step 1: Navigate to LinkedIn login page
        driver.get("https://www.linkedin.com/login")
        
        # Wait for and validate login fields
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = driver.find_element(By.ID, "password")
        except TimeoutException:
            raise LinkedInLoginError("Login page elements not found. Possible network issues.")
        
        # Input credentials
        username_field.send_keys(email)
        password_field.send_keys(password)
        
        # Click sign in button
        try:
            sign_in_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[@type="submit" and contains(., "Sign in")]')
                )
            )
            sign_in_button.click()
        except TimeoutException:
            raise LinkedInLoginError("Sign in button not clickable")
        
        # Check for login errors (incorrect credentials)
        try:
            # Check for various error messages that LinkedIn might show
            error_selectors = [
                (By.ID, "error-for-username"),
                (By.ID, "error-for-password"),
            ]
            
            for selector in error_selectors:
                try:
                    error_element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located(selector)
                    )
                    error_text = error_element.text.strip()
                    if error_text:
                        raise InvalidCredentialsError(f"Login failed: {error_text}")
                except TimeoutException:
                    continue
                    
        except TimeoutException:
            # No error messages found, continue with login process
            pass
        
        # Wait for OTP verification if required
        try:
            WebDriverWait(driver, 100).until(EC.url_contains("feed"))
        except TimeoutException:
            raise LinkedInLoginError("OTP verification timeout or login unsuccessful")
        
        # Navigate to post URL and scrape content
        driver.get(url)
        
        # Wait for the page to load
        time.sleep(5)
        
        # Load all comments before scraping
        click_load_more_comments(driver)
        
        # Get the page source and create a BeautifulSoup object
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extracting comment data
        df_list = []
        comments = soup.find_all("article", {"class": "comments-comment-entity"})
        logger.info(f"Found {len(comments)} comments to process")
        
        for comment in comments:
            try:
                commenter_name = comment.find(
                    "span", class_="comments-comment-meta__description-title"
                ).get_text(strip=True)
                
                commenter_header = comment.find(
                    "div", class_="comments-comment-meta__description-subtitle"
                ).get_text(strip=True)
                
                commenter_link = (
                    comment.find("a", class_="app-aware-link")["href"]
                    if comment.find("a", class_="app-aware-link")
                    else "N/A"
                )
                
                comment_content = comment.find(
                    "span", class_="comments-comment-item__main-content"
                ).get_text(strip=True)
                
                is_lead, reason = evaluate_lead(commenter_header, comment_content)
                
                new_row = {
                    "Name": commenter_name,
                    "Link": commenter_link,
                    "Header": commenter_header,
                    "Comment Content": comment_content,
                    "Is Lead": is_lead,
                    "Reason": reason,
                }
                df_list.append(new_row)
            except Exception as comment_exception:
                logger.error(f"Error processing comment: {comment_exception}")
                continue
        
        logger.info(f"Successfully processed {len(df_list)} comments")
        return pd.DataFrame(df_list)
        
    except InvalidCredentialsError:
        logger.error("Invalid credentials provided")
        raise
    except LinkedInLoginError as e:
        logger.error(f"Login error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {str(e)}")
        raise Exception(f"Unexpected error during scraping: {str(e)}")
    finally:
        driver.quit()
