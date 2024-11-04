from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from llm import evaluate_lead

def scraper(url):
    # Initialize the WebDriver (Assuming you're using Chrome)
    driver = webdriver.Chrome()

    try:
        # Load the LinkedIn post HTML
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'p[data-test-id="main-feed-activity-card__commentary"]')))
        
        # Get the page source and create a BeautifulSoup object
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Scrape Post Content
        post_content = soup.find('p', {'data-test-id': 'main-feed-activity-card__commentary'}).get_text(strip=True)

        # Scrape Profile Link and Commenter Details
        comments = soup.find_all('section', class_='comment')
        df_list = []  # Collect data in a list

        for comment in comments:
            try:
                # Commenter's name and header
                commenter_name = comment.find('a', {'data-tracking-control-name': 'public_post_comment_actor-name'}).get_text(strip=True)
                commenter_header = comment.find('p', class_='!text-xs text-color-text-low-emphasis leading-[1.33333] mb-0.5 truncate comment__author-headline').get_text(strip=True)
                commenter_link = comment.find('a', {'data-tracking-control-name': 'public_post_comment_actor-image'})['href']
                
                # Comment content
                comment_content = comment.find('p', class_='attributed-text-segment-list__content').get_text(strip=True)
                
                # Find is he a lead or not and the reason
                is_lead, reason = evaluate_lead(post_content, commenter_header, comment_content)
                
                # add lead to dataframe
                new_row = {'Name': commenter_name, 'Link': commenter_link, 'Header': commenter_header, 
                            'Comment Content': comment_content, 'Is Lead': is_lead, 'Reason': reason}
                
                df_list.append(new_row)

            except Exception as comment_exception:
                print(f"Error processing comment: {comment_exception}")

        # Create DataFrame
        df = pd.DataFrame(df_list)

    except Exception as e:
        print(f"An error occurred while scraping: {e}")
        df = pd.DataFrame(columns=['Name', 'Link', 'Header', 'Comment Content', 'Is Lead', 'Reason'])
        post_content = ""

    finally:
        # Close the WebDriver
        driver.quit()

    return post_content, df



# post_url = "https://www.linkedin.com/posts/abdulrahman-baqais_learn-data-science-with-our-online-courses-activity-7258048996340887553-ujpf?utm_source=share&utm_medium=member_desktop"



# post_content, df = scraper(post_url)


# print(post_content)
# print(df)