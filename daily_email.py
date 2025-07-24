import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from serpapi import GoogleSearch

# Load environment variables
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
EMAIL_SENDER = "ham19902008@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")  # Correct secret name

EMAIL_RECIPIENTS = [
    "ham19902008@gmail.com",
    "graham.tan@shizenenergy.net",
    "reza.ikram@shizenenergy.net",
    "redha.mahzar@shizenenergy.net"
]

# Debug: Check if secrets are loaded
if not EMAIL_PASSWORD:
    print("❌ EMAIL_APP_PASSWORD not found in environment!")
else:
    print("✅ EMAIL_APP_PASSWORD loaded.")

# Define keywords
keywords = [
    "renewable energy malaysia",
    "solar malaysia",
    "corporate renewable energy supply scheme malaysia",
    "cress malaysia",
    "ppa malaysia",
    "rp4 malaysia",
    "review period 4 malaysia",
    "energy commission malaysia",
    "suruhanjaya tenaga",
    "electricity malaysia",
    "electricity tariff malaysia",
    "energy malaysia",
    "voltage malaysia"
]

# Set time window
start_cutoff = datetime.now() - timedelta(days=3)  # Capture last 3 days including today

# Store articles with date
articles = []

def fuzzy_parse_date(date_str):
    now = datetime.now()
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%b %d, %Y")
    except:
        pass
    try:
        if "hour" in date_str or "minute" in date_str:
            return now
        elif "day ago" in date_str:
            num = int(date_str.split()[0])
            return now - timedelta(days=num)
    except:
        return None
    return None

for keyword in keywords:
    print(f"🔍 Searching: {keyword}")
    params = {
        "engine": "google",
        "q": keyword,
        "location": "Malaysia",
        "api_key": SERPAPI_API_KEY,
        "num": "30"
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    news_results = results.get("news_results", [])
    organic_results = results.get("organic_results", [])

    # Parse news_results
    for res in news_results:
        title = res.get("title")
        link = res.get("link")
        date_str = res.get("date")
        pub_time = fuzzy_parse_date(date_str)
        if title and link and pub_time and pub_time >= start_cutoff:
            articles.append((pub_time, title, link))

    # Parse organic_results
    for res in organic_results:
        title = res.get("title")
        link = res.get("link")
        date_str = res.get("date", "")
        pub_time = fuzzy_parse_date(date_str)
        if title and link and pub_time and pub_time >= start_cutoff:
            articles.append((pub_time, title, link))

# Remove duplicates
seen_links = set()
unique_articles = []
for article in articles:
    if article[2] not in seen_links:
        seen_links.add(article[2])
        unique_articles.append(article)

# Sort newest first
unique_articles.sort(key=lambda x: x[0], reverse=True)

# Build email body
if unique_articles:
    email_body = "📰 <b>Daily Malaysia Energy News Summary</b><br><br>"
    for dt, title, link in unique_articles:
        formatted_date = dt.strftime('%Y-%m-%d')
        email_body += f"{formatted_date} - <a href='{link}'>{title}</a><br>"
else:
    email_body = "⚠️ No new articles found in the last few days."

# Construct and send email
message = MIMEMultipart("alternative")
message["Subject"] = "Daily Malaysia Energy News Summary"
message["From"] = EMAIL_SENDER
message["To"] = ", ".join(EMAIL_RECIPIENTS)
mime_text = MIMEText(email_body, "html")
message.attach(mime_text)

try:
    print("📤 Sending email...")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, message.as_string())
    print("✅ Email sent successfully!")
except Exception as e:
    print("❌ Failed to send email:", e)
