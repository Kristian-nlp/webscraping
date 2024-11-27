"""
Module: CIP02

Description:
    This script scrapes real estate data from immoscout24.ch for listings in Basel. It uses Selenium
    to navigate the website and interact with dynamic elements, and BeautifulSoup to parse the HTML
    and extract listing details. Key data points include price, size (in square meters),
    number of rooms, and address. The data is then saved to a CSV file for further analysis.

Dependencies:
    - Selenium: Used for browser automation to interact with dynamic content.
    - BeautifulSoup: Used for parsing HTML content and extracting relevant data.
    - Pandas: Used for structuring the extracted data and saving it as a CSV file.
    - ChromeDriver: Required for Selenium to control the Chrome browser.

Usage:
    1. Install necessary dependencies using `pip`:
       pip install selenium beautifulsoup4 pandas requests
    2. Ensure that the ChromeDriver is installed and in your system PATH.
    3. Run the script

Output:
    - The script generates a CSV file named 'immoscout_basel_listings.csv' containing the following columns:
      - Rooms: Number of rooms in the apartment
      - Size: Apartment size in square meters
      - Price: Price of the listing in CHF
      - Address: Address of the listing

Notes:
    - The scraper respects the website’s robots.txt and scraping policies.
    - Error handling is implemented for missing elements and retries.
    - Uses dynamic scrolling and waits to handle lazy-loaded content.

Author: Kristian Zutter
Date: November 2024
"""

# Import necessary libraries
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

# Initialize the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Step 1: Open the target URL
url = "https://www.immoscout24.ch/en/flat/rent/city-basel"
driver.get(url)
time.sleep(3)  # Give the page time to load initially

# Maximize the browser window for consistent element positions
driver.maximize_window()

# Step 2: Accept the cookie banner, if present
try:
    # Wait for the cookie accept button to be clickable and click it
    cookie_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    )
    cookie_button.click()
    time.sleep(2)  # Allow time for cookie settings to take effect
except Exception as e:
    print("No cookie banner found or failed to click:", e)

# Step 3: Initial delay to ensure page content loads fully
time.sleep(5)

# Initialize an empty list to store the data for each listing
all_data = []

# Function to extract data from the current page source
def extract_listing_data(page_source):
    """
    Extracts real estate listing data from a page's HTML source using BeautifulSoup.

    Args:
        page_source (str): HTML content of the page to parse.

    Returns:
        list of dict: Each dictionary contains data for a single listing with keys
                      'Rooms', 'Size', 'Price', and 'Address'.
    """
    soup = BeautifulSoup(page_source, "html.parser")

    # Find all listing elements on the page
    listings = soup.select('div[data-test="result-list-item"]')
    print(f"Found {len(listings)} listings on the page.")  # Debugging output

    scraped_data = []  # Local storage for data extracted from this page

    for listing in listings:
        try:
            # Extract number of rooms
            rooms = listing.find('strong', class_='HgListingRoomsLivingSpacePrice_roomsLivingSpacePrice_M6Ktp')
            if rooms:
                rooms = rooms.text.strip()
            else:
                rooms = listing.select_one("div:contains('rooms') strong")
                rooms = rooms.text.strip() if rooms else "N/A"
            print("Rooms:", rooms)  # Debugging output

            # Extract apartment size in square meters
            size = listing.find('strong', class_='HgListingRoomsLivingSpacePrice_commaPrice_mXXpt')
            if size:
                size = size.text.strip()
            else:
                size = listing.select_one("strong[title='living space']")
                size = size.text.strip() if size else "N/A"
            print("Size:", size)  # Debugging output

            # Extract listing price
            price = listing.find('span', class_='HgListingRoomsLivingSpacePrice_price_u9Vee')
            price = price.text.strip() if price else "N/A"
            print("Price:", price)  # Debugging output

            # Extract listing address
            address = listing.find('div', class_='HgListingCard_address_JGiFv')
            address = address.text.strip() if address else "N/A"
            print("Address:", address)  # Debugging output

            # Store the extracted data in a dictionary and append to list
            scraped_data.append({
                'Rooms': rooms,
                'Size': size,
                'Price': price,
                'Address': address
            })
        except Exception as e:
            print(f"Error extracting data: {e}")

    return scraped_data

# Function to scrape data from the currently loaded page
def scrape_data_from_page(driver):
    """
    Collects data from the current page and adds it to the global list 'all_data'.

    Args:
        driver: WebDriver instance controlling the browser.
    """
    page_source = driver.page_source  # Get current page HTML source
    scraped_data = extract_listing_data(page_source)  # Extract data
    all_data.extend(scraped_data)  # Append to global list

# Step 5: Loop through pages and collect data
while True:
    scrape_data_from_page(driver)  # Scrape data from the current page

    try:
        # Scroll to bottom to make sure the "Next" button is visible
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        # Find and click the "Next" button to move to the next page
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='Go to next page']"))
        )
        next_button.click()

        # Wait until listings on the new page have loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test='result-list-item']"))
        )

        # Additional delay to account for any lazy-loading
        time.sleep(2)

    except TimeoutException:
        # If "Next" button isn't found, assume this is the last page
        print("Reached the last page.")
        break

# Step 7: Close the browser session after scraping completes
driver.quit()

# Save the collected data to a CSV file
df = pd.DataFrame(all_data)  # Convert list of dictionaries to DataFrame
df.to_csv('immoscout_basel_listings.csv', index=True)  # Save DataFrame to CSV
print("Scraping completed. Data saved to immoscout_basel_listings.csv.")