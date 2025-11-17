#!/bin/bash
#
# DIM Development Environment Setup
# Sets up local development environment for DIM module
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIM_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Setting up DIM development environment..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3.11+ required${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc -l) -eq 0 ]]; then
    echo -e "${RED}Error: Python 3.11+ required, found ${PYTHON_VERSION}${NC}"
    exit 1
fi

echo -e "${GREEN}Python ${PYTHON_VERSION} found${NC}"

# Check Node.js version
echo -e "${YELLOW}Checking Node.js version...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js 20+ required${NC}"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [[ $NODE_VERSION -lt 20 ]]; then
    echo -e "${RED}Error: Node.js 20+ required, found v${NODE_VERSION}${NC}"
    exit 1
fi

echo -e "${GREEN}Node.js $(node --version) found${NC}"

# Check IPFS
echo -e "${YELLOW}Checking IPFS...${NC}"
if ! command -v ipfs &> /dev/null; then
    echo -e "${YELLOW}IPFS not found. Installing...${NC}"
    brew install ipfs || {
        echo -e "${RED}Failed to install IPFS. Please install manually.${NC}"
        exit 1
    }
fi

echo -e "${GREEN}IPFS $(ipfs version --number) found${NC}"

# Initialize IPFS if needed
if [ ! -d ~/.ipfs ]; then
    echo -e "${YELLOW}Initializing IPFS...${NC}"
    ipfs init
fi

# Setup Python virtual environments
echo -e "${YELLOW}Setting up Python environments...${NC}"

# Orchestrator
cd "${DIM_ROOT}/orchestrator"
if [ ! -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Pattern Engines
for engine in collaborative comparative chained; do
    cd "${DIM_ROOT}/pattern_engines/${engine}"
    if [ ! -d venv ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
done

# Daemon
cd "${DIM_ROOT}/daemon"
if [ ! -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Agents
cd "${DIM_ROOT}/agents"
if [ ! -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Setup Node.js API Gateway
echo -e "${YELLOW}Setting up API Gateway...${NC}"
cd "${DIM_ROOT}/api-gateway"
if [ ! -d node_modules ]; then
    npm install
fi

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p /var/lib/dim/models
mkdir -p /var/log/dim
mkdir -p "${DIM_ROOT}/data/ipfs"

# Generate gRPC code (if protoc available)
if command -v protoc &> /dev/null; then
    echo -e "${YELLOW}Generating gRPC code...${NC}"
    "${DIM_ROOT}/scripts/generate-proto.sh" || echo -e "${YELLOW}Warning: gRPC code generation failed (optional)${NC}"
else
    echo -e "${YELLOW}protoc not found, skipping gRPC code generation${NC}"
fi

echo -e "${GREEN}DIM development environment setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start IPFS daemon: ipfs daemon"
echo "2. Start orchestrator: cd orchestrator && source venv/bin/activate && python main.py"
echo "3. Start pattern engines: cd pattern_engines/collaborative && source venv/bin/activate && python main.py"
echo "4. Start daemon: cd daemon && source venv/bin/activate && python main.py"
echo "5. Start API Gateway: cd api-gateway && npm run dev"

