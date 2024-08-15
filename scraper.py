from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError, Page
import random
import time 
import pandas as pd
#from serpapi import GoogleSearch
import requests

USER_AGENT_STRINGS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.3497.92 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
]

def google_jobs_api(keyword: str, location: str, df: pd.DataFrame, max_posts: int):
    keyword = keyword.replace(" ", "+")
    location = location.replace(",", "%2C").replace(" ", "+")
    params = {
        "api_key": "cea5964eec520c394a041039240d86db7c25f2f952f657f3c8e8ac8220791a02"
    }
    
    url = f"https://serpapi.com/search.json?engine=google_jobs&q={keyword}+{location}&hl=en"
    results = requests.get(url, params=params).json()
    added_jobs = []
    jobs_results = results["jobs_results"]
    count = 0
    for job in jobs_results:
        if count == max_posts:
            break
        job_title, company_name, job_location, job_link, job_description  = job["title"], job["company_name"], job["location"], job["related_links"][0]["link"], job["description"]
        
        try:
            position_type = job["detected_extensions"]["schedule_type"]
        except KeyError:
            position_type = "Not Provided"
            
        try:
            job_pay = job["detected_extensions"]["salary"]
        except KeyError:
            job_pay = "Not Provided"
            
        array_item = f"{job_title}{job_location}{company_name}"
        print(f"Title: {job_title}\nCompany: {company_name}\nLocation: {job_location}\n")
        count += 1
        if array_item not in added_jobs:
            added_jobs.append(array_item)
            new_row = pd.DataFrame([{"job_title": job_title, "position_type": position_type, "company_name": company_name, "location": job_location, "pay": job_pay, "apply_link": job_link, "role_desc": job_description, "source": "Indeed"}])
            df = pd.concat([df, new_row], ignore_index=True)
            
    
        
    

def scrape_indeed(keyword: str, location: str, distance: int, is_remote: bool, df: pd.DataFrame, page: Page, max_posts: int):
    keyword = keyword.replace(" ", "+")
    location = location.replace(",", "%2C").replace(" ", "+")
    added_jobs = []
    count = 1

    if is_remote:
        work_type = r"sc=0kf%3Aattr%28DSQF7%29%3B"
    else:
        work_type = ""
    
    indeed_url = f"https://www.indeed.com/jobs?q={keyword}&l={location}&radius={distance}&sc={work_type}"
    print(indeed_url)
    page.goto(indeed_url)
    page.wait_for_selector("#jobsearch-Main")
    
    while count < max_posts + 1:
        num_jobs = page.query_selector_all(f"#mosaic-provider-jobcards > ul > li.css-5lfssm.eu4oa1w0")
        for current_job in num_jobs:
            if count >= max_posts + 1:
                break
            try:
                current_job.click(timeout=1500)
                time.sleep(0.5)
            except Exception:
                continue
            try:
                page.wait_for_selector("div.jobsearch-JobInfoHeader-title-container.css-bbq8li.eu4oa1w0", timeout=2000)
                job_title = page.query_selector("div.jobsearch-JobInfoHeader-title-container.css-bbq8li.eu4oa1w0").inner_text().strip().replace("\n- job post", "")
                job_location = page.query_selector('[data-testid="inlineHeader-companyLocation"]').inner_text().strip()
                company_name = page.query_selector('[data-testid="inlineHeader-companyName"]').inner_text().strip() 
                
                try:
                    job_link = page.query_selector("#applyButtonLinkContainer > div > div > button").get_attribute("href")
                except AttributeError:
                    job_link = page.query_selector('[data-testid="inlineHeader-companyName"]').get_attribute("href")
                
                job_description = page.query_selector('div#jobDescriptionText').inner_text().strip()
                
                try:
                    job_pay = page.query_selector('div#salaryInfoAndJobType span.css-19j1a75.eu4oa1w0').inner_text().strip()
                except AttributeError:
                    job_pay = "None specified"
                    
                try:
                    position_type = page.query_selector('span.css-k5flys.eu4oa1w0').inner_text().strip()[2:]
                except AttributeError:
                    position_type = "None specified"
                         
                print(f"Title: {job_title}\nCompany: {company_name}\nLocation: {job_location}\nCount: {count}\n") #\nPay: {job_pay}\nLink: {job_link}\nDescription: {job_description}")
                count += 1
            except (IndexError, TimeoutError) as e:
                print("Not able to get element")
                continue
                
            array_item = f"{job_title}{job_location}{company_name}"
            if array_item not in added_jobs:
                added_jobs.append(array_item)
                new_row = pd.DataFrame([{"job_title": job_title, "position_type": position_type, "company_name": company_name, "location": job_location, "pay": job_pay, "apply_link": job_link, "role_desc": job_description, "source": "Indeed"}])
                df = pd.concat([df, new_row], ignore_index=True)
            
        try:
            page.wait_for_selector('#jobsearch-JapanPage > div > div.css-hyhnne.e37uo190 > div > div.css-pprl14.eu4oa1w0 > nav > ul > li > a', timeout=2000)
            next_btn = page.query_selector_all('[data-testid="pagination-page-next"]')[0]
            next_btn.click()
            page.wait_for_selector('#jobsearch-JapanPage > div > div.css-hyhnne.e37uo190 > div > div.css-pprl14.eu4oa1w0 > nav > ul > li > a', timeout=2000)
        except TimeoutError:
            print("Could not find next button")
            break
    
    return df

