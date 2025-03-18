import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import time
import os
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Configuration
URL = "https://www.amazon.com/product-reviews/B082QM1ZJN/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1"
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER  # Changed from EMAIL_ADDRESS
    msg['To'] = EMAIL_RECEIVER  # Changed from RECIPIENT
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)  # Changed from EMAIL_ADDRESS
        server.send_message(msg)

def check_reviews():
    send_email("Review Checker Test", f"Script started running at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Set up Selenium
    options = Options()
    options.add_argument("--headless")  # Run without opening a browser window
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)

    try:
        driver.get(URL)
        time.sleep(3)  # Wait for reviews to load (adjust if needed)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        today = datetime.now()
        five_days_ago = today - timedelta(days=5)
        reviews = soup.find_all('li', {'data-hook': 'review'})  # Updated to match your HTML
        
        low_rated_reviews = []
        for review in reviews:
            star_element = review.find('i', {'data-hook': 'review-star-rating'})
            if not star_element:
                continue
            stars_text = star_element.find('span', {'class': 'a-icon-alt'}).text  # "3.0 out of 5 stars"
            stars = float(stars_text.split()[0])

            if stars <= 3:
                date_element = review.find('span', {'data-hook': 'review-date'})
                if not date_element:
                    continue
                date_text = date_element.text.replace("Reviewed in the United States on ", "")
                review_date = datetime.strptime(date_text, "%B %d, %Y")

                if review_date.date() >= five_days_ago.date():
                    title_element = review.find('a', {'data-hook': 'review-title'})
                    title = title_element.find('span', recursive=False).text if title_element else "No title"
                    low_rated_reviews.append({
                        'stars': stars,
                        'title': title,
                        'date': date_text
                    })

        if low_rated_reviews:
            email_body = "Low-rated reviews found:\n\n"
            for review in low_rated_reviews:
                email_body += f"{review['stars']} stars - {review['title']}\n"
                email_body += f"Date: {review['date']}\n\n"
            send_email("Low Amazon Reviews Detected", email_body)
        else:
            send_email("No Low Reviews", "No 1, 2, or 3-star reviews found in the past 5 days.")

    except Exception as e:
        send_email("Review Checker Error", f"Error checking reviews: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_reviews()
