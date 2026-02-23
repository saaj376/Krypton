import httpx
from typing import Optional, Dict, Any

class KryptonClient:
    """
    The official SDK for interacting with a Krypton AI Gateway.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        # Remove trailing slashes for consistency
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, model: str = "llama3", max_tokens: int = 100, temperature: float = 0.7) -> str:
        """
        Send a prompt to the Krypton Gateway for LLM generation.
        """
        payload = {
            "prompt": prompt,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = httpx.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=120.0 # Generation might take a while depending on queue/hardware
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except httpx.HTTPStatusError as e:
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
    
    # 2. Generate text! (The server safely limits GPU concurrency)
    response = client.generate("Write a haiku about a GPU.")
    print(response)
"""
