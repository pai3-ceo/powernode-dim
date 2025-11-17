#!/bin/bash
#
# Start all DIM services (for development)
# Uses tmux to run services in separate panes
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIM_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux not found. Install with: brew install tmux"
    exit 1
fi

# Create tmux session
SESSION_NAME="dim-services"

# Kill existing session if it exists
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

# Create new session
tmux new-session -d -s "$SESSION_NAME" -n "orchestrator"

# Split window into panes
tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v
tmux select-pane -t 2
tmux split-window -v

# Start services in each pane
tmux send-keys -t "$SESSION_NAME:0.0" "cd ${DIM_ROOT} && ${DIM_ROOT}/scripts/start-orchestrator.sh" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "cd ${DIM_ROOT} && ${DIM_ROOT}/scripts/start-pattern-engine.sh collaborative" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "cd ${DIM_ROOT} && ${DIM_ROOT}/scripts/start-pattern-engine.sh comparative" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "cd ${DIM_ROOT} && ${DIM_ROOT}/scripts/start-pattern-engine.sh chained" C-m
tmux send-keys -t "$SESSION_NAME:0.4" "cd ${DIM_ROOT} && ${DIM_ROOT}/scripts/start-daemon.sh" C-m

# Create new window for API Gateway
tmux new-window -t "$SESSION_NAME" -n "api-gateway"
tmux send-keys -t "$SESSION_NAME:api-gateway" "cd ${DIM_ROOT} && ${DIM_ROOT}/scripts/start-api-gateway.sh dev" C-m

# Select first pane
tmux select-window -t "$SESSION_NAME:orchestrator"
tmux select-pane -t 0

echo "DIM services started in tmux session: $SESSION_NAME"
echo "Attach with: tmux attach -t $SESSION_NAME"
echo "Detach with: Ctrl+B, then D"
echo "Kill session with: tmux kill-session -t $SESSION_NAME"

