#!/bin/bash
# Start Krypton Gateway & Ngrok in the background using tmux

# 1. Kill any existing krypton-session to restart fresh
tmux kill-session -t krypton-session 2>/dev/null

# 2. Start a new detached tmux session
tmux new-session -d -s krypton-session

# 3. Window 0 (Gateway)
tmux rename-window -t krypton-session:0 'Gateway'
tmux send-keys -t krypton-session:0 'cd /home/saajan/Downloads/Krypton && source venv/bin/activate && uvicorn v1_local.gateway:app --host 0.0.0.0 --port 8000' C-m

# 4. Window 1 (Ngrok tunnel)
tmux new-window -t krypton-session -n 'Tunnel'
tmux send-keys -t krypton-session:1 'ngrok http --domain=staminal-susann-inimitably.ngrok-free.dev 8000' C-m

echo "✅ Krypton Gateway & Ngrok Tunnel are now running in the background!"
echo "To view the logs, run:   tmux attach -t krypton-session"
echo "To stop the servers, run: tmux kill-session -t krypton-session"
