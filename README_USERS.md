# Krypton Client Setup

Welcome to the Krypton network! To connect to a friend's RTX 3050 LLM Gateway, follow these simple steps.

## Option 1: Using the Krypton SDK (Python)

If you use Python, simply copy the `v1_local/sdk/__init__.py` file into your project (name the folder `krypton_sdk`).

```python
from krypton_sdk import KryptonClient

# 1. Connect to your friend's gateway URL (they should provide an ngrok link)
client = KryptonClient(base_url="https://their-public-url.ngrok-free.app")

# 2. Request a key (This will fail if their Ollama isn't running right now)
client.request_key(name="YourName")

# 3. Use the LLM!
response = client.generate("Why is the sky blue?", model="llama3")
print(response)
```

## Option 2: Using the CLI

If you just want to grab a key via Terminal, you can use the CLI tool. 
First, make sure you have `httpx` and `typer` installed (`pip install httpx typer`).

```bash
# Ask the gateway for a key
python manage.py request-key "YourName" --server-url https://their-public-url.ngrok-free.app
```
*Output:*
```text
Success! Server generated a key for 'YourName'.
Key: aB3cD4eF5gH6iJ7...
This key will expire in 3 hours.
```

## Option 3: Using simple cURL

You don't need any special tools. Just HTTP:

**Step 1. Get a key:**
```bash
curl -X POST https://their-public-url.ngrok-free.app/request-key \
     -H "Content-Type: application/json" \
     -d '{"name": "YourName"}'
```

**Step 2. Generate:**
```bash
curl -X POST https://their-public-url.ngrok-free.app/generate \
     -H "X-API-Key: THE-KEY-YOU-GOT-IN-STEP-1" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Write a poem about GPUs"}'
```
