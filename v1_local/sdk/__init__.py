import httpx
from typing import Optional, Dict, Any
import json
import requests
class KryptonClient:
    """
    The official SDK for interacting with a Krypton AI Gateway.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000", email: str = None, webhook_url: str = None):
        if not base_url:
            raise ValueError("You must provide a base_url pointing to the Krypton server.")
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.webhook_url = webhook_url

    def generate(self, prompt: str, model: str = "llama3", max_tokens: int = 100, temperature: float = 0.7, stream: bool = False):
        """
        Send a prompt to the Krypton Gateway for LLM generation.
        If stream=True, returns a generator that yields parts of the response string.
        Otherwise, returns the complete response string.
        """
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
                # Normal synchronous generation
                response = httpx.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
                return response.json().get("response", "")
                
        except httpx.HTTPStatusError as e:
            raise Exception(f"Generation failed: {e.response.text}")
        except httpx.RequestError as e:
            if self.webhook_url and self.email:
                print("The Krypton Server is currently offline. Notifying the owner of your request...")
                try:
                    requests.post(self.webhook_url, json={
                        "email": self.email,
                        "message": f"User {self.email} is requesting access, but the server is offline."
                    })
                    print("The owner has been notified. You will receive an email once the server is online and you are approved.")
                except Exception as webhook_e:
                    print(f"Failed to notify owner: {str(webhook_e)}")
            else:
                print(f"Failed to connect to Krypton Server at {self.base_url}. Is the server running? Error: {str(e)}")
            raise Exception(f"Connection error: {str(e)}")

# Example usage string to help users
__doc__ = """
Welcome to the Krypton SDK.

Usage:
    from krypton_sdk import KryptonClient
    
    # 1. Connect to your friend's server
    client = KryptonClient(
        base_url="https://staminal-susann-inimitably.ngrok-free.dev",
        email="your_email@example.com",
        webhook_url="https://formspree.io/f/your_form_id" # Optional: Notifies owner if offline
    )
    
    # 2. Generate text! (The server safely limits GPU concurrency)
    response = client.generate("Write a haiku about a GPU.")
    print(response)
"""
