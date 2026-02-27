import os
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
app=FastAPI()

class Settings(BaseSettings):
    sender_email: str = os.getenv("SENDER_EMAIL")
    sender_app_password: str = os.getenv("SENDER_APP_PASSWORD")
    owner_email: str = os.getenv("OWNER_EMAIL")

settings = Settings()

class AccessRequest(BaseModel):
    user_email: str

def send_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.sender_email, settings.sender_app_password)
            server.sendmail(settings.sender_email, to_email, msg.as_string())
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")

@app.post("/request-access")
async def request_access(req: AccessRequest):
    if not req.user_email:
        raise HTTPException(status_code=400, detail="Email is required")

    owner_subject = "ACTION REQUIRED: Krypton Server Request"
    owner_body = f"User {req.user_email} is waiting. Please start the Krypton GPU Server locally!"
    send_email(settings.owner_email, owner_subject, owner_body)

    user_subject = "Krypton Access Request Received"
    user_body = "Your request has been received. The owner is starting the server. You will be emailed your API key shortly."
    send_email(req.user_email, user_subject, user_body)

    return {"message": "Notification sent successfully"}