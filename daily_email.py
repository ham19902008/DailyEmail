import os
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from serpapi import GoogleSearch
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

# ---- Secrets / Email ----
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
EMAIL_SENDER = "ham19902008@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

EMAIL_RECIPIENTS = [
    "ham19902008@gmail.com",
    "graham.tan@shizenenergy.net",

]

if not EMAIL_PASSWORD:
    print("❌ EMAIL_APP_PASSWORD not found in environment!")
else:
    print("✅ EMAIL_APP_PASSWORD loaded.")

# ---- Keywords ----
KEYWORDS = [
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
    "high voltage malaysia",
       "Tenaga Nasional Berhad",
       "TNB", 
       "Ministry of Energy Transition and Water Transformation",
       "PETRA",
       "Data center Malaysia",
]

# ---- Config ----
LOOKBACK_DAYS = 7  # wider window to avoid misses due to timezones / late stamps
START_CUTOFF = datetime.now() - timedelta(days=LOOKBACK_DAYS)

def strip_tracking(u: str) -> str:
    """Remove common tracking params to improve de-duplication."""
    try:
        p = urlparse(u)
        q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith(("utm_", "gclid", "fbclid"))]
        return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(q), p.fragment))
    except Exception:
        return u

def parse_date(date_str: str):
    """Parse absolute and relative dates found in SerpApi results."""
    if not date_str:
        return None
    s = date_str.strip()
    now = datetime.now()

    # Absolute formats
    abs_formats = [
        "%b %d, %Y",        # Aug 11, 2025
        "%B %d, %Y",        # August 11, 2025
        "%Y-%m-%d",         # 2025-08-11
        "%b %d, %Y %I:%M %p",
        "%B %d, %Y %I:%M %p",
    ]
    for fmt in abs_formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass

    # Normalize
    sl = s.lower()

    # Common words
    if "yesterday" in sl:
        return now - timedelta(days=1)
    if "today" in sl:
        return now

    # Relative like "2 hours ago", "3 days ago", "1 week ago", "4 months ago", "2 years ago"
    m = re.search(r"(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago", sl)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit == "minute":
            return now - timedelta(minutes=n)
        if unit == "hour":
            return now - timedelta(hours=n)
        if unit == "day":
            return now - timedelta(days=n)
        if unit == "week":
            return now - timedelta(weeks=n)
        if unit == "month":
            return now - timedelta(days=30*n)  # approx
        if unit == "year":
            return now - timedelta(days=365*n) # approx

    # Fallback: if it mentions "hour" or "minute" without a number, treat as now
    if "hour" in sl or "minute" in sl:
        return now

    return None

def fetch_google_news(keyword: str):
    """Use SerpApi Google News engine (most reliable for fresh news)."""
    params = {
        "engine": "google_news",
        "q": keyword,
        "api_key": SERPAPI_API_KEY,
        "gl": "my",            # country bias: Malaysia
        "hl": "en",            # language
        "when": "7d",          # last 7 days
        "sort_by": "date",     # newest first
        "num": "100",
        "no_cache": "true",
        "safe": "off",
    }
    return GoogleSearch(params).get_dict()

def fetch_google_tbm_news(keyword: str):
    """Fallback: Google web engine with tbm=nws (news tab)."""
    params = {
        "engine": "google",
        "q": keyword,
        "api_key": SERPAPI_API_KEY,
        "gl": "my",
        "hl": "en",
        "tbm": "nws",
        "num": "50",
        "no_cache": "true",
        "safe": "off",
    }
    return GoogleSearch(params).get_dict()

def collect_articles():
    items = []

    for kw in KEYWORDS:
        print(f"🔎 Google News: {kw}")
        try:
            gn = fetch_google_news(kw)
        except Exception as e:
            print("Google News fetch error:", e)
            gn = {}

        # google_news returns typically 'news_results' and sometimes 'stories_results'
        for res in gn.get("news_results", []):
            title = res.get("title")
            link = res.get("link")
            date_str = res.get("date")
            pub_time = parse_date(date_str)
            if title and link and pub_time and pub_time >= START_CUTOFF:
                items.append((pub_time, title, link))

        for story in gn.get("stories_results", []):
            # story may have 'news_articles' list with similar fields
            for art in story.get("news_articles", []):
                title = art.get("title")
                link = art.get("link")
                date_str = art.get("date")
                pub_time = parse_date(date_str)
                if title and link and pub_time and pub_time >= START_CUTOFF:
                    items.append((pub_time, title, link))

        print(f"🔎 Google TBM=nws fallback: {kw}")
        try:
            tbm = fetch_google_tbm_news(kw)
        except Exception as e:
            print("Google tbm=nws fetch error:", e)
            tbm = {}

        for res in tbm.get("news_results", []):
            title = res.get("title")
            link = res.get("link")
            date_str = res.get("date")
            pub_time = parse_date(date_str)
            if title and link and pub_time and pub_time >= START_CUTOFF:
                items.append((pub_time, title, link))

    # De-duplicate by stripped URL
    seen = set()
    uniq = []
    for dt, title, link in items:
        clean = strip_tracking(link)
        if clean not in seen:
            seen.add(clean)
            uniq.append((dt, title, clean))

    # Sort newest first
    uniq.sort(key=lambda x: x[0], reverse=True)
    return uniq

def build_email_body(articles):
    if not articles:
        return "⚠️ No new articles found in the last few days."

    body = ["📰 <b>Daily Malaysia Energy News Summary</b><br><br>"]
    for dt, title, link in articles:
        # show timestamp (local) for transparency
        body.append(f"{dt.strftime('%Y-%m-%d %H:%M')} — <a href='{link}'>{title}</a><br>")
    return "".join(body)

# ---- Run fetch + email ----
articles = collect_articles()
email_body = build_email_body(articles)

message = MIMEMultipart("alternative")
message["Subject"] = "Daily Malaysia Energy News Summary"
message["From"] = EMAIL_SENDER
message["To"] = ", ".join(EMAIL_RECIPIENTS)
message.attach(MIMEText(email_body, "html"))

try:
    print(f"📤 Sending email... ({len(articles)} articles)")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, message.as_string())
    print("✅ Email sent successfully!")
except Exception as e:
    print("❌ Failed to send email:", e)
