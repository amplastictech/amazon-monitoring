import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import time

# Configuration
URL = "https://www.amazon.com/product-reviews/B082QM1ZJN/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1"
EMAIL_SENDER = "your_email@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "your_app_password"   # Replace with your app-specific password
EMAIL_RECEIVER = "receiver_email@example.com"  # Replace with receiver email
SMTP_SERVER = "smtp.gmail.com"  # For Gmail; change if using different provider
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
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

def check_reviews():
    """Check Amazon reviews for low ratings from the past day"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get current date and yesterday's date
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        # Find all review elements
        reviews = soup.find_all('div', {'data-hook': 'review'})
        low_rated_reviews = []

        for review in reviews:
            # Get star rating
            star_element = review.find('i', {'data-hook': 'review-star-rating'})
            if not star_element:
                continue
                
            stars_text = star_element.find('span', {'class': 'a-icon-alt'})
            if not stars_text:
                continue
                
            stars = float(stars_text.text.split()[0])
            
            # Check if rating is 1, 2, or 3 stars
            if stars <= 3:
                # Get review date
                date_element = review.find('span', {'data-hook': 'review-date'})
                if not date_element:
                    continue
                    
                date_text = date_element.text.strip()
                review_date_str = date_text.replace("Reviewed in the United States on ", "")
                review_date = datetime.strptime(review_date_str, "%B %d, %Y")
                
                # Check if review is from yesterday or today
                if review_date.date() >= yesterday.date():
                    title = review.find('a', {'data-hook': 'review-title'})
                    title_text = title.find('span', recursive=False).text if title else "No title"
                    low_rated_reviews.append({
                        'stars': stars,
                        'title': title_text,
                        'date': date_text
                    })

        # Send email if low-rated reviews found
        if low_rated_reviews:
            email_body = "Low-rated reviews found:\n\n"
            for review in low_rated_reviews:
                email_body += f"{review['stars']} stars - {review['title']}\n"
                email_body += f"Date: {review['date']}\n\n"
            send_email("Low Amazon Reviews Detected", email_body)

    except Exception as e:
        error_msg = f"Error checking reviews: {e}"
        send_email("Review Checker Error", error_msg)
        print(error_msg)

if __name__ == "__main__":
    check_reviews()
