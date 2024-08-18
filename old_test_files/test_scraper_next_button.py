from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError, Page
import random
import time 
import pandas as pd
import requests

USER_AGENT_STRINGS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.3497.92 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
]    

def scrape_indeed(keyword: str, location: str, distance: int, is_remote: bool, df: pd.DataFrame, page: Page):
    keyword = keyword.replace(" ", "+")
    location = location.replace(",", "%2C").replace(" ", "+")
    added_jobs = []
    
    if is_remote:
        work_type = r"sc=0kf%3Aattr%28DSQF7%29%3B"
    else:
        work_type = ""
    
    indeed_url = f"https://www.indeed.com/jobs?q={keyword}&l={location}&radius={distance}&sc={work_type}"
    page.goto(indeed_url)
    page.wait_for_selector("#jobsearch-Main")
    
    while True:
        num_jobs = page.query_selector_all(f"#mosaic-provider-jobcards > ul > li.css-5lfssm.eu4oa1w0")
        count = 0
        for current_job in num_jobs:
            count += 1
            try:
                current_job.click(timeout=1500)
            except Exception:
                continue
            try:
                page.wait_for_selector("div.jobsearch-JobInfoHeader-title-container.css-bbq8li.eu4oa1w0", timeout=2000)
                job_title = page.query_selector_all("div.jobsearch-JobInfoHeader-title-container.css-bbq8li.eu4oa1w0")[0].inner_text().strip().replace("\n- job post", "")
                job_location = page.query_selector_all('[data-testid="inlineHeader-companyLocation"]')[0].inner_text().strip()
                company_name = page.query_selector_all('[data-testid="inlineHeader-companyName"]')[0].inner_text().strip() 
                job_link = page.query_selector_all("#applyButtonLinkContainer > div > div > button")[0].get_attribute("href")
                job_description = page.query_selector_all('div#jobDescriptionText')[0].inner_text().strip()
                
                try:
                    job_pay = page.query_selector_all('div#salaryInfoAndJobType span.css-19j1a75.eu4oa1w0')[0].inner_text().strip()
                except IndexError:
                    job_pay = "None specified"
                    
                try:
                    position_type = page.query_selector_all('span.css-k5flys.eu4oa1w0')[0].inner_text().strip()
                except IndexError:
                    position_type = "None specified"
                         
                print(f"Title: {job_title}\nCompany: {company_name}\nLocation: {job_location}\nCount: {count}\n") #\nPay: {job_pay}\nLink: {job_link}\nDescription: {job_description}")
            except (IndexError, TimeoutError) as e:
                continue
                #print("Not able to get element")
                
            #("\n\n")
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

