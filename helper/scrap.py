from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import pandas as pd


def scraper(url):

    # Initialize the WebDriver (Assuming you're using Chrome)
    driver = webdriver.Chrome()

    # Load the LinkedIn post HTML (Replace with the actual URL if needed)
    driver.get(url)
    time.sleep(5)  # Wait for the page to load completely

    # Get the page source and create a BeautifulSoup object
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # **3. Scrape Post Content**
    post_content = soup.find('p', {'data-test-id': 'main-feed-activity-card__commentary'}).get_text(strip=True)

    # **4. Scrape Profile Link and Commenter Details**
    comments = soup.find_all('section', class_='comment')

    df = pd.DataFrame({'Name':[''], 'Link':[''], 'Header':[''], 'Comment Content':['']})

    for comment in comments:
        # Commenter's name and header
        commenter_name = comment.find('a', {'data-tracking-control-name': 'public_post_comment_actor-name'}).get_text(strip=True)
        commenter_header = comment.find('p', class_='!text-xs text-color-text-low-emphasis leading-[1.33333] mb-0.5 truncate comment__author-headline').get_text(strip=True)
        commenter_link = comment.find('a', {'data-tracking-control-name': 'public_post_comment_actor-image'})['href']
        
        # Comment content
        comment_content = comment.find('p', class_='attributed-text-segment-list__content').get_text(strip=True)
        
        new_row = {'Name':commenter_name, 'Link':commenter_link, 'Header':commenter_header, 'Comment Content':comment_content}
        
        df = df._append(new_row, ignore_index=True)

    # **5. Close the WebDriver**
    driver.quit()
    
    return post_content, df


# post_url = "https://www.linkedin.com/posts/abdulrahman-baqais_learn-data-science-with-our-online-courses-activity-7258048996340887553-ujpf?utm_source=share&utm_medium=member_desktop"



# post_content, df = scraper(post_url)


# print(post_content)
# print(df)