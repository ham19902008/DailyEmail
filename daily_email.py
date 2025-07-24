import os
import smtplib
from datetime import datetime, timedelta
from serpapi import GoogleSearch
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dateutil import parser
from dotenv import load_dotenv

load_dotenv()

# Keywords to search
keywords = [
    "Malaysia renewable energy",
    "Malaysia solar",
    "Malaysia corporate renewable energy supply scheme",
    "Malaysia CRESS",
    "Malaysia PPA",
    "Malaysia RP4",
    "Malaysia review period 4",
    "Malaysia energy commission",
    "Malaysia suruhanjaya tenaga",
    "Malaysia electricity",
    "Malaysia electricity tariff",
    "Malaysia energy",
    "Malaysia voltage"
]

# Email credentials and settings
sender_email = "ham19902008@gmail.com"
receiver_emails = ["ham19902008@gmail.com", "graham.tan@shizenenergy.net"]
app_password = os.getenv("EMAIL_PASSWORD")
serpapi_api_key = os.getenv("SERPAPI_API_KEY")

# Function to get results for a keyword
def get_news_results(keyword):
    search = GoogleSearch({
        "q": keyword,
        "engine": "google",
        "api_key": serpapi_api_key,
        "gl": "my",  # Malaysia
        "hl": "en",
        "num": 30,
    })
    results = search.get_dict()
    return results.get("news_results", [])

# Filter results to only include recent ones
def filter_recent_news(news_items, days=30):
    recent_news = []
    now = datetime.now()
    for item in news_items:
        try:
            published = parser.parse(item.get("date") or "")
            if (now - published).days <= days:
                item["parsed_date"] = published
                recent_news.append(item)
        except Exception:
            continue
    # Sort by date descending (latest first)
    recent_news.sort(key=lambda x: x["parsed_date"], reverse=True)
    return recent_news

# Compile email body
def compile_email_body(filtered_articles):
    if not filtered_articles:
        return "No recent energy-related articles found in the past 30 days."

    email_content = "Here are the most recent energy-related news articles (last 30 days):\n\n"
    for article in filtered_articles:
        title = article.get("title", "No Title")
        link = article.get("link", "#")
        date_str = article["parsed_date"].strftime("%Y-%m-%d")
        email_content += f"{title}\nPublished on: {date_str}\n{link}\n\n"
    return email_content

# Main process
def send_news_email():
    all_articles = []
    for keyword in keywords:
        results = get_news_results(keyword)
        filtered = filter_recent_news(results)
        all_articles.extend(filtered)

    # Deduplicate by link
    unique_articles = {item["link"]: item for item in all_articles}.values()
    sorted_articles = sorted(unique_articles, key=lambda x: x["parsed_date"], reverse=True)

    email_body = compile_email_body(sorted_articles)

    # Email setup
    msg = MIMEMultipart()
    msg["Subject"] = "🇲🇾 Malaysia Energy News Summary"
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)
    msg.attach(MIMEText(email_body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_emails, msg.as_string())
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    send_news_email()
