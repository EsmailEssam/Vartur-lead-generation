import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from .llm import evaluate_lead

class XLoginError(Exception):
    """Custom exception for X login errors"""
    pass

class InvalidCredentialsError(Exception):
    """Custom exception for invalid credentials"""
    pass

class XScraper:
    def __init__(self, url, email, password, is_headless=False):
        self.url = url
        self.email = email
        self.password = password
        self.driver = self._initialize_driver(is_headless)
        
    def _initialize_driver(self, is_headless):
        """Initialize undetected Chrome driver with specified options"""
        options = uc.ChromeOptions()
        
        if is_headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        return uc.Chrome(options=options)

    def _login(self):
        """Perform login on X"""
        try:
            self.driver.get("https://X.com/i/flow/login")
            time.sleep(3)

            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']"))
            )
            email_field.send_keys(self.email)
            
            # Click next
            next_button = self.driver.find_element(By.XPATH, "//span[text()='Next']")
            next_button.click()
            time.sleep(2)

            # Handle possible username verification
            try:
                username_verify = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']"))
                )
                username_verify.send_keys(self.email.split('@')[0])
                next_button = self.driver.find_element(By.XPATH, "//span[text()='Next']")
                next_button.click()
                time.sleep(2)
            except TimeoutException:
                pass

            # Enter password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))
            )
            password_field.send_keys(self.password)
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//span[text()='Log in']")
            login_button.click()
            time.sleep(5)

            # Check for successful login
            if "login" in self.driver.current_url:
                error_message = self.driver.find_element(By.XPATH, "//span[contains(@class, 'error-message')]").text
                raise InvalidCredentialsError(error_message)

        except TimeoutException:
            raise XLoginError("Login process timeout")
        except Exception as e:
            raise XLoginError(f"Login failed: {str(e)}")

    def _navigate_to_post(self):
        """Navigate to the specific X post"""
        self.driver.get(self.url)
        time.sleep(5)

    def _scroll_to_load_comments(self):
        """Scroll down to load more comments"""
        last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
        scroll_pause_time = 2
        max_scrolls = 50
        scrolls = 0

        while scrolls < max_scrolls:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(scroll_pause_time)
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            
            # Break if no more content loaded
            if new_height == last_height:
                break
                
            last_height = new_height
            scrolls += 1

    def _extract_comments(self):
        """Extract comments data from the post"""
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        comments = soup.find_all('article', {'data-testid': 'tweet'})
        
        data = []
        for comment in comments:
            try:
                # Skip the main tweet
                if comment.find('a', {'aria-label': 'Profile Tweet time'}):
                    continue
                
                # Extract user info
                user_info = comment.find('div', {'data-testid': 'User-Name'})
                name = user_info.find('span', {'class': re.compile(r'css-.*')}).text.strip()
                username = user_info.find('a', {'role': 'link'})['href'].strip('/')
                
                # Extract comment content
                content = comment.find('div', {'data-testid': 'tweetText'})
                content_text = content.get_text() if content else ""
                
                link = f"https://X.com/{username}/status/{comment['data-tweet-id']}" if 'data-tweet-id' in comment.attrs else "N/A"
                is_lead, reason = evaluate_lead(content, content_text, platform='X')
                data.append({
                    'Name': name,
                    'Username': username,
                    'Profile Link':f"https://x.com/{username}",
                    'Comment Content': content_text,
                    'Link': link,
                    "Is Lead": is_lead,
                    "Reason": reason,
                })
                
            except Exception as e:
                print(f"Error processing comment: {str(e)}")
                continue
                
        return pd.DataFrame(data)

    def scrape(self):
        """Main function to perform the scraping process"""
        try:
            self._login()
            self._navigate_to_post()
            self._scroll_to_load_comments()
            return self._extract_comments()
        finally:
            self.driver.quit()