def scrape_linkedin(keyword: str, location: str, distance: int, is_remote: bool, df: pd.DataFrame, page: Page):
    keyword = keyword.replace(" ", "%2B")
    location = location.replace(",", "%2C").replace(" ", "%2B")
    added_jobs = []
    
    if is_remote:
        work_type = "2"
    else:
        work_type = ""
        
    linkedin_url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}&distance={distance}&f_TPR={work_type}"
    page.goto(linkedin_url)
    #page.wait_for_selector("div.results-context-header")
    
    num_jobs = page.query_selector_all("ul.jobs-search__results-list li")
    count = 0
    for current_job in num_jobs:
        count += 1
        try:
            current_job.click(timeout=1500)
            time.sleep(1.0)
        except Exception:
            print("Couldnt click on the job")
            continue
        try:
            
            page.wait_for_selector("body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > section > div > div.top-card-layout__entity-info-container.flex.flex-wrap.papabear\\:flex-nowrap > div > a > h2", timeout=2500)
            job_title = page.query_selector_all("body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > section > div > div.top-card-layout__entity-info-container.flex.flex-wrap.papabear\\:flex-nowrap > div > a > h2")[0].inner_text().strip()
            job_location = page.query_selector_all('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > section > div > div.top-card-layout__entity-info-container.flex.flex-wrap.papabear\\:flex-nowrap > div > h4 > div:nth-child(1) > span.topcard__flavor.topcard__flavor--bullet')[0].inner_text().strip()
            company_name = page.query_selector_all('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > section > div > div.top-card-layout__entity-info-container.flex.flex-wrap.papabear\\:flex-nowrap > div > h4 > div:nth-child(1) > span:nth-child(1) > a')[0].inner_text().strip() 
            job_link = page.query_selector_all("#applyUrl")[0].inner_html()[5:-4]
            
            show_more_btn = page.query_selector("body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > div > section.core-section-container.my-3.description > div > div > section > button.show-more-less-html__button.show-more-less-button.show-more-less-html__button--more.ml-0\\.5")
            show_more_btn.click()
            job_description = page.query_selector_all('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > div > section.core-section-container.my-3.description > div > div > section > div')[0].inner_text().strip()
            
            try:
                job_pay = page.query_selector_all('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > div > section.core-section-container.my-3.compensation.compensation--above-description.compensation--jserp > div > div > div')[0].inner_text().strip()
            except IndexError:
                job_pay = "None specified"
                
            try:
                position_type = page.query_selector_all('body > div.base-serp-page > div > section > div.details-pane__content.details-pane__content--show > div > section.core-section-container.my-3.description > div > ul > li:nth-child(2) > span')[0].inner_text().strip()
            except IndexError:
                position_type = "None specified"
                        
            print(f"Title: {job_title}\nCompany: {company_name}\nLocation: {job_location}\nCount: {count}\n") #\nPay: {job_pay}\nLink: {job_link}\nDescription: {job_description}")
        except (IndexError, TimeoutError) as e:
            print(e)
            continue
            
        array_item = f"{job_title}{job_location}{company_name}"
        if array_item not in added_jobs:
            added_jobs.append(array_item)
            new_row = pd.DataFrame([{"job_title": job_title, "position_type": position_type, "company_name": company_name, "location": job_location, "pay": job_pay, "apply_link": job_link, "role_desc": job_description, "source": "Indeed"}])
            df = pd.concat([df, new_row], ignore_index=True)

    return df

def google_jobs_api(keyword: str, location: str, df: pd.DataFrame):
    keyword = keyword.replace(" ", "+")
    location = location.replace(",", "%2C").replace(" ", "+")
    params = {
        "api_key": "cea5964eec520c394a041039240d86db7c25f2f952f657f3c8e8ac8220791a02"
    }
    
    url = f"https://serpapi.com/search.json?engine=google_jobs&q={keyword}+{location}&hl=en"
    results = requests.get(url, params=params).json()
    added_jobs = []
    jobs_results = results["jobs_results"]
    for job in jobs_results:
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
        if array_item not in added_jobs:
            added_jobs.append(array_item)
            new_row = pd.DataFrame([{"job_title": job_title, "position_type": position_type, "company_name": company_name, "location": job_location, "pay": job_pay, "apply_link": job_link, "role_desc": job_description, "source": "Indeed"}])
            df = pd.concat([df, new_row], ignore_index=True)
            
