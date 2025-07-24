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

# Function to fetch articles for a keyword
def get_articles(keyword):
    search = GoogleSearch({
        "q": keyword,
        "api_key": serpapi_api_key,
        "engine": "google",
        "num": 30
    })
    results = search.get_dict()
    return results.get("news_results", [])

# Function to parse date robustly
def parse_article_date(date_string):
    if not date_string:
        return None
    parsed = dateparser.parse(
        date_string,
        settings={
            'TIMEZONE': 'Asia/Tokyo',
            'TO_TIMEZONE': 'Asia/Tokyo',
            'RETURN_AS_TIMEZONE_AWARE': False,
            'RELATIVE_BASE': datetime.now()
        }
    )
    return parsed

# Function to filter recent articles from the past N days
def filter_recent_articles(articles, days=30):
    cutoff = datetime.now() - timedelta(days=days)
    filtered = []
    for article in articles:
        date_str = article.get("date", "")
        parsed_date = parse_article_date(date_str)
        if parsed_date:
            article["parsed_date"] = parsed_date
            if parsed_date >= cutoff:
                filtered.append(article)
    return sorted(filtered, key=lambda x: x["parsed_date"], reverse=True)

# Format email content
def build_email_body(all_articles):
    if not all_articles:
        return "No new articles in the past 30 days."
    
    lines = []
    for art in all_articles:
        title = art.get("title", "No Title")
        link = art.get("link", "")
        date_str = art["parsed_date"].strftime('%Y-%m-%d') if "parsed_date" in art else "Unknown Date"
        lines.append(f"{date_str} - {title}\n{link}\n")
    return "\n".join(lines)

# Collect and aggregate articles
def gather_articles():
    combined = []
    for keyword in keywords:
        print(f"🔍 Searching for: {keyword}")
        articles = get_articles(keyword)
        print(f"  - Retrieved {len(articles)} articles")
        recent = filter_recent_articles(articles)
        print(f"  - {len(recent)} articles are within 30 days")
        combined.extend(recent)
    return sorted(combined, key=lambda x: x["parsed_date"], reverse=True)

# Email sending function
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

# Main routine
if __name__ == "__main__":
    print("📡 Starting article scraping and email routine...")
    articles = gather_articles()
    print(f"📦 Total articles to email: {len(articles)}")
    email_body = build_email_body(articles)
    send_email("🇲🇾 Malaysia Energy News - Daily Digest", email_body)
