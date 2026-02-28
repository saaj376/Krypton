# Krypton AI Gateway

Krypton is a production-grade LLM gateway designed for local GPU hosting. It seamlessly turns any consumer-grade GPU (like an RTX 3050) into a robust, queue-managed private cloud using a custom async Python SDK.

It is the ultimate tool for unlimited, safe, and metered generative AI access!

---

## 🛠️ System Architecture

Krypton is uniquely designed into three "Smart" modular phases that gracefully protect your machine while maintaining a professional SaaS-like experience for your developers:

1. **The Cloud Sentinel (`ping_server`)**: A completely free, zero-maintenance Render cloud app that uses Google App Passwords to securely alert you whenever a developer requests API access while your machine is asleep.
2. **The Local Enforcer (`v1_local/gateway.py`)**: A fully self-managing queue system hosted locally. It actively monitors your GPU limit exactly 2 concurrent active users to prevent memory thrashing. It automatically deletes session keys after 3 hours and proactively emails the next waitlisted developer that their slot on the GPU is ready. 
3. **The Smart Broker SDK (`krypton_sdk v0.2.0`)**: A polished PyPI Python package for developers. It natively parses endpoints, injects API key headers, and boasts incredible offline fallback routing logic to wake you up without crashing their app.

---

## 🚀 How to use it?

If you are a developer looking to connect to a friend's Krypton server using the `krypton-sdk` Python package, **[please read the detailed USAGE.md guide here!](USAGE.md)**

If you are the **Gateway Owner** and want to run your own server:
1. Copy the `.env.example` to `.env` and fill in your Gmail App Password.
2. Deploy the `ping_server` folder to Render forever.
3. Run `source start_krypton.sh` when you're ready to share your GPU!
