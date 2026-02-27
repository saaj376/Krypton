# Krypton Ping Server (Always-On Cloud App)

This directory contains the micro-service that stays online 24/7. Its **only job** is to act as a receptionist when your powerful local GPU machine is turned off. 

When a user tries to use the Krypton SDK and your local server is down, the SDK automatically hits this Ping Server. This server then sends an email to you ("Wake up!") and an email to the user ("The owner is turning the server on").

## 🚀 Step-by-Step Deployment Guide

### Step 1: Get a Google App Password
Since we are sending emails simply and reliably without 3rd party providers, we will use Python's built-in `smtplib` via Gmail. You cannot use your normal Gmail password.

1. Go to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Ensure **2-Step Verification** is turned ON.
3. Search for **App Passwords** in the search bar.
4. Create a new App Password (name it "Krypton Ping Server").
5. Copy the 16-character password it gives you. Keep this safe; you will need it soon.

### Step 2: Create the Environment File
We never hardcode passwords in the code.

1. Inside the `ping_server` directory, create a file named `.env`.
2. Add the following variables:
   ```env
   SENDER_EMAIL=your_actual_email@gmail.com
   SENDER_APP_PASSWORD=the_16_char_password_from_step_1
   OWNER_EMAIL=your_actual_email@gmail.com
   ```
*(Note: `OWNER_EMAIL` is the email you want the notification sent to. It can be the same as `SENDER_EMAIL`).*

### Step 3: Write the Code (`main.py`)
Create a file named `main.py` in this directory. We are keeping it extremely lightweight using FastAPI.

```python
import os
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

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

    # 1. Alert the Owner
    owner_subject = "🔴 ACTION REQUIRED: Krypton Server Request"
    owner_body = f"User {req.user_email} is waiting. Please start the Krypton GPU Server locally!"
    send_email(settings.owner_email, owner_subject, owner_body)

    # 2. Reassure the User
    user_subject = "Krypton Access Request Received"
    user_body = "Your request has been received. The owner is starting the server. You will be emailed your API key shortly."
    send_email(req.user_email, user_subject, user_body)

    return {"message": "Notification sent successfully"}
```

### Step 4: Create Tracking Files (`requirements.txt`)
Cloud providers need to know what Python packages to install to run your server.
Create a file named `requirements.txt` containing:
```text
fastapi
uvicorn
pydantic
pydantic_settings
python-dotenv
```

### Step 5: Test Locally (Optional but Recommended)
Before putting it on the internet, make sure your emails work!
1. Open a terminal in the `ping_server` directory.
2. Run `pip install -r requirements.txt`.
3. Run `uvicorn main:app --reload`.
4. Send a test POST request to `http://127.0.0.1:8000/request-access` with a JSON body `{"user_email": "test@example.com"}`. 
5. Check your Gmail inbox for the notifications!

### Step 6: Deploy for Free to the Cloud (Render.com)
Now we put it on the public internet so the SDK can always reach it. Render is great for this because it connects directly to GitHub for free.

1. **Commit to GitHub:** Push your entire project (including `ping_server`, but **exclude the `.env` file!**) to GitHub. Ensure `.env` is in your `.gitignore`.
2. **Go to Render.com:** Create a free account and click **New > Web Service**.
3. **Connect GitHub:** Link your repository.
4. **Configure Settings:**
   * **Root Directory:** `ping_server`
   * **Environment:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variables:** In Render's dashboard, go to the "Environment Variables" section of your new service and manually add the variables from your `.env` file (`SENDER_EMAIL`, `SENDER_APP_PASSWORD`, `OWNER_EMAIL`).
6. **Deploy!** Click Create.

Within 5 minutes, Render will give you a public URL (e.g., `https://krypton-ping.onrender.com`). 
You will use this URL inside the Python SDK so it always has a permanent address to ping when your local machine is asleep!
