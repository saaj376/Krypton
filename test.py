from krypton_sdk import KryptonClient

# 1. Connect to the remote server over the internet
client = KryptonClient(base_url="https://staminal-susann-inimitably.ngrok-free.dev")

# 2. Generate text! The heavy lifting happens remotely.
print("Answer: ", end="", flush=True)

# Set stream=True to receive chunks in real time
for chunk in client.generate(
    prompt="what is a donkey",
    model="llama3",
    max_tokens=200,
    stream=True
):
    print(chunk, end="", flush=True)
print()