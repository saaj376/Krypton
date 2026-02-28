import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD")

print(f"SENDER_EMAIL: {SENDER_EMAIL}")
print(f"SENDER_APP_PASSWORD length: {len(SENDER_APP_PASSWORD) if SENDER_APP_PASSWORD else 0}")

to_email = "saajancoding376@gmail.com"
subject = "Krypton Manual Test"
body = "This is a direct test."

msg = MIMEText(body)
msg["Subject"] = subject
msg["From"] = SENDER_EMAIL
msg["To"] = to_email

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        # server.set_debuglevel(1)
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD.replace(" ", ""))
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Error sending email: {e}")
