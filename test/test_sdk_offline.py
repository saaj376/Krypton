import sys
import os

# Temporarily point to the local sdk_build directory so we don't need to pip install it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../sdk_build')))
from krypton_sdk import KryptonClient

def run_offline_test():
    print("=========================================")
    print("   KRYPTON SDK - OFFLINE FALLBACK TEST   ")
    print("=========================================\n")
    print("⚠️  REQUIREMENT: Make sure your local gateway is OFF!")
    print("   (Kill any running uvicorn processes in terminals)\n")
    
    email = "saajancoding376@gmail.com"
    print(f"Initializing SDK with email: {email}")
    client = KryptonClient(email=email, base_url="http://127.0.0.1:8000")
    
    print("\n--- 1. Testing: Fallback on Join Queue ---")
    print("Description: Attempting to connect to an offline gateway. This should automatically catch the ConnectError and ping the Render Cloud Server.")
    print("Expected: '[Krypton] Central GPU Server is offline! Notifying the owner to start it...'")
    client.join_queue()

    print("\n--- 2. Testing: Fallback on Text Generation ---")
    client.api_key = "fake_key_to_bypass_first_check"
    try:
        client.generate("This request shouldn't reach Ollama because the gateway is off.")
    except Exception as e:
        print(f"Test Exception caught (as expected or unexpected): {e}")

if __name__ == "__main__":
    run_offline_test()
