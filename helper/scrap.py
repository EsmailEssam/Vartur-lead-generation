import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from .llm import evaluate_lead

# Configure logging
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

def get_driver(headless=True):
    """Initialize undetected-chromedriver with appropriate options"""
    options = uc.ChromeOptions()
    
    if headless:
        options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    
    # Add stealth options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    return uc.Chrome(options=options)

def click_load_more_comments(driver):
    """Click 'Load more comments' button with enhanced reliability"""
    wait_time = 3
    max_attempts = 50
    attempts = 0
    
    while attempts < max_attempts:
        try:
            load_more_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//button[contains(@class, 'comments-comments-list__load-more-comments-button') and contains(.,'Load more comments')]"
                ))
            )
            
            if not load_more_button.is_displayed():
                logger.info("No more comments button visible")
                break
                
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            time.sleep(1)
            
            try:
                driver.execute_script("arguments[0].click();", load_more_button)
                logger.info("Clicked 'Load more comments' button")
                time.sleep(wait_time)
                attempts += 1
            except Exception as e:
                logger.error(f"Failed to click button: {str(e)}")
                break
                
        except TimeoutException:
            logger.info("No more comments to load")
            break
        except Exception as e:
            logger.error(f"Error loading comments: {str(e)}")
            break


def scraper(url, email, password, headless=True):
    """Scrape LinkedIn post comments with enhanced reliability"""
    driver = None
    try:
        logger.info("Initializing Chrome driver...")
        driver = get_driver(headless=headless)
        
        # Handle login
        logger.info("Navigating to LinkedIn login page...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        
        logger.info("Entering credentials...")
        username_field.send_keys(email)
        password_field.send_keys(password)
        
        sign_in_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
        )
        sign_in_button.click()
        
        # Wait for successful login or error
        try:
            WebDriverWait(driver, 30).until(
                lambda x: "feed" in x.current_url or 
                         x.find_elements(By.ID, "error-for-username") or 
                         x.find_elements(By.ID, "error-for-password")
            )
        except TimeoutException:
            raise LinkedInLoginError("Login process timeout")
        
        # Check for error messages
        error_elements = driver.find_elements(By.CLASS_NAME, "alert-content")
        if error_elements:
            raise InvalidCredentialsError(error_elements[0].text)
        
        logger.info("Successfully logged in")
        
        # Navigate to post URL
        logger.info(f"Navigating to post: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Load all comments
        logger.info("Loading comments...")
        click_load_more_comments(driver)
        
        # Extract data
        logger.info("Extracting comment data...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        comments = soup.find_all("article", {"class": "comments-comment-entity"})
        logger.info(f"Found {len(comments)} comments")
        
        df_list = []
        for index, comment in enumerate(comments, 1):
            try:
                name = comment.find("span", class_="comments-comment-meta__description-title").text.strip()
                header = comment.find("div", class_="comments-comment-meta__description-subtitle").text.strip()
                link = comment.find("a", class_="app-aware-link")
                link = link["href"] if link else "N/A"
                content = comment.find("span", class_="comments-comment-item__main-content").text.strip()
                
                logger.info(f"Processing comment {index}/{len(comments)}")
                is_lead, reason = evaluate_lead(header, content)
                
                df_list.append({
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
        return pd.DataFrame(df_list)
        
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")
