#!/bin/bash
#
# Start DIM Pattern Engine
# Usage: start-pattern-engine.sh [collaborative|comparative|chained]
#

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 [collaborative|comparative|chained]"
    exit 1
fi

ENGINE=$1

if [[ ! "$ENGINE" =~ ^(collaborative|comparative|chained)$ ]]; then
    echo "Error: Invalid engine. Must be one of: collaborative, comparative, chained"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIM_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${DIM_ROOT}/pattern_engines/${ENGINE}"

# Activate virtual environment
if [ -d venv ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Run setup-dev.sh first."
    exit 1
fi

# Set environment variables
export PYTHONPATH="${DIM_ROOT}/pattern_engines/${ENGINE}:${PYTHONPATH}"
export DIM_IPFS_API="${DIM_IPFS_API:-/ip4/127.0.0.1/tcp/5001}"

# Determine port
case $ENGINE in
    collaborative)
        PORT=8001
        ;;
    comparative)
        PORT=8002
        ;;
    chained)
        PORT=8003
        ;;
esac

# Start engine
echo "Starting DIM ${ENGINE} pattern engine on port ${PORT}..."
python main.py

