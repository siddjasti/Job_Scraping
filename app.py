from flask import Flask, request, render_template
import pandas as pd
from scraper import google_jobs_api, scrape_indeed, scrape_linkedin, scrape_zip_recruiter, USER_AGENT_STRINGS
from playwright.sync_api import sync_playwright
import random

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    df_html = None
    if request.method == 'POST':
        keyword = request.form['keyword']
        location = request.form['location']
        distance = int(request.form['distance'])
        is_remote = 'is_remote' in request.form
        max_posts = 4
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=random.choice(USER_AGENT_STRINGS)
            )
            page.set_default_timeout(5000)
        
            columns = ["job_title", "position_type", "company_name", "location", "pay", "apply_link", "role_desc", "source"]
            df = pd.DataFrame(columns=columns)
            
            #df = google_jobs_api(keyword=keyword, location=location, df=df, max_posts = max_posts)
            #df = scrape_linkedin(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page, max_posts = max_posts)
            df = scrape_indeed(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page, max_posts = max_posts)
            df = scrape_zip_recruiter(keyword = keyword, location = location, distance = distance, is_remote = is_remote, df = df, page = page, max_posts = max_posts)
        
        df['apply_link'] = df['apply_link'].apply(lambda x: f'<a href="{x}" target="_blank" class="apply-link">Apply</a>')
        df['role_desc'] = df['role_desc'].apply(lambda x: f'<button class="description-button" data-desc="{x}">Description</button>')
        df.columns = [col.replace('_', ' ').upper() for col in df.columns]

        df_html = df.to_html(escape=False, index=False)
    
    return render_template('index.html', df_html=df_html)

if __name__ == '__main__':
    app.run(debug=True)
