import asyncio
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

async def test_krypton_gateway():
    print(f"\n--- Testing Krypton Local Gateway at {BASE_URL} ---")
    
    # 1. Test Gateway Status
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{BASE_URL}/")
            print(f"✅ Gateway Ping: {res.json()}")
    except Exception as e:
        print(f"❌ Gateway is OFFLINE! Did you run 'uvicorn v1_local.gateway:app --reload'?\nError: {e}")
        return

    # 2. Test requesting an API Key/Joining the Queue
    test_email = "saajancoding376@gmail.com"
    print(f"\n--- Requesting access for {test_email} ---")
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{BASE_URL}/join-queue", 
                json={"user_email": test_email}
            )
            data = res.json()
            status = data.get("status")
            
            if status == "success":
                api_key = data.get("api_key")
                print(f"✅ Success! Got API Key: {api_key}")
                print(f"   (Check your email for the API Key)")
            elif status == "waitlist":
                print(f"⏳ Server is Full (2 users active). Added to waitlist!")
                api_key = None
            else:
                print(f"❌ Unexpected response: {data}")
                return
    except Exception as e:
        print(f"❌ Failed to request access: {e}")
        return

    # 3. Test Generation Security (Without API Key)
    print(f"\n--- Testing Security (No API Key) ---")
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{BASE_URL}/generate",
                json={"prompt": "Say exactly: 'Access Denied Test'"},
                headers={} # Deliberately missing X-API-Key
            )
            if res.status_code == 401:
                print("✅ Security working: Rejected request without API Key.")
            else:
                print(f"❌ Security failure: Server allowed generation without API Key! Status: {res.status_code}")
    except Exception as e:
        print(f"❌ Test error: {e}")

    # 4. Test Generation (With API Key, if we got one)
    if api_key:
        print(f"\n--- Testing Generation (With API Key: {api_key}) ---")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{BASE_URL}/generate",
                    json={
                        "prompt": "Say exactly: 'Hello Krypton Server'",
                        "stream": False,
                        "max_tokens": 10
                    },
                    headers={"X-API-Key": api_key}
                )
                
                if res.status_code == 200:
                    print(f"✅ Generation Successful! Ollama replied:\n   {res.json().get('response', '').strip()}")
                elif res.status_code == 502:
                    print(f"⚠️ Gateway accepted key, but Ollama is not running on port 11434.")
                else:
                    print(f"❌ Generation failed with status {res.status_code}: {res.text}")
        except Exception as e:
            print(f"❌ Generation error: {e}")

if __name__ == "__main__":
    asyncio.run(test_krypton_gateway())