def scrape_linkedin(keyword: str, location: str, distance: int, is_remote: bool, df: pd.DataFrame, page: Page, max_posts: int):
    keyword = keyword.replace(" ", "%2B")
    location = location.replace(",", "%2C").replace(" ", "%2B")
    added_jobs = []
    
    if is_remote:
        work_type = "2"
    else:
        work_type = None
        
    if work_type:
        linkedin_url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}&distance={distance}&f_TPR={work_type}"
    else:
        linkedin_url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}&distance={distance}&position=1&pageNum=0"

    page.goto(linkedin_url)
    print(linkedin_url)
    #page.wait_for_selector("div.results-context-header")
    
    num_jobs = page.query_selector_all("ul.jobs-search__results-list li")
    count = 0
    for current_job in num_jobs:
        if count == max_posts:
            break
        try:
            current_job.click(timeout=1500)
            time.sleep(0.25)
        except Exception:
            print("Couldnt click on the job")
            continue
        try:
            
            page.wait_for_selector("body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > section > div > div.top-card-layout__entity-info-container.flex.flex-wrap.papabear\\:flex-nowrap > div > a > h2", timeout=1000)
            job_title = page.query_selector("body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > section > div > div.top-card-layout__entity-info-container.flex.flex-wrap.papabear\\:flex-nowrap > div > a > h2").inner_text().strip()
            job_location = page.query_selector('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > section > div > div.top-card-layout__entity-info-container.flex.flex-wrap.papabear\\:flex-nowrap > div > h4 > div:nth-child(1) > span.topcard__flavor.topcard__flavor--bullet').inner_text().strip()
            company_name = page.query_selector('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > section > div > div.top-card-layout__entity-info-container.flex.flex-wrap.papabear\\:flex-nowrap > div > h4 > div:nth-child(1) > span:nth-child(1) > a').inner_text().strip() 
                
            try:
                job_link = page.query_selector('[data-tracking-control-name="public_jobs_apply-link-onsite"]').inner_html()[5:-4]
            except AttributeError:
                job_link = page.query_selector('[data-tracking-control-name="public_jobs_apply-link-offsite_sign-up-modal"]').inner_html()[5:-4]
            
            show_more_btn = page.query_selector("body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > div > section.core-section-container.my-3.description > div > div > section > button.show-more-less-html__button.show-more-less-button.show-more-less-html__button--more.ml-0\\.5")
            show_more_btn.click()
            job_description = page.query_selector('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > div > section.core-section-container.my-3.description > div > div > section > div').inner_text().strip()
            
            try:
                job_pay = page.query_selector('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > div > section.core-section-container.my-3.compensation.compensation--above-description.compensation--jserp > div > div > div').inner_text().strip()
            except AttributeError:
                job_pay = "None specified"
                
            try:
                position_type = page.query_selector('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > div > section.core-section-container.my-3.description > div > ul > li:nth-child(2) > span').inner_text().strip()
            except AttributeError:
                position_type = "None specified"
                        
            count += 1
            print(f"Title: {job_title}\nCompany: {company_name}\nLocation: {job_location}\nCount: {count}\n") #\nPay: {job_pay}\nLink: {job_link}\nDescription: {job_description}")
        except (AttributeError, TimeoutError) as e:
            print(e)
            continue
            
        array_item = f"{job_title}{job_location}{company_name}"
        if array_item not in added_jobs:
            added_jobs.append(array_item)
            new_row = pd.DataFrame([{"job_title": job_title, "position_type": position_type, "company_name": company_name, "location": job_location, "pay": job_pay, "apply_link": job_link, "role_desc": job_description, "source": "Indeed"}])
            df = pd.concat([df, new_row], ignore_index=True)

    return df

