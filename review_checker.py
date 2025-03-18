import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import time
import os

# Configuration
URL = "https://www.amazon.com/product-reviews/B082QM1ZJN/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1"
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email(subject, body):
    """Send email notification"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully: " + subject)
    except Exception as e:
        print(f"Error sending email: {e}")
        raise  # Raise the exception to ensure it’s visible in logs

def check_reviews():
    """Check Amazon reviews for low ratings from the past 5 days"""
    # Send a test email to confirm email functionality
    send_email("Review Checker Test", "Script started running at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        today = datetime.now()
        five_days_ago = today - timedelta(days=5)
        
        reviews = soup.find_all('div', {'data-hook': 'review'})
        low_rated_reviews = []

        for review in reviews:
            star_element = review.find('i', {'data-hook': 'review-star-rating'})
            if not star_element:
                continue
                
            stars_text = star_element.find('span', {'class': 'a-icon-alt'})
            if not stars_text:
                continue
                
            stars = float(stars_text.text.split()[0])
            
            if stars <= 3:
                date_element = review.find('span', {'data-hook': 'review-date'})
                if not date_element:
                    continue
                    
                date_text = date_element.text.strip()
                review_date_str = date_text.replace("Reviewed in the United States on ", "")
                review_date = datetime.strptime(review_date_str, "%B %d, %Y")
                
                if review_date.date() >= five_days_ago.date():
                    title = review.find('a', {'data-hook': 'review-title'})
                    title_text = title.find('span', recursive=False).text if title else "No title"
                    low_rated_reviews.append({
                        'stars': stars,
                        'title': title_text,
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
        error_msg = f"Error checking reviews: {e}"
        send_email("Review Checker Error", error_msg)
        print(error_msg)

if __name__ == "__main__":
    check_reviews()
