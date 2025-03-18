import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
import os
import random
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    os.environ["DISPLAY"] = ":99"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0")
    driver = webdriver.Firefox(options=options)

    try:
        debug_info = [f"Selenium version: {selenium.__version__}"]
        driver.get(URL)
        time.sleep(random.uniform(3, 6))  # Initial wait

        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                debug_info.append(f"Attempt {attempt + 1}: Waiting for reviews...")
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-hook='review'], .review, .a-section.review"))
                )
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(3, 5))
                debug_info.append("Reviews found after wait.")
                break
            except Exception as e:
                debug_info.append(f"Failed attempt {attempt + 1}: {str(e)}")
                if attempt == max_attempts - 1:
                    debug_info.append("All attempts failed. Capturing page source anyway.")
                time.sleep(5)

        page_source = driver.page_source
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        debug_info.append(f"Page source length: {len(page_source)}")
        debug_info.append(f"Page source snippet: {page_source[:500]}")
        debug_info.append(f"Title: {driver.title}")

        soup = BeautifulSoup(page_source, 'html.parser')
        today = datetime.now()
        five_days_ago = today - timedelta(days=5)

        reviews = (soup.find_all('div', {'data-hook': 'review'}) or 
                   soup.find_all('div', class_='review') or 
                   soup.find_all('div', class_='a-section review'))

        all_reviews_info = []
        low_rated_reviews = []
        raw_html_snippets = []

        if not reviews:
            debug_info.append("No reviews found with any selector.")

        for review in reviews:
            star_element = review.select_one('[data-hook="review-star-rating"], .review-rating, .a-icon-star')
            stars_text = star_element.find('span', {'class': 'a-icon-alt'}).text if star_element else "Unknown stars"
            stars = float(stars_text.split()[0]) if stars_text != "Unknown stars" else -1

            date_element = review.select_one('span[data-hook="review-date"], .review-date')
            date_text = date_element.text.replace("Reviewed in the United States on ", "").strip() if date_element else "Unknown date"

            title_element = review.select_one('[data-hook="review-title"] span, .review-title')
            title = title_element.text.strip() if title_element else "No title"

            all_reviews_info.append({
                'stars': stars,
                'title': title,
                'date': date_text
            })

            if stars <= 3 and stars != -1:
                try:
                    review_date = datetime.strptime(date_text, "%B %d, %Y")
                    if five_days_ago.date() <= review_date.date() <= today.date():
                        low_rated_reviews.append({
                            'stars': stars,
                            'title': title,
                            'date': date_text
                        })
                except ValueError:
                    raw_html_snippets.append(f"Failed parsing date: {date_text} - HTML: {str(review)[:500]}")

            if len(raw_html_snippets) < 3:
                raw_html_snippets.append(str(review)[:500])

        email_body = "All reviews found on the page:\n\n"
        email_body += "\n".join([f"Stars: {r['stars']}, Title: {r['title']}, Date: {r['date']}" for r in all_reviews_info]) or "No reviews parsed."
        email_body += "\n\n"

        if low_rated_reviews:
            email_body += "Low-rated reviews (1, 2, or 3 stars) within the past 5 days:\n\n"
            email_body += "\n".join([f"Stars: {r['stars']}, Title: {r['title']}, Date: {r['date']}" for r in low_rated_reviews])
        else:
            email_body += "No 1, 2, or 3-star reviews found in the past 5 days.\n"

        email_body += f"\n\nDebug info: Today = {today.date()}, Five days ago = {five_days_ago.date()}\n"
        email_body += f"Number of reviews found: {len(reviews)}\n"
        email_body += "\n\n--- Debug Log ---\n" + "\n".join(debug_info)
        email_body += "\n\n--- Raw HTML snippets (first 3 reviews or debug info): ---\n\n"
        email_body += "\n\n".join(raw_html_snippets[:3])

        send_email("Amazon Review Check Results with Debug HTML", email_body)

    except Exception as e:
        send_email("Review Checker Error", f"Error checking reviews: {str(e)}\nPartial page source: {driver.page_source[:500] if 'driver' in locals() else 'N/A'}")

    finally:
        driver.quit()

if __name__ == "__main__":
    check_reviews()
