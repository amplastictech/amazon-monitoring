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
    from email.mime.text import MIMEText
    import smtplib

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

def check_reviews():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0")
    driver = webdriver.Firefox(options=options)

    try:
        driver.get(URL)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        today = datetime.now()
        five_days_ago = today - timedelta(days=5)

        reviews = soup.find_all('div', {'data-hook': 'review'})

        all_reviews_info = []
        low_rated_reviews = []

        # Debug raw HTML snippets for the first few reviews
        raw_html_snippets = []

        for review in reviews:
            # Raw HTML snippet for debugging
            raw_html_snippets.append(str(review)[:1000])  # limit snippet length

            star_element = review.select_one('[data-hook="review-star-rating"] span')
            stars_text = star_element.text.strip() if star_element else "Unknown"
            stars = float(stars_text.split()[0]) if stars_text != "Unknown stars" else -1

            date_element = review.select_one('span[data-hook="review-date"]')
            date_text = date_element.text.replace("Reviewed in the United States on ", "").strip() if date_element else "Unknown date"
            review_date = datetime.strptime(date_text, "%B %d, %Y") if date_element else None

            title_element = review.select_one('a[data-hook="review-title"] span')
            title = title_element.text.strip() if (title_element := review.select_one('a[data-hook="review-title"] span')) else "No title"

            all_reviews_info.append(f"{stars} stars - {title} (Date: {date_text})")

            if stars <= 3 and stars != -1 and review_date := datetime.strptime(date_text, "%B %d, %Y"):
                if five_days_ago.date() <= review_date.date() <= today.date():
                    low_rated_reviews.append(f"{stars} stars - {title} (Date: {date_text})")

            # Capture only first 3 raw snippets
            if len(raw_html_snippets) < 3:
                raw_html_snippets.append(str(review))

        email_body = "All reviews found on the page:\n\n"
        email_body += "\n".join(all_reviews_info)
        email_body += "\n\n"

        if low_rated_reviews:
            email_body += "Low-rated reviews (1, 2, or 3 stars) within the past 5 days:\n\n"
            email_body += "\n".join(low_rated_reviews)
        else:
            email_body += "No 1, 2, or 3-star reviews found in the past 5 days.\n"

        email_body += f"\n\nDebug info: Today = {datetime.now().date()}, Five days ago = {(datetime.now() - timedelta(days=5)).date()}\n"
        email_body += "\n\n--- Raw HTML snippets (first 3 reviews): ---\n\n"
        email_body += "\n\n".join(raw_html_snippets)

        send_email("Amazon Review Check Results with Debug HTML", email_body)

    except Exception as e:
        send_email("Review Checker Error", f"Error checking reviews: {str(e)}")

    finally:
        driver.quit()

if __name__ == "__main__":
    check_reviews()
