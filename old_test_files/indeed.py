from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

chrome_options = Options()
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

webdriver_service = Service('https://storage.googleapis.com/chrome-for-testing-public/126.0.6478.126/mac-x64/chrome-mac-x64.zip')  # e.g., '/usr/local/bin/chromedriver'

driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

city, stateAbrev = "Kansas City", "MO"
city = city.replace(" ", "+")

url = f'https://www.indeed.com/jobs?q={city}%2C+{stateAbrev}'

driver.get(url)

wait = WebDriverWait(driver, 10)
job_cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.css-5lfssm.eu4oa1w0')))

jobs = []

for job_card in job_cards:
    try:
        title = job_card.find_element(By.CSS_SELECTOR, 'h2.jobTitle').text
        company = job_card.find_element(By.CSS_SELECTOR, 'span.companyName').text
        location = job_card.find_element(By.CSS_SELECTOR, 'div.companyLocation').text
        summary = job_card.find_element(By.CSS_SELECTOR, 'div.job-snippet').text
        jobs.append({
            'title': title,
            'company': company,
            'location': location,
            'summary': summary
        })
    except Exception as e:
        print(f"Error parsing job card: {e}")

driver.quit()

jobs_df = pd.DataFrame(jobs)

print(jobs_df)
