import os
import smtplib
from email.message import EmailMessage
from serpapi import GoogleSearch
from datetime import datetime, timedelta
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

openai.api_key = OPENAI_API_KEY

# Define keywords here directly
KEYWORDS = [
    "renewables Malaysia",
    "solar Malaysia",
    "Tenaga Nasional Berhad",
    "TNB green energy",
    "Malaysia energy transition",
    "hydropower Malaysia",
    "energy policy Malaysia",
    "carbon neutrality Malaysia",
    "battery storage Malaysia",
    "EV Malaysia",
    "Petronas hydrogen",
    "clean energy Malaysia"
]

def search_articles(keywords, max_articles=30):
    articles = []
    cutoff_date = datetime.now() - timedelta(days=1)
    print("🔍 Scraping news...")

    for keyword in keywords:
        params = {
            "engine": "google",
            "q": keyword,
            "tbm": "nws",
            "api_key": SERPAPI_API_KEY
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        news_results = results.get("news_results", [])
        
        for result in news_results:
            try:
                date_str = result.get("date", "")
                link = result.get("link")
                title = result.get("title")

                # Parse date string to datetime
                published = parse_date(date_str)
                if published and published > cutoff_date:
                    articles.append({
                        "title": title,
                        "link": link,
                        "published": published.strftime('%Y-%m-%d %H:%M'),
                        "keyword": keyword
                    })
                    if len(articles) >= max_articles:
                        return articles
            except Exception as e:
                print(f"❗ Error parsing article: {e}")
                continue

    return articles

def parse_date(date_str):
    now = datetime.now()
    if "hour" in date_str or "min" in date_str:
        return now
    if "day ago" in date_str or "days ago" in date_str:
        days = int(date_str.split()[0])
        return now - timedelta(days=days)
    try:
        return datetime.strptime(date_str, "%b %d, %Y")
    except:
        return None

def summarize_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who summarizes news articles."},
                {"role": "user", "content": f"Summarize this article title and topic in 2-3 lines: {text}"}
            ],
            temperature=0.5,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(Summary failed: {e})"

def send_email(articles):
    msg = EmailMessage()
    msg["Subject"] = "📰 Daily Malaysia Energy News Summary"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ["ham19902008@gmail.com", "graham.tan@shizenenergy.net"]

    if not articles:
        msg.set_content("No recent articles found in the last 24 hours.")
    else:
        content = "Here are the latest articles:\n\n"
        for article in articles:
            summary = summarize_text(article["title"])
            content += f"🗞️ *{article['title']}*\n🔗 {article['link']}\n📅 {article['published']}\n💡 {summary}\n\n"
        msg.set_content(content)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def main():
    articles = search_articles(KEYWORDS, max_articles=30)
    if not articles:
        print("⚠️ No recent articles found.")
    else:
        print(f"✅ Found {len(articles)} recent articles.")
    send_email(articles)

if __name__ == "__main__":
    main()
