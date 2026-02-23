import asyncio
import sys
import os

# Add project root to path so we can import shared modules if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import httpx

from shared.auth import verify_access

app = FastAPI()

# Semaphore for local RTX 3050 limit (6GB VRAM) restricts concurrent usage to 2
gpu_semaphore = asyncio.Semaphore(2)

# Define the expected API Key header
api_key_header = APIKeyHeader(name="X-API-Key")

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "llama3"
    max_tokens: int | None = 100
    temperature: float | None = 0.7

async def check_api_key(api_key: str = Security(api_key_header)):
    """Dependency to validate the API key."""
    if not verify_access(api_key):  
        raise HTTPException(status_code=403, detail="Invalid or expired API Key")
    return api_key

@app.get("/")
async def root():
    return {"message": "Krypton v1 Local Gateway Running"}

@app.post("/generate")
async def generate(request: GenerateRequest, api_key: str = Security(check_api_key)):
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
