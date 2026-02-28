import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD")

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        # Test WITH spaces exactly as it is in the gateway
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        print("✅ Logged in successfully with spaces!")
except Exception as e:
    print(f"❌ Error: {e}")
