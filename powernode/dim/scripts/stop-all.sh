#!/bin/bash
#
# Stop all DIM services
#

SESSION_NAME="dim-services"

# Kill tmux session
tmux kill-session -t "$SESSION_NAME" 2>/dev/null && echo "Stopped DIM services" || echo "No DIM services running"

# Also kill any processes by name (fallback)
pkill -f "dim.*orchestrator" 2>/dev/null || true
pkill -f "dim.*daemon" 2>/dev/null || true
pkill -f "dim.*pattern.*engine" 2>/dev/null || true
pkill -f "dim.*api-gateway" 2>/dev/null || true

echo "All DIM services stopped"

