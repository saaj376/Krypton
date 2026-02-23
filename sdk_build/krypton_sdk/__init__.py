import httpx
from typing import Optional, Dict, Any
import json

class KryptonClient:
    def __init__(self, base_url: str):
        if not base_url:
            raise ValueError("You must provide a base_url pointing to the Krypton server.")
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, model: str = "llama3", max_tokens: int = 100, temperature: float = 0.7, stream: bool = False):
        payload = {
            "prompt": prompt,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }

        try:
            if stream:
                # We yield words interactively
                def stream_generator():
                    with httpx.stream("POST", f"{self.base_url}/generate", json=payload, timeout=120.0) as response:
                        response.raise_for_status()
                        for line in response.iter_lines():
                            if line:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                return stream_generator()
            else:
                response = httpx.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    timeout=120.0 
                )
                response.raise_for_status()
                return response.json().get("response", "")
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"Krypton Server returned an error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to Krypton Server at {self.base_url}. Is the server running? Error: {str(e)}")
