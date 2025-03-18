import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

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
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

def check_reviews():
    send_email("Review Checker Test", f"Script started running at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Set up Selenium with Firefox
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0")
    driver = webdriver.Firefox(options=options)

    try:
        driver.get(URL)
        time.sleep(3)  # Wait for reviews to load
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        today = datetime.now()
        five_days_ago = today - timedelta(days=5)
        reviews = soup.find_all('li', {'data-hook': 'review'})
        
        all_reviews = []
        low_rated_reviews = []
        
        # Collect all reviews
        for review in reviews:
            star_element = review.find('i', {'data-hook': 'review-star-rating'})
            stars_text = star_element.find('span', {'class': 'a-icon-alt'}).text if star_element else "Unknown stars"
            stars = float(stars_text.split()[0]) if stars_text != "Unknown stars" else -1

            date_element = review.find('span', {'data-hook': 'review-date'})
            date_text = date_element.text.replace("Reviewed in the United States on ", "") if date_element else "Unknown date"
            review_date = datetime.strptime(date_text, "%B %d, %Y") if date_text != "Unknown date" else None

            title_element = review.find('a', {'data-hook': 'review-title'})
            title = title_element.find('span', recursive=False).text if title_element else "No title"

            # Add to all reviews list
            all_reviews.append({
                'stars': stars,
                'title': title,
                'date': date_text
            })

            # Check for low-rated reviews within 5 days
            if stars <= 3 and stars != -1 and review_date and review_date.date() >= five_days_ago.date():
                low_rated_reviews.append({
                    'stars': stars,
                    'title': title,
                    'date': date_text
                })

        # Prepare email body with all reviews
        email_body = "All reviews found on the page:\n\n"
        for review in all_reviews:
            email_body += f"{review['stars']} stars - {review['title']}\n"
            email_body += f"Date: {review['date']}\n\n"

        # Add low-rated reviews (if any)
        if low_rated_reviews:
            email_body += "Low-rated reviews (1, 2, or 3 stars) within the past 5 days:\n\n"
            for review in low_rated_reviews:
                email_body += f"{review['stars']} stars - {review['title']}\n"
                email_body += f"Date: {review['date']}\n\n"
        else:
            email_body += "No 1, 2, or 3-star reviews found in the past 5 days.\n"

        email_body += f"Debug info: Today = {today.date()}, Five days ago = {five_days_ago.date()}"

        send_email("Amazon Review Check Results", email_body)

    except Exception as e:
        send_email("Review Checker Error", f"Error checking reviews: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_reviews()
