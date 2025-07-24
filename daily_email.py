import os
import smtplib
from email.mime.text import MIMEText
from serpapi import GoogleSearch
from datetime import datetime, timedelta
import dateparser

# Keywords to track
keywords = ["Malaysia energy", "renewables Malaysia", "solar Malaysia", "Tenaga Nasional Berhad"]

# Load API key and email credentials
serpapi_api_key = os.environ["SERPAPI_API_KEY"]
email_address = "ham19902008@gmail.com"
email_password = os.environ["EMAIL_APP_PASSWORD"]
recipients = ["ham19902008@gmail.com", "graham.tan@shizenenergy.net"]

# Function to fetch articles
def get_articles(keyword):
    search = GoogleSearch({
        "q": keyword,
        "api_key": serpapi_api_key,
        "engine": "google",
        "num": 30
    })
    results = search.get_dict()
    return results.get("news_results", [])

# Filter articles by last 30 days
def filter_recent_articles(articles, days=30):
    cutoff = datetime.now() - timedelta(days=days)
    filtered = []
    for article in articles:
        parsed_date = dateparser.parse(article.get("date", ""), settings={'TIMEZONE': 'Asia/Tokyo'})
        if parsed_date and parsed_date > cutoff:
            article["parsed_date"] = parsed_date
            filtered.append(article)
    return sorted(filtered, key=lambda x: x["parsed_date"], reverse=True)

# Format email content
def build_email_body(all_articles):
    lines = []
    for art in all_articles:
        date_str = art['parsed_date'].strftime('%Y-%m-%d') if 'parsed_date' in art else 'Unknown Date'
        lines.append(f"{date_str} - {art['title']}\n{art['link']}\n")
    return "\n".join(lines) or "No new articles in the past 30 days."

# Fetch and combine all articles
def gather_articles():
    combined = []
    for kw in keywords:
        articles = get_articles(kw)
        recent = filter_recent_articles(articles)
        combined.extend(recent)
    return sorted(combined, key=lambda x: x["parsed_date"], reverse=True)

# Send email
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = ", ".join(recipients)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_address, email_password)
            server.sendmail(email_address, recipients, msg.as_string())
            print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# Main flow
if __name__ == "__main__":
    print("📡 Starting article collection...")
    articles = gather_articles()
    print(f"📰 Found {len(articles)} articles from the past 30 days.")
    body = build_email_body(articles)
    send_email("🇲🇾 Malaysia Energy News - Daily Digest", body)