def scrape_zip_recruiter(keyword: str, location: str, distance: int, is_remote: bool, df: pd.DataFrame, page: Page, max_posts: int):
    keyword = keyword.replace(" ", "+")
    location = location.replace(",", "%2C").replace(" ", "+")
    added_jobs = []
    total_scraped = 0
    
    zip_recruiter_link = f"https://www.ziprecruiter.com/jobs-search?search={keyword}&location={location}"
    print(zip_recruiter_link)
    page.goto(zip_recruiter_link)
    page.wait_for_selector("#react-job-results-root > div > div.relative.flex.w-full.flex-col.h-full")
    page.mouse.click(x = 0, y = 10)
    time.sleep(0.3)
    
    while total_scraped <= max_posts:
        num_jobs = page.query_selector_all("div.job_result_wrapper")
        count = 0
        for current_job in num_jobs:
            if total_scraped >= max_posts:
                break
            job_card = current_job.query_selector("h2.font-bold.text-black.text-header-sm")
            count += 1

            try:
                job_card.click(timeout=1500)
                time.sleep(0.5)
            except Exception:
                print("error")
                continue
            try:
                job_title = page.query_selector("h1.font-bold.text-black.text-header-lg.md\\:text-header-lg-tablet").inner_text().strip()
                job_location = page.query_selector('div.mb-24 p').inner_text().strip().split("•")[0]
                company_name = page.query_selector('div.flex.flex-col div.mb-12 a').inner_text().strip() 
                job_description = page.query_selector('div.relative.flex.flex-col.gap-24').inner_text().strip()
            
                try:
                    job_link = page.query_selector("div.mb-12 a").get_attribute("href")
                except (AttributeError, TimeoutError):
                    job_link = None
                
                container = page.query_selector('div.flex.flex-col div.flex.flex-col.gap-4')
                if container:
                    p_elements = container.query_selector_all('p.text-black.normal-case.text-body-md')

                    job_pay = "none specified"
                    position_type = "Unknown"

                    if len(p_elements) == 1:
                        position_type = p_elements[0].inner_text()
                    elif len(p_elements) == 2:
                        job_pay = p_elements[0].inner_text()
                        position_type = p_elements[1].inner_text()

                         
                print(f"Title: {job_title}\nCompany: {company_name}\nLocation: {job_location}\nCount: {count}\n") #\nPay: {job_pay}\nLink: {job_link}\nDescription: {job_description}")
                total_scraped += 1
            except (AttributeError, TimeoutError) as e:
                print("error")
                continue
                
            array_item = f"{job_title}{job_location}{company_name}"
            if array_item not in added_jobs:
                added_jobs.append(array_item)
                new_row = pd.DataFrame([{"job_title": job_title, "position_type": position_type, "company_name": company_name, "location": job_location, "pay": job_pay, "apply_link": job_link, "role_desc": job_description, "source": "Zip Recruiter"}])
                df = pd.concat([df, new_row], ignore_index=True)
            
        try:
            page.wait_for_selector('[title="Next Page"]', timeout=2000)
            next_btn = page.query_selector('[title="Next Page"]')
            next_btn.click()
            page.wait_for_selector('[data-testid="right-pane"]', timeout=2000)
        except TimeoutError:
            print("Could not find next button")
            break
    
    return df

    
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=50)
        page = browser.new_page(
            user_agent=random.choice(USER_AGENT_STRINGS)
        )
        try: 
            page.set_default_timeout(5000)
        except Exception:
            page.set_default_timeout(5000)
    
        columns = ["job_title", "position_type", "company_name", "location", "pay", "apply_link", "role_desc", "source"]
        df = pd.DataFrame(columns=columns)
        keyword = "Software Engineering"
        location = "Austin, TX"
        distance = 10 #0, 5, 10, 25, 50
        is_remote = False
        max_posts = 60
        
        #df = google_jobs_api(keyword = keyword, location = location, df = df)
        #df = scrape_linkedin(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page, max_posts = max_posts)
        #df = scrape_indeed(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page, max_posts = max_posts)
        #df = scrape_zip_recruiter(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page, max_posts = max_posts)
        df.to_csv('output.csv', index=True)
        
    #browser.close()
    

if __name__ == "__main__":
    main()