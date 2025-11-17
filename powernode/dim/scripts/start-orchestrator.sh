#!/bin/bash
#
# Start DIM Orchestrator
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIM_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${DIM_ROOT}/orchestrator"

# Activate virtual environment
if [ -d venv ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Run setup-dev.sh first."
    exit 1
fi

# Set environment variables
export PYTHONPATH="${DIM_ROOT}/orchestrator/src:${PYTHONPATH}"
export DIM_IPFS_API="${DIM_IPFS_API:-/ip4/127.0.0.1/tcp/5001}"
export DIM_GRPC_ADDRESS="${DIM_GRPC_ADDRESS:-localhost:50051}"

# Start orchestrator
echo "Starting DIM Orchestrator..."
python main.py

