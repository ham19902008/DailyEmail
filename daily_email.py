import datetime
import smtplib
from email.mime.text import MIMEText
from serpapi import GoogleSearch
from dateutil import parser
import os

# List of keywords to search
KEYWORDS = [
    "renewable energy", "solar", "corporate renewable energy supply scheme",
    "cress", "ppa", "rp4", "review period 4", "energy commission",
    "suruhanjaya tenaga", "electricity", "electricity tariff", "energy", "voltage"
]

# Email settings from GitHub Secrets or local .env
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENTS = ["ham19902008@gmail.com", "graham.tan@shizenenergy.net"]
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# Search and collect news articles from the past 30 days
def fetch_recent_articles():
    print("🔍 Scraping news...")
    recent_articles = []
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=30)

    for keyword in KEYWORDS:
        search = GoogleSearch({
            "q": f"{keyword} malaysia",
            "tbm": "nws",
            "num": 10,
            "api_key": SERPAPI_API_KEY
        })
        results = search.get_dict()
        articles = results.get("news_results", [])

        for article in articles:
            title = article.get("title", "No title")
            link = article.get("link", "")
            published_str = article.get("date", "").strip()

            try:
                published_dt = parser.parse(published_str)
                if published_dt >= cutoff_date:
                    formatted_date = published_dt.strftime("%Y-%m-%d")
                    recent_articles.append({
                        "title": title,
                        "link": link,
                        "published": formatted_date
                    })
                else:
                    print(f"🕒 Skipped (too old): {title} — {published_dt}")
            except Exception as e:
                print(f"⚠️ Failed to parse date for: {title} — raw: '{published_str}' — error: {e}")

    return sorted(recent_articles, key=lambda x: x["published"], reverse=True)

# Format email content
def build_email_body(articles):
    if not articles:
        return "No recent articles found in the last 30 days."

    body = "📰 *Malaysia Energy News Digest*\n\n"
    for article in articles:
        body += f"- {article['published']}: [{article['title']}]({article['link']})\n"
    return body

# Send the email
def send_email(subject, body):
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(RECIPIENTS)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, RECIPIENTS, msg.as_string())

    print("✅ Email sent successfully!")

# Main function
def main():
    articles = fetch_recent_articles()

    if not articles:
        print("⚠️ No recent articles found.")
        return

    email_subject = f"Malaysia Energy News — {datetime.datetime.now().strftime('%Y-%m-%d')}"
    email_body = build_email_body(articles)
    send_email(email_subject, email_body)

if __name__ == "__main__":
    main()
