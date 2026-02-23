import httpx
from typing import Optional, Dict, Any

class KryptonClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def request_key(self, name: str, ttl_hours: int = 3) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/request-key",
                json={"name": name, "ttl_hours": ttl_hours},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            self.api_key = data["key"]
            print(f"Successfully registered as '{name}'. Key valid for {data['expires_in_hours']} hours.")
            return self.api_key
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise Exception("The Krypton server's local Ollama is currently offline.")
            raise Exception(f"Failed to request key: {e.response.text}")
        except Exception as e:
            raise Exception(f"Connection error: {str(e)}")

    def generate(self, prompt: str, model: str = "llama3", max_tokens: int = 100, temperature: float = 0.7) -> str:
        if not self.api_key:
            raise ValueError("No API key provided. Either pass it in __init__ or call request_key() first.")

        headers = {"X-API-Key": self.api_key}
        payload = {
            "prompt": prompt,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = httpx.post(
                f"{self.base_url}/generate",
                headers=headers,
                json=payload,
                timeout=120.0 # Generation might take a while depending on queue/hardware
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise PermissionError("API Key is invalid or expired.")
            raise Exception(f"Generation failed: {e.response.text}")
        except Exception as e:
            raise Exception(f"Connection error: {str(e)}")

# Example usage string to help users
__doc__ = """
Welcome to the Krypton SDK.

Usage:
    from krypton_sdk import KryptonClient
    
    # 1. Connect to your friend's server
    client = KryptonClient(base_url="https://their-public-url.ngrok-free.app")
    
    # 2. Request an access key (Only works if their Ollama is running)
    client.request_key(name="MyName")
    
    # 3. Generate text! (The server safely limits GPU concurrency)
    response = client.generate("Write a haiku about a GPU.")
    print(response)
"""
