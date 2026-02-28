import sys
import os

# Temporarily point to the local sdk_build directory so we don't need to pip install it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../sdk_build')))
from krypton_sdk import KryptonClient

def run_online_test():
    print("=========================================")
    print("   KRYPTON SDK - ONLINE GATEWAY TEST   ")
    print("=========================================\n")
    print("⚠️  REQUIREMENT: Make sure your local gateway is RUNNING!")
    print("   (Run `uvicorn v1_local.gateway:app` in another terminal)\n")
    
    email = "saajancoding376@gmail.com"
    print(f"Initializing SDK with email: {email}")
    client = KryptonClient(email=email, base_url="http://127.0.0.1:8000")
    
    print("\n--- 1. Testing: Join Queue ---")
    client.join_queue()
    
    if not client.api_key:
        print("❌ Failed to get an API key. Is the server full or offline?")
        return

    print("\n--- 2. Testing: Generation (Non-Streaming) ---")
    prompt = "What is the capital of France? Answer in exactly one word."
    print(f"Sending prompt: '{prompt}'")
    try:
        response = client.generate(prompt=prompt, model="llama3", max_tokens=10)
        print(f"🤖 Response: {response}")
    except Exception as e:
        print(f"❌ Generation failed: {e}")

    print("\n--- 3. Testing: Generation (Streaming) ---")
    prompt_stream = "Count from 1 to 5."
    print(f"Sending prompt: '{prompt_stream}'")
    try:
        stream_response = client.generate(prompt=prompt_stream, model="llama3", max_tokens=20, stream=True)
        if stream_response:
            print("🤖 Response: ", end="", flush=True)
            for chunk in stream_response:
                print(chunk, end="", flush=True)
            print("\n✅ Stream completed successfully.")
    except Exception as e:
        print(f"❌ Streaming failed: {e}")

if __name__ == "__main__":
    run_online_test()
