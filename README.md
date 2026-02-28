# Krypton AI Gateway

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black?logo=ollama)](https://ollama.com/)
[![PyPI](https://img.shields.io/badge/SDK-krypton--sdk-orange?logo=pypi)](https://pypi.org/project/krypton-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Turn any consumer GPU into a private, queue-managed, SaaS-grade AI cloud — for free.**

Krypton is a production-grade LLM gateway designed for local GPU hosting. It seamlessly turns any consumer-grade GPU (e.g. an RTX 3050 with 6 GB VRAM) into a robust, queue-managed private cloud. Developers connect through a polished Python SDK (`krypton-sdk`) that handles authentication, queuing, streaming, and offline wake-up calls automatically.

---

## Table of Contents

- [Why Krypton?](#why-krypton)
- [System Architecture](#system-architecture)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [1. Clone & Python environment](#1-clone--python-environment)
  - [2. Configure environment variables](#2-configure-environment-variables)
  - [3. Deploy the Cloud Sentinel (ping_server)](#3-deploy-the-cloud-sentinel-ping_server)
  - [4. Start the local gateway](#4-start-the-local-gateway)
- [API Reference](#api-reference)
- [Developer Guide — Using the SDK](#developer-guide--using-the-sdk)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Streaming responses](#streaming-responses)
  - [Reusing an existing API key](#reusing-an-existing-api-key)
- [v2 — Google Colab Variant](#v2--google-colab-variant)
- [Running Tests](#running-tests)
- [Contributing](#contributing)
- [License](#license)

---

## Why Krypton?

| Problem | Krypton's solution |
|---|---|
| Commercial LLM APIs are expensive | Run your own Ollama model on your GPU at zero cost |
| Uncontrolled GPU access causes crashes | Hard concurrency limit (semaphore) allows max **2 simultaneous users** |
| Managing user sessions is complex | Automatic 3-hour TTL keys + SQLite waitlist with email promotions |
| Developers crash when the server is off | Smart SDK detects offline state and pings the owner via cloud beacon |
| Sharing a local machine is insecure | UUID-based `kr_` prefixed API keys + header injection + expiry enforcement |

---

## System Architecture

Krypton is composed of three independent, loosely-coupled components:

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEVELOPER MACHINE                        │
│                                                                 │
│   krypton-sdk (pip install krypton-sdk)                         │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  KryptonClient                                           │  │
│   │  • join_queue()   → POST /join-queue                     │  │
│   │  • generate()     → POST /generate  (stream or batch)    │  │
│   │  • _notify_offline_server() → POST /request-access       │  │
│   └──────────────────────────────────────────────────────────┘  │
└──────────────────┬────────────────────────────┬─────────────────┘
                   │ Ngrok HTTPS tunnel          │ Fallback (offline)
                   ▼                             ▼
┌─────────────────────────────┐  ┌──────────────────────────────┐
│   v1_local/gateway.py       │  │  ping_server (Render cloud)  │
│   FastAPI + asyncio         │  │  FastAPI (always-on, free)   │
│                             │  │                              │
│  ┌─────────────────────┐    │  │  POST /request-access        │
│  │  GPU Semaphore (2)  │    │  │  → emails owner to wake up   │
│  └──────────────────────┘   │  └──────────────────────────────┘
│  ┌──────────────────────┐   │
│  │  SQLite (krypton.db) │   │
│  │  api_keys  table     │   │
│  │  waitlist  table     │   │
│  └──────────────────────┘   │
│                             │
│  ┌──────────────────────┐   │
│  │  Ollama (port 11434) │   │
│  └──────────────────────┘   │
└─────────────────────────────┘
```

### The three components

| # | Component | Location | Hosting | Role |
|---|---|---|---|---|
| 1 | **Cloud Sentinel** | `ping_server/` | Render (free tier, always-on) | Wakes the owner via Gmail when the local server is offline |
| 2 | **Local Enforcer** | `v1_local/gateway.py` | Your machine (Ngrok tunnel) | Enforces GPU limits, manages the SQLite queue, issues & expires API keys |
| 3 | **Smart Broker SDK** | `sdk_build/` / PyPI | Developer machines | Handles auth, queue, streaming, and offline fallback transparently |

---

## Directory Structure

```
Krypton/
├── ping_server/            # Cloud Sentinel — deploy to Render
│   ├── main.py             # FastAPI app: POST /request-access
│   └── requirements.txt
│
├── v1_local/               # Local Enforcer — run on your GPU machine
│   ├── gateway.py          # FastAPI gateway with queue, semaphore, Ollama proxy
│   └── sdk/                # In-repo copy of the KryptonClient SDK
│       └── __init__.py
│
├── v2_colab/               # Alternative gateway for Google Colab GPUs
│   ├── cloud_gateway.py
│   └── tunnel.py
│
├── shared/                 # Shared utilities used by the gateway
│   ├── database.py         # SQLite helpers: keys, waitlist, expiry
│   └── auth.py             # Key generation & verification helpers
│
├── sdk_build/              # PyPI-ready package source (krypton-sdk)
│
├── test/                   # Integration & unit tests
│   ├── test_gateway.py     # Tests all gateway HTTP endpoints
│   ├── test_sdk_online.py  # SDK end-to-end test (requires running gateway)
│   ├── test_sdk_offline.py # SDK offline fallback test
│   ├── test_email.py       # Email dispatch test
│   ├── test_email2.py
│   └── dbtest.py           # Direct database layer tests
│
├── krypton.db              # SQLite database (auto-created on first run)
├── start_krypton.sh        # One-command startup script (tmux + Ngrok)
├── USAGE.md                # End-user SDK guide
└── README.md               # This file
```

---

## Prerequisites

### Gateway Owner (running the server)

| Requirement | Notes |
|---|---|
| Python 3.10+ | Tested with 3.10 and 3.11 |
| [Ollama](https://ollama.com/) | Must be running on `localhost:11434` with a model pulled (e.g. `ollama pull llama3`) |
| [Ngrok](https://ngrok.com/) | Free account; used to expose the local gateway over HTTPS |
| [tmux](https://github.com/tmux/tmux) | Used by `start_krypton.sh` to manage background sessions |
| Gmail account + [App Password](https://support.google.com/accounts/answer/185833) | Used to send key/waitlist/expiry email notifications |
| [Render account](https://render.com/) | Free tier; used to deploy `ping_server` permanently |

### Developer (using the SDK)

| Requirement | Notes |
|---|---|
| Python 3.10+ | |
| A running Krypton Gateway URL | Provided by the gateway owner (e.g. an Ngrok link) |
| Your email address | Used to receive your API key |

---

## Installation & Setup

### 1. Clone & Python environment

```bash
git clone https://github.com/saaj376/Krypton.git
cd Krypton

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install fastapi uvicorn httpx pydantic pydantic-settings python-dotenv
```

### 2. Configure environment variables

Create a `.env` file in the project root (copy from `.env.example` if present):

```ini
# .env
SENDER_EMAIL=your.gmail@gmail.com
SENDER_APP_PASSWORD=xxxx xxxx xxxx xxxx   # Gmail App Password (16 characters)
OWNER_EMAIL=your.personal@email.com       # Where owner alerts are sent
```

> **How to get a Gmail App Password:**
> 1. Go to your Google Account → Security → 2-Step Verification (must be enabled).
> 2. Under "App passwords", create a new app password for "Mail".
> 3. Use the generated 16-character code as `SENDER_APP_PASSWORD`.

### 3. Deploy the Cloud Sentinel (`ping_server`)

The `ping_server` is a tiny FastAPI app that must be deployed to a free [Render](https://render.com/) web service so it is **always reachable**, even when your laptop is off.

1. Push this repo (or just the `ping_server/` folder) to GitHub.
2. In Render, create a new **Web Service** pointing to the `ping_server/` directory.
3. Set the same three environment variables (`SENDER_EMAIL`, `SENDER_APP_PASSWORD`, `OWNER_EMAIL`) in the Render dashboard.
4. Copy the public Render URL — the SDK is pre-configured to call `https://krypton-pl4h.onrender.com/request-access` (update `ping_server_url` in `v1_local/sdk/__init__.py` if you use your own deployment).

### 4. Start the local gateway

**Option A — one-command start (recommended):**

```bash
source start_krypton.sh
```

This uses `tmux` to launch two background windows:

| tmux window | Command |
|---|---|
| `Gateway` | `uvicorn v1_local.gateway:app --host 0.0.0.0 --port 8000` |
| `Tunnel` | `ngrok http --domain=<your-ngrok-domain> 8000` |

To view live logs:
```bash
tmux attach -t krypton-session
```

To stop everything:
```bash
tmux kill-session -t krypton-session
```

**Option B — manual start:**

```bash
# Terminal 1 — gateway
uvicorn v1_local.gateway:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Ngrok tunnel
ngrok http 8000
```

> Make sure `ollama serve` is running in a separate terminal before starting the gateway.

---

## API Reference

All endpoints are served by the local gateway (`v1_local/gateway.py`) on port **8000**.

### `GET /`

Health-check endpoint.

**Response**
```json
{ "message": "Krypton v1 Local Gateway Running" }
```

---

### `POST /join-queue`

Request an API key or join the waitlist.

**Request body**
```json
{ "user_email": "developer@example.com" }
```

**Responses**

| Scenario | HTTP | Body |
|---|---|---|
| Slot available (< 2 active keys) | `200` | `{ "status": "success", "api_key": "kr_...", "message": "API Key generated and emailed." }` |
| Server full (≥ 2 active keys) | `200` | `{ "status": "waitlist", "message": "Server at capacity. Added to waitlist." }` |

In both cases the user receives a confirmation email. When a slot opens, the next person on the waitlist is promoted automatically and emailed their key.

---

### `POST /generate`

Generate text via the local Ollama model. **Requires a valid API key** in the `X-API-Key` request header.

**Headers**
```
X-API-Key: kr_<your_api_key>
```

**Request body**
```json
{
  "prompt": "Explain quantum entanglement in one paragraph.",
  "model": "llama3",
  "max_tokens": 250,
  "temperature": 0.7,
  "stream": false
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `prompt` | `string` | required | The input text |
| `model` | `string` | `"llama3"` | Ollama model name |
| `max_tokens` | `int` | `100` | Maximum tokens to generate |
| `temperature` | `float` | `0.7` | Sampling temperature (0 = deterministic) |
| `stream` | `bool` | `false` | Enable NDJSON streaming |

**Non-streaming response (`stream: false`)**
```json
{
  "response": "Quantum entanglement is a phenomenon...",
  "ollama_raw": { ... }
}
```

**Streaming response (`stream: true`)**

Returns a chunked `application/x-ndjson` stream. Each line is a JSON object:
```json
{"response": "Quantum "}
{"response": "entanglement "}
...
```

**Error codes**

| Code | Meaning |
|---|---|
| `401` | Missing or expired `X-API-Key` |
| `502` | Ollama is not running on `localhost:11434` |
| `500` | Unexpected server error |

---

### `POST /request-access` *(ping_server only)*

Deployed on Render. Notifies the owner by email that a developer is waiting for the local server to come online.

**Request body**
```json
{ "user_email": "developer@example.com" }
```

**Response**
```json
{ "message": "Notification sent successfully" }
```

---

## Developer Guide — Using the SDK

### Installation

```bash
pip install krypton-sdk
```

### Quick Start

You need only two things from the gateway owner:
1. Their **Gateway URL** (e.g. `https://abc123.ngrok-free.app`)
2. Your **email address** (to receive your API key)

```python
from krypton_sdk import KryptonClient

# 1. Initialise the client
client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app"
)

# 2. Request an API key (or join the waitlist)
client.join_queue()

# 3. Generate text
response = client.generate(
    prompt="Explain quantum computing in one paragraph.",
    model="llama3",       # optional, default: llama3
    max_tokens=250,       # optional, default: 100
    temperature=0.7       # optional, default: 0.7
)

print(response)
```

**What `join_queue()` does:**

| Server state | SDK behaviour |
|---|---|
| Slot available | Instantly receives an API key (stored in `client.api_key`) and emails you a copy |
| Server full | Adds you to the SQLite waitlist; you are emailed when promoted |
| Server offline | Intercepts the connection error, calls the Render ping server to wake the owner, and prints a status message |

### Streaming responses

```python
stream = client.generate(
    prompt="Write a haiku about a GPU.",
    stream=True
)

print("AI: ", end="", flush=True)
for chunk in stream:
    print(chunk, end="", flush=True)
print()
```

### Reusing an existing API key

API keys are valid for **3 hours**. If you already have an unexpired key you can inject it directly — no need to call `join_queue()` again:

```python
client = KryptonClient(
    email="you@example.com",
    base_url="https://abc123.ngrok-free.app",
    api_key="kr_your_existing_key_here"
)

response = client.generate("Hello again!")
print(response)
```

If the key has expired, the server returns `401 Unauthorized`. Simply call `client.join_queue()` to obtain a fresh key.

---

## v2 — Google Colab Variant

The `v2_colab/` directory contains an experimental gateway designed to run on a **Google Colab** GPU (free T4) instead of a local machine.

| File | Purpose |
|---|---|
| `v2_colab/cloud_gateway.py` | FastAPI gateway adapted for the Colab environment |
| `v2_colab/tunnel.py` | Sets up a public tunnel from Colab (e.g. via `pyngrok`) |

> **Note:** The Colab session expires after a period of inactivity. The v1 local setup is preferred for long-running access.

---

## Running Tests

Tests live in the `test/` directory. Most require the local gateway and/or Ollama to be running.

```bash
# From the project root, with venv active:

# 1. Test the gateway HTTP endpoints directly
python test/test_gateway.py

# 2. End-to-end SDK test (gateway + Ollama must be running)
python test/test_sdk_online.py

# 3. Offline fallback test (gateway should be OFF)
python test/test_sdk_offline.py

# 4. Database layer sanity check
python test/dbtest.py

# 5. Email dispatch test
python test/test_email.py
```

---

## Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository and create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes and add/update tests as appropriate.
3. Ensure all relevant tests pass before opening a PR.
4. Open a pull request describing your changes.

Please follow the existing code style (PEP 8, type hints where used).

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Copyright © 2026 Saajan Varghese
