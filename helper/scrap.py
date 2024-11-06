from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import chromedriver_autoinstaller
import logging

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

    # Install `chromedriver` automatically
    chromedriver_autoinstaller.install()
    
    # Set up Chrome options for headless operation
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize the WebDriver
    chrome_options.binary_location = "packages.txt/google-chrome-stable"
    # driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


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
        time.sleep(5)
        
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
