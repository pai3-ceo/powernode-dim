#!/bin/bash
#
# Start DIM API Gateway
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIM_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${DIM_ROOT}/api-gateway"

# Check if node_modules exists
if [ ! -d node_modules ]; then
    echo "Installing dependencies..."
    npm install
fi

# Set environment variables
export PORT="${PORT:-3000}"
export HOST="${HOST:-0.0.0.0}"
export ORCHESTRATOR_ADDRESS="${ORCHESTRATOR_ADDRESS:-localhost:50051}"
export LOG_LEVEL="${LOG_LEVEL:-info}"

# Start API Gateway
echo "Starting DIM API Gateway on port ${PORT}..."
if [ "$1" == "dev" ]; then
    npm run dev
else
    npm run build
    npm start
fi

