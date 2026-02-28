# Krypton SDK

![PyPI - Version](https://img.shields.io/pypi/v/krypton-sdk)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/krypton-sdk)
![License](https://img.shields.io/github/license/saaj376/krypton)

A fully-featured, ultra-lightweight Python SDK that allows clients to connect to a remotely hosted Krypton AI Gateway over the internet.

**Zero VRAM required on the client side! You do not need to download your own LLaMA models.**

All the heavy lifting and inference happens on the remote host's GPU seamlessly.

---

## 🌟 Key Features

1. **Remote AI Inference**: Connect to powerful remote GPUs using your local machines without worrying about hardware bottlenecks.
2. **Smart Queueing System**: Automatically handles waitlists! If the remote server is at maximum capacity, you are placed in a waitlist and automatically emailed a session token when your slot is ready.
3. **Streaming Support**: Instantly stream generation tokens to your terminal/application instead of waiting for the full response to finish generating.
4. **Offline Support (Fallback Notification)**: If the host gateway goes completely offline, the SDK gracefully catches the network failure and pings a centralized server to automatically notify the host owner via email to turn their machine back on!
5. **Secure Authentication**: Uses dynamic API sessions restricted by time limits (e.g., 3 hours).

---

## 🚀 Installation

Install the package directly via pip:

```bash
pip install krypton-sdk
```

---

## 📘 Quickstart Guide

### 1. Initialization
Provide your email and the public URL of the active Krypton gateway (such as an ngrok, Render, or localtunnel link provided by the host).

```python
from krypton_sdk import KryptonClient

client = KryptonClient(
    email="your_email@example.com", 
    base_url="http://your-gateway-url.com"
)
```

### 2. Joining the Queue
Before generating, you must request an API Key (session token).

```python
# The server will check capacity. If free, you get a key instantly. 
# If full, you are added to the waitlist and will be emailed when ready!
client.join_queue()
```

### 3. Generating Text (Standard)
Once you have an active API key, you can ping the remote Ollama models.

```python
response = client.generate(
    prompt="Explain quantum computing in one sentence.",
    model="llama3",
    max_tokens=200,
    temperature=0.7
)

print(response)
```

### 4. Generating Text (Streaming)
Enable streaming to print chunks of text exactly as they are produced by the remote GPU.

```python
stream_generator = client.generate(
    prompt="Count from 1 to 10!",
    model="llama3",
    stream=True
)

if stream_generator:
    for chunk in stream_generator:
        print(chunk, end="", flush=True)
```

---

## 🛠️ Handling Server Downtime

If the gateway is ever offline, the SDK's `join_queue()` and `generate()` methods will automatically intercept the `ConnectError`, reach out to `Krypton Ping Server`, and instantly dispatch an alert to the server administrator. You'll simply see:

```text
[Krypton] Central GPU Server is offline! Notifying the owner to start it...
[Krypton] Owner notified. You will receive an email shortly once the server is online.
```

---

## 👨‍💻 Contributing

Have suggestions or want to host your own Krypton Hub? Visit the repository at [GitHub - saaj376/Krypton](https://github.com/saaj376/Krypton)

**License:** MIT
