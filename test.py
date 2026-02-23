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