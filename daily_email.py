import os
import smtplib
import base64
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from serpapi import GoogleSearch
from dotenv import load_dotenv
from dateutil import parser

# Load environment variables
load_dotenv()

# Email credentials
EMAIL_ADDRESS = "ham19902008@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")  # store your app password in .env

# SerpAPI key
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# Keywords to search
KEYWORDS = [
    "renewable energy", "solar", "corporate renewable energy supply scheme",
    "cress", "ppa", "rp4", "review period 4", "energy commission",
    "suruhanjaya tenaga", "electricity", "electricity tariff",
    "energy", "voltage"
]

# Search time filter (30 days)
DAYS_BACK = 30
cutoff_date = datetime.now() - timedelta(days=DAYS_BACK)

# Recipients
RECIPIENTS = [
    "ham19902008@gmail.com",
    "graham.tan@shizenenergy.net"
]

def fetch_articles(keyword):
    params = {
        "q": f"Malaysia {keyword}",
        "engine": "google",
        "tbm": "nws",
        "api_key": SERPAPI_API_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    news_results = results.get("news_results", [])

    articles = []
    for result in news_results:
        try:
            date_str = result.get("date", "")
            published = parser.parse(date_str, fuzzy=True)
            if published < cutoff_date:
                continue
            articles.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "published": published
            })
        except Exception as e:
            continue
    return articles

def compile_email_content(articles):
    # Sort articles by published date (descending)
    articles = sorted(articles, key=lambda x: x["published"], reverse=True)

    html = "<h2>🇲🇾 Malaysia Energy News Summary</h2>"
    html += "<ul>"
    for article in articles:
        html += f"<li><strong>{article['published'].strftime('%Y-%m-%d')}</strong>: <a href='{article['link']}'>{article['title']}</a></li>"
    html += "</ul>"

    return html

def send_email(subject, html_content):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(RECIPIENTS)
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, RECIPIENTS, msg.as_string())
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    print("🔍 Scraping news...")
    all_articles = []
    for kw in KEYWORDS:
        all_articles += fetch_articles(kw)

    if not all_articles:
        print("⚠️ No recent articles found.")
    else:
        html_content = compile_email_content(all_articles)
        send_email("🇲🇾 Daily Malaysia Energy News", html_content)
