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
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")  # FIXED name to match GitHub secret

EMAIL_RECIPIENTS = [
    "ham19902008@gmail.com",
    "graham.tan@shizenenergy.net"
]

# Debugging: Check if password is loaded
if not EMAIL_PASSWORD:
    print("❌ EMAIL_APP_PASSWORD environment variable not found!")
else:
    print("✅ EMAIL_APP_PASSWORD found")

# Keywords to search
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

# Limit date to last 30 days
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

# Collect results
articles = []

for keyword in keywords:
    params = {
        "engine": "google",
        "q": keyword,
        "location": "Malaysia",
        "api_key": SERPAPI_API_KEY,
        "num": "20"
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])

    for result in organic_results:
        title = result.get("title")
        link = result.get("link")
        date = result.get("date", "")
        if title and link:
            articles.append((date, title, link))

# Sort by most recent date (if possible)
def parse_date(d):
    try:
        return datetime.strptime(d, "%b %d, %Y")
    except:
        return datetime.min

articles.sort(key=lambda x: parse_date(x[0]), reverse=True)

# Create email content
email_body = "📰 <b>Daily Malaysia Energy News Summary</b><br><br>"
for date, title, link in articles:
    email_body += f"{date} - <a href='{link}'>{title}</a><br>"

# Build MIME email
message = MIMEMultipart("alternative")
message["Subject"] = "Daily Malaysia Energy News Summary"
message["From"] = EMAIL_SENDER
message["To"] = ", ".join(EMAIL_RECIPIENTS)

mime_text = MIMEText(email_body, "html")
message.attach(mime_text)

# Send email
try:
    print("📤 Preparing to send email...")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, message.as_string())
    print("✅ Email sent successfully!")
except Exception as e:
    print("❌ Failed to send email:", e)
