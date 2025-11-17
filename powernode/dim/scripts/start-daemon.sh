#!/bin/bash
#
# Start DIM Daemon
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIM_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${DIM_ROOT}/daemon"

# Activate virtual environment
if [ -d venv ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Run setup-dev.sh first."
    exit 1
fi

# Set environment variables
export PYTHONPATH="${DIM_ROOT}/daemon/src:${PYTHONPATH}"
export NODE_ID="${NODE_ID:-node-001}"
export DIM_IPFS_API="${DIM_IPFS_API:-/ip4/127.0.0.1/tcp/5001}"

# Start daemon
echo "Starting DIM Daemon for node ${NODE_ID}..."
python main.py

