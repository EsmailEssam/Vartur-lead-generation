


# Social Media Lead Generation

## Overview

Social Media Lead Generation is a web application built using Streamlit that helps users extract potential leads from social media posts, specifically from LinkedIn, (Instagram, and X, Soon to be implemented). Users can input their credentials and a post URL to generate a list of potential leads based on the post's content.

## Features

- **Platform Selection**: Currently supports lead generation from LinkedIn.
- **User Authentication**: Allows users to log in using their LinkedIn credentials.
- **Data Extraction**: Scrapes potential leads from specified LinkedIn post URLs.
- **CSV Export**: Users can download the extracted leads as a CSV file.
- **User-friendly Interface**: Simple and intuitive design for ease of use.

## Technologies Used

- Python
- Streamlit
- Pandas
- BeautifulSoup (or any other web scraping library used in the scraper)
- HTML/CSS for styling

## Installation

To set up this project locally, follow these steps:

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Mu-Magdy/Vartur-lead-generation.git
   cd Vartur-lead-generation

   ```

2. **Create a Virtual Environment (optional but recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the Required Packages**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Application**

   Start the Streamlit app by executing the following command:

   ```bash
   streamlit run main.py
   ```

2. **Interact with the Application**

   - Select the platform (currently only LinkedIn).
   - Enter your LinkedIn credentials and the URL of the LinkedIn post you wish to scrape.
   - Click on the "Generate" button to extract potential leads.
   - Download the results as a CSV file if needed.

## Help Section

The help section provides a brief guide on how to use the application:

- Enter your credentials and a post URL in the text box.
- Click on **Generate** to extract potential leads.
- Download the data as a CSV file if needed.

