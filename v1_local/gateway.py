import os
import smtplib
from email.mime.text import MIMEText
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import httpx
from contextlib import asynccontextmanager
import json
from fastapi.responses import StreamingResponse
import uuid
from shared.database import (
    count_active_keys, create_key, add_to_waitlist, 
    get_connection, pop_from_waitlist, validate_key
)
from datetime import datetime, timezone

load_dotenv()

class Settings(BaseSettings):
    sender_email: str = os.getenv("SENDER_EMAIL", "")
    sender_app_password: str = os.getenv("SENDER_APP_PASSWORD", "")
    owner_email: str = os.getenv("OWNER_EMAIL", "")

settings = Settings()

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

async def enforce_expirations():
    while True:
        await asyncio.sleep(60) # Run every 60 seconds
        
        now_str = datetime.now(timezone.utc).isoformat()
        expired_emails = []
        
        # 1. Find and Delete Expired Keys
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT owner_name FROM api_keys WHERE expires_at < ?', (now_str,))
            rows = cursor.fetchall()
            
            for row in rows:
                expired_emails.append(row[0])
                
            if expired_emails:
                cursor.execute('DELETE FROM api_keys WHERE expires_at < ?', (now_str,))
                conn.commit()

        # 2. Email Expired Users
        for email in expired_emails:
            print(f"[ALERT] API Key for {email} has expired! Removing.")
            send_email(email, "Krypton Session Expired", "Your 3-hour session on Krypton has ended. Thank you for using the service!")

            # 3. Promote from Waitlist since a slot just opened!
            next_user = pop_from_waitlist()
            if next_user:
                new_key = f"kr_{uuid.uuid4().hex}"
                create_key(new_key, next_user, ttl_hours=3)
                print(f"[QUEUE] Promoted {next_user} from waitlist!")
                send_email(next_user, "Your Krypton API Key is Ready!", f"The server is free! Your turn. Here is your API key: {new_key}\n(Valid for 3 hours).")

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(enforce_expirations())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

# Semaphore for local RTX 3050 limit (6GB VRAM) restricts concurrent usage to 2
gpu_semaphore = asyncio.Semaphore(2)

class QueueRequest(BaseModel):
    user_email: str

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "llama3"
    max_tokens: int | None = 100
    temperature: float | None = 0.7
    stream: bool = False

async def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header missing")
    if not validate_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid or expired API Key")
    return x_api_key

@app.get("/")
async def root():
    return {"message": "Krypton v1 Local Gateway Running"}

@app.post("/join-queue")
async def join_queue(req: QueueRequest):
    active_count = count_active_keys()
       
    if active_count < 2:
        new_api_key = f"kr_{uuid.uuid4().hex}"
        create_key(new_api_key, req.user_email, ttl_hours=3)
        
        body = f"The server is free! Your API key is: {new_api_key}\nIt is valid for exactly 3 hours."
        send_email(req.user_email, "Your Krypton API Key", body)
        
        return {"status": "success", "api_key": new_api_key, "message": "API Key generated and emailed."}
    else:
        add_to_waitlist(req.user_email)
        body = "The Krypton Server is currently at max capacity (2 users). You have been added to the waitlist! We will email you your API key automatically when a slot opens."
        send_email(req.user_email, "Krypton Waitlist Confirmation", body)
        
        return {"status": "waitlist", "message": "Server at capacity. Added to waitlist."}

@app.post("/generate")
async def generate(request: GenerateRequest, api_key: str = Depends(verify_api_key)):
    async def stream_generator():
        async with gpu_semaphore:
            try:
                async with httpx.AsyncClient() as client:
                    async with client.stream(
                        "POST",
                        "http://localhost:11434/api/generate",
                        json={
                            "model": request.model,
                            "prompt": request.prompt,
                            "stream": True,
                            "options": {
                                "temperature": request.temperature,
                                "num_predict": request.max_tokens
                            }
                        },
                        timeout=120.0
                    ) as response:
                        response.raise_for_status()
                        async for chunk in response.aiter_bytes():
                            yield chunk
            except httpx.RequestError as e:
                yield json.dumps({"error": f"Ollama connection error: {str(e)}"}).encode()
            except Exception as e:
                yield json.dumps({"error": str(e)}).encode()

    if request.stream:
        return StreamingResponse(stream_generator(), media_type="application/x-ndjson")
    
    # Non-streaming (Wait and collect all data in memory safely)
    async with gpu_semaphore:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": request.model,
                        "prompt": request.prompt,
                        "stream": False,
                        "options": {
                            "temperature": request.temperature,
                            "num_predict": request.max_tokens
                        }
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "response": data.get("response", ""),
                    "ollama_raw": data
                }
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Ollama connection error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))