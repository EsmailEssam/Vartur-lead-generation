from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from llm import evaluate_lead

def scraper(url, email, password):
    
    # Initialize the WebDriver (Assuming you're using Chrome)
    driver = webdriver.Chrome()

    try:
        # Step 1: Navigate to LinkedIn's login page
        driver.get("https://www.linkedin.com/login")
        
        # Wait for the login fields to load and input credentials
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'username')))
        driver.find_element(By.ID, 'username').send_keys(email)
        driver.find_element(By.ID, 'password').send_keys(password)
        
        # Click on the 'Sign in' button
        sign_in_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and contains(., "Sign in")]'))
        )
        sign_in_button.click()
        print("Signed IN")
        # Step 2: Wait for user to manually input OTP
        WebDriverWait(driver, 120).until(EC.url_contains("feed"))

        # Step 3: Navigate to the post URL after successful login and OTP verification
        driver.get(url)

        # Wait for the comments section to load
        # WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'section.comment')))
        time.sleep(5)
        print('Comments loaded *****************')

        # Get the page source and create a BeautifulSoup object
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extracting comment data: Initialize an empty list to store comment information
        df_list = []

        # Finding each comment section on the page
        comments = soup.find_all('article', {'class': 'comments-comment-entity'})

        for comment in comments:
            try:
                # Extract the commenter's name
                commenter_name = comment.find('span', class_='comments-comment-meta__description-title').get_text(strip=True)

                # Extract the commenter's headline (like role/title)
                commenter_header = comment.find('div', class_='comments-comment-meta__description-subtitle').get_text(strip=True)

                # Extract the profile link of the commenter
                commenter_link = comment.find('a', class_='app-aware-link')['href'] if comment.find('a', class_='app-aware-link') else 'N/A'

                # Extract the main content of the comment
                comment_content = comment.find('span', class_='comments-comment-item__main-content').get_text(strip=True)
                
                # Find if they are a lead and the reason
                is_lead, reason = evaluate_lead(commenter_header, comment_content)
                
                # Add lead to DataFrame
                new_row = {'Name': commenter_name, 'Link': commenter_link, 'Header': commenter_header, 
                           'Comment Content': comment_content, 'Is Lead': is_lead, 'Reason': reason}
                
                df_list.append(new_row)

            except Exception as comment_exception:
                print(f"Error processing comment: {comment_exception}")

        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(df_list)

    except Exception as e:
        print(f"An error occurred while scraping: {e}")
        # Return an empty DataFrame if an error occurs
        df = pd.DataFrame(columns=['Name', 'Link', 'Header', 'Comment Content','Is Lead','Reason'])

    return df