def scrape_zip_recruiter(keyword: str, location: str, distance: int, is_remote: bool, df: pd.DataFrame, page: Page):
    keyword = keyword.replace(" ", "+")
    location = location.replace(",", "%2C").replace(" ", "+")
    added_jobs = []
    
    if is_remote:
        work_type = r"sc=0kf%3Aattr%28DSQF7%29%3B"
    else:
        work_type = ""
    
    zip_recruiter_link = f"https://www.ziprecruiter.com/jobs-search?search={keyword}&location={location}"
    page.goto(zip_recruiter_link)
    #time.sleep(3)
    page.wait_for_selector("#react-job-results-root > div > div.relative.flex.w-full.flex-col.h-full")
    
    while True:
        num_jobs = page.query_selector_all(f"div.job_result_wrapper.job_result_selected")
        num_jobs.extend(page.query_selector_all(f"div.job_result_wrapper"))
        count = 0
        for current_job in num_jobs:
            current_job = page.query_selector("div.group.flex w-full.flex-col.text-black")
            count += 1
            try:
                current_job.click(timeout=1500)
            except Exception:
                continue
            try:
                page.wait_for_selector("h1.font-bold.text-black.text-header-lg.md:text-header-lg-tablet", timeout=2000)
                job_title = page.query_selector_all("h1.font-bold.text-black.text-header-lg.md:text-header-lg-tablet")[0].inner_text().strip().replace("\n- job post", "")
                job_location = page.query_selector_all('p.text-black normal-case.text-body-md')[0].inner_text().strip()
                company_name = page.query_selector_all('div.flex.flex-col > div.mb-24')[0].inner_text().strip() 
                
                show_more_btn = page.query_selector("mt-[-48px].w-fit.min-w-[252px]")
                show_more_btn.click()
                job_description = page.query_selector_all('div.relative.flex.flex-col.gap-24')[0].inner_text().strip()
            
                try:
                    job_link = page.query_selector_all("div.flex.flex-col a")[0].get_attribute("href")
                except (IndexError, TimeoutError):
                    job_link = page.query_selector_all('div#jobDescriptionText')[0].inner_text().strip()
                
                try:
                    job_pay = page.query_selector_all('div#salaryInfoAndJobType span.css-19j1a75.eu4oa1w0')[0].inner_text().strip()
                except IndexError:
                    job_pay = "None specified"
                    
                try:
                    position_type = page.query_selector_all('div.flex.flex-col.gap-4')[0].inner_text().strip()
                except IndexError:
                    position_type = "None specified"
                         
                print(f"Title: {job_title}\nCompany: {company_name}\nLocation: {job_location}\nCount: {count}\n") #\nPay: {job_pay}\nLink: {job_link}\nDescription: {job_description}")
            except (IndexError, TimeoutError) as e:
                continue
                #print("Not able to get element")
                
            #("\n\n")
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

def scrape_monster(keyword: str, location: str, distance: int, is_remote: bool, df: pd.DataFrame, page: Page):
    keyword = keyword.replace(" ", "+")
    location = location.replace(",", "%2C").replace(" ", "+")
    added_jobs = []
    
    monster_link = f"https://www.monster.com/jobs/search?q={keyword}&where={location}&page=1"
    page.goto(monster_link)
    #time.sleep(3)
    page.wait_for_selector('[data-testid="pagination-page-next"]')
    
    while True:
        num_jobs = page.query_selector_all(f"div.job-search-results-style__JobCardWrap-sc-a3bbdc54-4.MsARP")
        count = 0
        for current_job in num_jobs:
            count += 1
            try:
                current_job.click(timeout=1500)
            except Exception:
                continue
            try:
                page.wait_for_selector('[data-testid="pagination-page-next"]', timeout=2000)
                job_title = page.query_selector_all('[data-testid="pagination-page-next"]')[0].inner_text().strip().replace("\n- job post", "")
                job_location = page.query_selector_all('[data-testid="jobDetailLocation"]')[0].inner_text().strip()
                company_name = page.query_selector_all('[data-testid="company"]')[0].inner_text().strip() 
                
                job_description = page.query_selector_all('div.description-styles__DescriptionContainerOuter-sc-78eb761c-0.bA-dNHP')[0].inner_text().strip()
            
                job_link = ""#page.query_selector_all("div.flex.flex-col a")[0].get_attribute("href")
                
                try:
                    job_pay = page.query_selector_all('[data-testid="payTag"]')[0].inner_text().strip()
                except IndexError:
                    job_pay = "None specified"
                    
                try:
                    position_type = page.query_selector_all('[data-testid="tag"]')[0].inner_text().strip()
                except IndexError:
                    position_type = "None specified"
                         
                print(f"Title: {job_title}\nCompany: {company_name}\nLocation: {job_location}\nCount: {count}\n") #\nPay: {job_pay}\nLink: {job_link}\nDescription: {job_description}")
            except (IndexError, TimeoutError) as e:
                continue
                #print("Not able to get element")
                
            #("\n\n")
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
    
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
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
        location = "Dallas, TX"
        distance = 0 #0, 5, 10, 25, 50
        is_remote = False
        
        #df = google_jobs_api(keyword = keyword, location = location, df = df)
        #df = scrape_linkedin(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page)
        #df = scrape_indeed(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page)
        #df = scrape_zip_recruiter(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page)
        df = scrape_zip_recruiter(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page)
        df.to_csv('output.csv', index=True)
        
    #browser.close()
    

if __name__ == "__main__":
    main()