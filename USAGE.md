# 🚀 Krypton SDK — Developer Guide

The `krypton-sdk` is the official Python client library for the **Krypton AI Gateway**. It gives you a clean, high-level interface to a privately hosted LLM (powered by [Ollama](https://ollama.com/)) running on someone else's GPU. The SDK handles API key negotiation, request queuing, token streaming, and automatic offline fallback transparently so you can focus on building.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [KryptonClient API Reference](#kryptonclient-api-reference)
  - [Constructor](#constructor)
  - [join\_queue()](#join_queue)
  - [generate()](#generate)
- [Streaming Responses](#streaming-responses)
- [Reusing an Existing API Key](#reusing-an-existing-api-key)
- [Error Handling](#error-handling)
- [Offline Fallback Mechanism](#offline-fallback-mechanism)
- [Practical Examples](#practical-examples)
  - [Simple Question & Answer](#simple-question--answer)
  - [Streaming Chat Loop](#streaming-chat-loop)
  - [Batch Processing](#batch-processing)
  - [Persisting Your API Key Between Sessions](#persisting-your-api-key-between-sessions)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before using the SDK you need two things from the **Krypton Gateway owner**:

| What you need | Where to get it |
|---|---|
| **Gateway URL** | Provided by the owner — typically an Ngrok HTTPS link, e.g. `https://abc123.ngrok-free.app` |
| **Your email address** | Your own inbox — the gateway emails your API key and waitlist notifications here |

You do **not** need to install Ollama, run a server, or manage any infrastructure. That is entirely the owner's responsibility.

---

## Installation

Install the SDK from PyPI using pip:

```bash
pip install krypton-sdk
```

The SDK's only runtime dependency is [`httpx`](https://www.python-httpx.org/) (≥ 0.28.0), which is installed automatically.

**Python version requirement:** Python 3.7 or later.

---

## Quick Start

```python
from krypton_sdk import KryptonClient

# 1. Create a client with your email and the gateway URL
client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app"
)

# 2. Request an API key (or join the waitlist if the server is full)
client.join_queue()

# 3. Generate text once you have a key
response = client.generate(
    prompt="Explain quantum computing in one paragraph.",
    model="llama3",
    max_tokens=250,
    temperature=0.7
)

print(response)
```

That is the complete workflow for the majority of use-cases. The sections below explain every option in detail.

---

## KryptonClient API Reference

### Constructor

```python
KryptonClient(email: str, base_url: str, api_key: str = None)
```

Creates and configures a new SDK client instance.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `email` | `str` | ✅ | Your email address. Used to receive your API key and waitlist notifications. |
| `base_url` | `str` | ✅ | Full HTTPS URL of the Krypton Gateway (no trailing slash). Example: `"https://abc123.ngrok-free.app"` |
| `api_key` | `str` | ❌ | An existing, unexpired API key (`kr_...`). If provided, you can skip `join_queue()` and call `generate()` immediately. Defaults to `None`. |

**Raises:** `ValueError` if either `email` or `base_url` is empty or `None`.

**Example:**

```python
# Standard initialisation — no key yet
client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app"
)

# Initialisation with a pre-existing key
client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app",
    api_key="kr_AbCdEfGhIjKlMnOpQrStUvWxYz123456"
)
```

---

### join_queue()

```python
client.join_queue() -> None
```

Requests an API key from the gateway. Depending on the gateway's current load one of three outcomes occurs:

| Gateway state | What happens |
|---|---|
| **Slot available** (fewer than 2 active keys) | An API key is generated immediately. It is stored in `client.api_key` and a copy is emailed to you. |
| **Server full** (2 active keys already in use) | You are added to the SQLite waitlist. When an existing key expires or is freed, the gateway automatically promotes the oldest waitlisted user and emails them a fresh key. |
| **Server offline** | The SDK catches the connection error, silently contacts the always-on Render Cloud Ping Server, and asks it to email the gateway owner. You will be notified once the server is back online. |

**After a successful call** `client.api_key` is populated and you can proceed to call `generate()`.

**Example:**

```python
client.join_queue()

if client.api_key:
    print(f"Ready! Key: {client.api_key}")
else:
    print("Added to waitlist — check your email for a key when a slot opens.")
```

> **Note:** API keys are valid for exactly **3 hours** from the moment of creation. After expiry the key is automatically invalidated by the gateway.

---

### generate()

```python
client.generate(
    prompt: str,
    model: str = "llama3",
    max_tokens: int = 100,
    temperature: float = 0.7,
    stream: bool = False
) -> str | Generator[str, None, None] | None
```

Sends a prompt to the Ollama model running on the gateway and returns the response.

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `prompt` | `str` | required | The input text to send to the model. |
| `model` | `str` | `"llama3"` | The Ollama model to use. Must be a model that the gateway owner has already pulled (e.g. `"llama3"`, `"mistral"`, `"phi3"`). |
| `max_tokens` | `int` | `100` | Maximum number of tokens the model is allowed to generate. Increase this for longer outputs. |
| `temperature` | `float` | `0.7` | Controls randomness. `0.0` = fully deterministic, `1.0` = very creative. Values between `0.2` and `0.8` work well for most tasks. |
| `stream` | `bool` | `False` | When `True`, returns a generator that yields text chunks as they are produced (token-by-token streaming). When `False`, waits for the full response and returns it as a single string. |

#### Return values

| `stream` value | Return type | Description |
|---|---|---|
| `False` | `str` | The full generated text as a single string. Returns `""` if the model produced no output. |
| `True` | `Generator[str, None, None]` | A lazy generator. Each `yield` produces a small text chunk (usually a word or a few tokens). Iterate with a `for` loop. |
| Either | `None` | Returned when `client.api_key` is not set, or when the gateway is offline and the fallback has been triggered. |

#### Exceptions

| Exception | When raised |
|---|---|
| `Exception("Krypton Server returned an error: 5xx - ...")` | The gateway returned an HTTP 5xx error (e.g. Ollama is not running). |
| `Exception("Failed to connect to Krypton Server at <url>: ...")` | A network-level error other than a clean connection refusal occurred. |

A `401 Unauthorized` response is handled silently: the SDK prints `[Krypton] API Key is Invalid or Expired.` and returns `None` (non-streaming) or yields nothing (streaming) without raising an exception.

**Example — non-streaming:**

```python
answer = client.generate(
    prompt="What is the boiling point of water in Celsius?",
    model="llama3",
    max_tokens=50,
    temperature=0.0    # deterministic answer
)
print(answer)
```

**Example — streaming:**

```python
stream = client.generate(
    prompt="Tell me a short story about a robot.",
    model="llama3",
    max_tokens=300,
    stream=True
)

for chunk in stream:
    print(chunk, end="", flush=True)
print()  # newline after stream ends
```

---

## Streaming Responses

When you pass `stream=True` to `generate()`, the SDK opens a persistent HTTP connection and yields each text chunk as it arrives from the model. This produces a **ChatGPT-like typewriter effect** in the terminal or UI.

```python
stream = client.generate(
    prompt="Describe the history of the internet in detail.",
    model="llama3",
    max_tokens=500,
    stream=True
)

print("AI: ", end="", flush=True)
for chunk in stream:
    print(chunk, end="", flush=True)
print()
```

**Important behaviours to know:**

- The generator is **lazy**: the HTTP request is not made until you start iterating.
- The generator is **single-use**: you cannot re-iterate after it is exhausted.
- If the key expires mid-stream, the SDK prints an expiry warning and the generator stops cleanly.
- The connection timeout for streaming requests is **120 seconds** of inactivity. Long generations keep the connection alive by sending data, so this limit is rarely reached.

---

## Reusing an Existing API Key

API keys are valid for **3 hours**. If you have an unexpired key from a previous session (e.g. copied from your email or stored in a `.env` file) you can inject it at construction time and skip `join_queue()` entirely:

```python
import os
from krypton_sdk import KryptonClient

client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app",
    api_key=os.getenv("KRYPTON_API_KEY")    # load from environment variable
)

# No join_queue() needed — generate immediately
response = client.generate("Summarise the latest news in two sentences.")
print(response)
```

If the injected key has already expired the gateway returns `401 Unauthorized`. The SDK prints a warning and `generate()` returns `None`. To recover, simply call `client.join_queue()` to obtain a fresh key:

```python
response = client.generate("Hello!")
if response is None:
    print("Key expired — requesting a new one...")
    client.join_queue()
    response = client.generate("Hello!")
    print(response)
```

---

## Error Handling

The table below lists every significant error condition and the recommended action.

| Condition | SDK behaviour | What to do |
|---|---|---|
| `email` or `base_url` is empty | Raises `ValueError` immediately | Provide both values in the constructor. |
| `generate()` called without a key | Prints a warning, returns `None` | Call `client.join_queue()` first, or pass `api_key` to the constructor. |
| Gateway offline during `join_queue()` | Prints offline message, pings the Render server | Wait for the owner's wake-up email, then call `join_queue()` again. |
| Gateway offline during `generate()` | Prints offline message, returns `None` | Same as above. |
| `401 Unauthorized` (expired or invalid key) | Prints expiry warning, returns `None` | Call `client.join_queue()` to get a new key. |
| `502 Bad Gateway` from the gateway | Raises `Exception` with status and body | The gateway is running but Ollama is not. Ask the owner to start Ollama. |
| `5xx` server error | Raises `Exception` with status and body | Retry later or contact the gateway owner. |
| Non-connection `httpx.RequestError` | Raises `Exception` with message | Check your internet connection and the `base_url`. |

**Minimal defensive wrapper example:**

```python
from krypton_sdk import KryptonClient

client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app"
)

client.join_queue()

if client.api_key:
    try:
        response = client.generate("What is 2 + 2?", max_tokens=20)
        if response is not None:
            print(response)
        else:
            print("No response received — key may have expired.")
    except Exception as e:
        print(f"Generation failed: {e}")
```

---

## Offline Fallback Mechanism

The Krypton SDK includes a built-in "smart broker" that prevents your application from crashing when the gateway owner's machine is turned off.

**How it works:**

1. When `join_queue()` or `generate()` attempts an HTTP request and receives a `httpx.ConnectError` (connection refused), the SDK does **not** raise an exception.
2. Instead, it calls the internal `_notify_offline_server()` method, which POSTs `{"user_email": "<your-email>"}` to the always-on **Render Cloud Ping Server** at `https://krypton-pl4h.onrender.com/request-access`.
3. The Ping Server sends an alert email to the gateway owner.
4. The SDK prints a status message to the console and returns gracefully.

**Console output you will see:**

```
[Krypton] Central GPU Server is offline! Notifying the owner to start it...
[Krypton] Owner notified. You will receive an email shortly once the server is online.
```

Once the owner restarts the gateway, call `client.join_queue()` again to obtain your key.

> **Note:** The fallback only triggers on a clean `ConnectError` (i.e. the host is unreachable). It does not trigger for HTTP errors like `401`, `502`, or `500` — those mean the gateway *is* running and returned an error.

---

## Practical Examples

### Simple Question & Answer

```python
from krypton_sdk import KryptonClient

client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app"
)

client.join_queue()

if client.api_key:
    questions = [
        "What is the speed of light?",
        "Who wrote Romeo and Juliet?",
        "What is the largest planet in the solar system?",
    ]
    for question in questions:
        answer = client.generate(prompt=question, max_tokens=60, temperature=0.0)
        print(f"Q: {question}")
        print(f"A: {answer}\n")
```

---

### Streaming Chat Loop

Build a simple interactive terminal chatbot that streams each response as it is generated:

```python
from krypton_sdk import KryptonClient

client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app"
)

client.join_queue()

if not client.api_key:
    print("Could not obtain an API key. Exiting.")
    exit(1)

print("Krypton Chat — type 'quit' to exit.\n")
while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ("quit", "exit", "q"):
        break
    if not user_input:
        continue

    print("AI: ", end="", flush=True)
    try:
        stream = client.generate(
            prompt=user_input,
            model="llama3",
            max_tokens=300,
            temperature=0.7,
            stream=True
        )
        if stream:
            for chunk in stream:
                print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"\n[Error] {e}")
```

---

### Batch Processing

Process a list of prompts and collect the results:

```python
from krypton_sdk import KryptonClient

client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app"
)

client.join_queue()

prompts = [
    "Summarise machine learning in one sentence.",
    "Summarise deep learning in one sentence.",
    "Summarise reinforcement learning in one sentence.",
]

results = []
if client.api_key:
    for prompt in prompts:
        try:
            response = client.generate(
                prompt=prompt,
                model="llama3",
                max_tokens=80,
                temperature=0.3
            )
            results.append({"prompt": prompt, "response": response})
        except Exception as e:
            results.append({"prompt": prompt, "response": f"Error: {e}"})

for item in results:
    print(f"Prompt : {item['prompt']}")
    print(f"Response: {item['response']}\n")
```

---

### Persisting Your API Key Between Sessions

Save your API key to an environment variable or a local file so you do not have to re-join the queue every time you run your script (as long as the 3-hour window has not elapsed):

```python
import os
from krypton_sdk import KryptonClient

GATEWAY_URL = "https://abc123.ngrok-free.app"
EMAIL = "you@example.com"
SAVED_KEY = os.getenv("KRYPTON_API_KEY")   # export KRYPTON_API_KEY=kr_...

client = KryptonClient(
    email=EMAIL,
    base_url=GATEWAY_URL,
    api_key=SAVED_KEY  # None if env var is not set
)

if not client.api_key:
    client.join_queue()

# Generate once we definitely have a key
if client.api_key:
    # Optionally persist the key for future runs
    print(f"export KRYPTON_API_KEY={client.api_key}")

    response = client.generate(
        prompt="Give me a motivational quote.",
        max_tokens=60
    )
    print(response)
```

---

## Troubleshooting

### "You must provide both an email and a base_url."

You passed an empty string or `None` for `email` or `base_url` when creating the client. Both are required.

---

### `join_queue()` prints the offline message immediately

The SDK cannot reach the gateway at the provided `base_url`. Possible causes:
- The `base_url` is wrong or the Ngrok tunnel has changed (Ngrok free-tier URLs change on each restart).
- The gateway owner has not started the server.
- Your own internet connection is down.

Ask the gateway owner to confirm the current active URL and restart if needed.

---

### `generate()` returns `None` without an error message

This happens when:
1. `client.api_key` is `None` — call `join_queue()` first.
2. The API key has expired (`401` response) — call `join_queue()` to get a fresh key.
3. The gateway went offline mid-session — the offline fallback triggered and `None` was returned.

---

### `generate()` raises "Krypton Server returned an error: 502"

The gateway is reachable but Ollama is not running on the owner's machine. The gateway owner needs to start Ollama (`ollama serve`) and ensure their model is pulled (`ollama pull llama3`).

---

### Streaming stops mid-response

This can happen if:
- The 120-second idle timeout was reached (very rare for streaming responses).
- The API key expired while the stream was in progress.
- The gateway or Ollama crashed on the server side.

Re-initialise the client, call `join_queue()`, and retry.

---

### I was added to the waitlist — how long do I wait?

Each API key has a 3-hour TTL. When an active key expires (or if a user's session ends early), the gateway automatically promotes the first person on the waitlist and emails them a key. There is no way to skip the queue — the waitlist is strictly FIFO.

---

### The key in my email does not match `client.api_key`

This should not happen. If it does, use the key from your email — it is the authoritative copy stored in the gateway's database. Re-create the client with `api_key=<key from email>` to use it directly.
