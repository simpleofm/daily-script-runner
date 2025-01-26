from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import time

# Google Sheets setup
SPREADSHEET_ID = "1VCr_Or9m6G76QRtAH8cHOg8OVsd0TT29jKpMPl3IWh8"
SHEET_NAME = "Template"
RANGE = f"{SHEET_NAME}!A2:E"  # Adjust if more columns are involved

# Service account JSON file path
SERVICE_ACCOUNT_FILE = "/Users/noelnaoumi/Desktop/time-tracker-449005-53996a5ed6b3.json"

# Initialize Sheets API
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

# Selenium setup
chrome_driver_path = "/Users/noelnaoumi/Desktop/chromedriver-mac-arm64/chromedriver"
chrome_options = Options()
# chrome_options.add_argument("--start-maximized")  # Fullscreen mode
chrome_options.add_argument("--headless")  # Uncomment for headless mode
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Scraping function
def get_best_time(subreddit):
    base_url = f"https://www.delayforreddit.com/analysis/subreddit/{subreddit}"
    post_at_xpath = '//*[@id="post-at"]'
    
    try:
        driver.get(base_url)

        # Wait until the XPath element is visible, up to 10 seconds
        post_at_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, post_at_xpath))
        )

        # Pause briefly to ensure page has fully loaded
        time.sleep(0.5)

        # Extract the text once the element is visible
        post_at_text = post_at_element.text

        # Format the result
        if "is on" in post_at_text:
            parts = post_at_text.split("is on")
            day_time = parts[1].strip().split(" at ")
            day = day_time[0].strip()
            time_part = day_time[1].strip()
            return f"{day}, {time_part}"

    except TimeoutException:
        return "No data available"
    return "Error"

# Read subreddits from Google Sheets
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
rows = result.get("values", [])

# Process each subreddit and update best time
updates = []
for i, row in enumerate(rows):
    subreddit_url = row[0]
    subreddit_name = subreddit_url.split("/r/")[-1].strip("/")
    best_time = get_best_time(subreddit_name)
    updates.append({"range": f"{SHEET_NAME}!E{i + 2}", "values": [[best_time]]})

    # Wait for 1 second before moving to the next subreddit
    time.sleep(1)

# Batch update the sheet
if updates:
    body = {"valueInputOption": "RAW", "data": updates}
    sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

# Close the browser
driver.quit()
