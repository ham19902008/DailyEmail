import os
import datetime
import smtplib
from email.mime.text import MIMEText
from serpapi import GoogleSearch
from dotenv import load_dotenv
from main import KEYWORDS  # Make sure this exists and is populated

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENTS = os.getenv("RECIPIENTS", "").split(",")

def fetch_recent_articles():
    all_articles = []
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=30)

    for keyword in KEYWORDS:
        print(f"🔍 Scraping news for keyword: {keyword}")
        search = GoogleSearch({
            "q": keyword,
            "tbm": "nws",
            "api_key": SERPAPI_API_KEY
        })

        results = search.get_dict()
        print(f"📦 Raw results for '{keyword}':", results)  # Debug line
        articles = results.get("news_results", [])

        for article in articles:
            title = article.get("title")
            link = article.get("link")
            date_str = article.get("date", "").strip()
            print(f"🗓️  Found date string: '{date_str}'")  # Debug line

            # Parse date string
            pub_date = parse_date_string(date_str)
            if pub_date and pub_date > cutoff_date:
                all_articles.append({
                    "keyword": keyword,
                    "title": title,
                    "link": link,
                    "date": pub_date.strftime("%Y-%m-%d")
                })

    return sorted(all_articles, key=lambda x: x["date"], reverse=True)

def parse_date_string(date_str):
    now = datetime.datetime.now()

    try:
        if "hour" in date_str or "minute" in date_str:
            return now
        elif "day" in date_str:
            days = int(date_str.split()[0])
            return now - datetime.timedelta(days=days)
        elif "Yesterday" in date_str:
            return now - datetime.timedelta(days=1)
        else:
            # Try direct parse
            return datetime.datetime.strptime(date_str, "%b %d, %Y")
    except Exception as e:
        print(f"⚠️ Failed to parse date '{date_str}': {e}")
        return None

def send_email(articles):
    if not articles:
        print("⚠️ No recent articles found.")
        return

    body = "📰 Malaysia Energy News Summary\n\n"
    for article in articles:
        body += f"[{article['date']}] ({article['keyword']}) {article['title']}\n{article['link']}\n\n"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Daily Energy News Digest - Malaysia"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(RECIPIENTS)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, RECIPIENTS, msg.as_string())
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    print("🔍 Scraping news...")
    recent_articles = fetch_recent_articles()
    send_email(recent_articles)
