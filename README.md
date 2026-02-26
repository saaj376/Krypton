# Krypton
Krypton is a production-grade LLM gateway for local Llama 3 hosting. It turns an RTX 3050 into a private cloud using a custom SDK, and async semaphores to prevent GPU crashes. It's the ultimate hackathon tool for unlimited, safe AI access.

# Krypton Client Setup

Welcome to the Krypton network! To connect to a friend's RTX 3050 LLM Gateway, follow these simple steps.

## Option 1: Using the Krypton SDK (Python)

If you use Python, simply copy the `v1_local/sdk/__init__.py` file into your project (name the folder `krypton_sdk`).

```python
from krypton_sdk import KryptonClient

# 1. Connect to your friend's gateway URL (they should provide an ngrok link)
client = KryptonClient(base_url="https://staminal-susann-inimitably.ngrok-free.dev")

# 2. Use the LLM!
response = client.generate("Why is the sky blue?", model="llama3")
print(response)
```

## Option 2: Using simple cURL

You don't need any special tools. Just HTTP:

```bash
curl -X POST https://staminal-susann-inimitably.ngrok-free.dev/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Write a poem about GPUs"}'
```
