import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

# Semaphore for local RTX 3050 limit (6GB VRAM) restricts concurrent usage to 2
gpu_semaphore = asyncio.Semaphore(2)

import json
from fastapi.responses import StreamingResponse

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "llama3"
    max_tokens: int | None = 100
    temperature: float | None = 0.7
    stream: bool = False

@app.get("/")
async def root():
    return {"message": "Krypton v1 Local Gateway Running"}

@app.post("/generate")
async def generate(request: GenerateRequest):
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
