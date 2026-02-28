import httpx
from typing import Optional, Dict, Any, Generator
import json

class KryptonClient:
    def __init__(self, email: str, base_url: str, api_key: str = None):
        if not base_url or not email:
            raise ValueError("You must provide both an email and a base_url.")
        
        self.email = email
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.ping_server_url = "https://krypton-pl4h.onrender.com/request-access"

    def _notify_offline_server(self):
        print("\n[Krypton] Central GPU Server is offline! Notifying the owner to start it...")
        try:
            response = httpx.post(
                self.ping_server_url,
                json={"user_email": self.email},
                timeout=10.0
            )
            if response.status_code == 200:
                print("[Krypton] Owner notified. You will receive an email shortly once the server is online.")
            else:
                print(f"[Krypton] Failed to notify owner via Ping Server. Status: {response.status_code}")
        except Exception as e:
            print(f"[Krypton] Could not reach offline Ping Server either: {e}")

    def join_queue(self):
        try:
            response = httpx.post(
                f"{self.base_url}/join-queue",
                json={"user_email": self.email},
                timeout=15.0
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                self.api_key = data.get("api_key")
                print(f"[Krypton] Success! Received API Key: {self.api_key}")
                print("[Krypton] (It is also in your email inbox).")
            elif data.get("status") == "waitlist":
                print("[Krypton] Server is full. You have been added to the waitlist. Check your email when you are promoted.")
            else:
                print(f"[Krypton] Unexpected response: {data}")
                
        except httpx.ConnectError:
            self._notify_offline_server()
        except Exception as e:
            print(f"[Krypton] Error joining queue: {e}")

    def generate(self, prompt: str, model: str = "llama3", max_tokens: int = 100, temperature: float = 0.7, stream: bool = False):
        if not self.api_key:
            print("[Krypton] You must provide an api_key to generate, or call client.join_queue() first.")
            return None

        payload = {
            "prompt": prompt,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        headers = {
            "X-API-Key": self.api_key
        }

        try:
            if stream:
                def stream_generator():
                    with httpx.stream("POST", f"{self.base_url}/generate", json=payload, headers=headers, timeout=120.0) as response:
                        if response.status_code == 401:
                            print("\n[Krypton] API Key is Invalid or Expired.")
                            return
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
                    headers=headers,
                    timeout=120.0 
                )
                if response.status_code == 401:
                    print("\n[Krypton] API Key is Invalid or Expired.")
                    return None
                response.raise_for_status()
                return response.json().get("response", "")
            
        except httpx.ConnectError:
            self._notify_offline_server()
            return None
        except httpx.HTTPStatusError as e:
            raise Exception(f"Krypton Server returned an error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to Krypton Server at {self.base_url}: {str(e)}")
