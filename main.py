import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Environment variables
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "1VCr_Or9m6G76QRtAH8cHOg8OVsd0TT29jKpMPl3IWh8")
SHEET_NAME = os.environ.get("SHEET_NAME", "Template")
SERVICE_ACCOUNT_INFO = json.loads(os.environ.get("SERVICE_ACCOUNT_INFO"))

# Google Sheets setup
creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO, scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

# Selenium setup
chrome_options = Options()
chrome_options.add_argument("--headless")  # Headless mode for cloud execution
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
service = Service("/usr/bin/chromedriver")  # Default path in Cloud Functions
driver = webdriver.Chrome(service=service, options=chrome_options)

def get_best_time(subreddit):
    base_url = f"https://www.delayforreddit.com/analysis/subreddit/{subreddit}"
    post_at_xpath = '//*[@id="post-at"]'
    try:
        driver.get(base_url)
        post_at_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, post_at_xpath))
        )
        time.sleep(0.5)
        post_at_text = post_at_element.text
        if "is on" in post_at_text:
            parts = post_at_text.split("is on")
            day_time = parts[1].strip().split(" at ")
            return f"{day_time[0].strip()}, {day_time[1].strip()}"
    except TimeoutException:
        return "No data available"
    return "Error"

def update_sheet(request):
    RANGE = f"{SHEET_NAME}!A2:E"
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
    rows = result.get("values", [])
    updates = []
    for i, row in enumerate(rows):
        subreddit_url = row[0]
        subreddit_name = subreddit_url.split("/r/")[-1].strip("/")
        best_time = get_best_time(subreddit_name)
        updates.append({"range": f"{SHEET_NAME}!E{i + 2}", "values": [[best_time]]})
        time.sleep(1)
    if updates:
        body = {"valueInputOption": "RAW", "data": updates}
        sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    driver.quit()
    return "Update completed."
