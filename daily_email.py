import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Get environment variables
sender_email = os.getenv("SENDER_EMAIL", "ham19902008@gmail.com")
receiver_emails = ["ham19902008@gmail.com", "graham.tan@shizenenergy.net"]
app_password = os.getenv("EMAIL_APP_PASSWORD")  # ✅ Updated to match workflow

# Build your email
def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = ", ".join(receiver_emails)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_emails, msg.as_string())

        print("✅ Email sent successfully!")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
