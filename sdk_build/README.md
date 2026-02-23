# Krypton SDK

A super lightweight pip package allowing clients to connect to a remotely hosted Krypton Gateway over the internet. 

**Zero VRAM required on the client side! You do not need to download the Llama model.** 

All inference happens on the remote host's GPU.

## Installation

```bash
pip install krypton-sdk
```

## Usage

You must provide the public URL of the Krypton gateway (usually an ngrok or localtunnel link provided by the host).

```python
from krypton_sdk import KryptonClient

# 1. Connect to the remote server over the internet
client = KryptonClient(base_url="https://staminal-susann-inimitably.ngrok-free.dev")

# 2. Generate text! The heavy lifting happens remotely.
response = client.generate(
    prompt="Explain quantum computing in one sentence.",
    model="llama3",
    max_tokens=200
)

print(response)
```
