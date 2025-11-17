#!/bin/bash
#
# Run DIM test suite
# Usage: run-tests.sh [unit|integration|e2e|performance|security|all]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIM_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TEST_TYPE="${1:-all}"

cd "$DIM_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Running DIM test suite...${NC}"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found. Install with: pip install -r tests/requirements.txt${NC}"
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH="${DIM_ROOT}/orchestrator/src:${DIM_ROOT}/daemon/src:${PYTHONPATH}"

# Run tests based on type
case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running unit tests...${NC}"
        pytest tests/unit/ -m unit -v
        ;;
    integration)
        echo -e "${YELLOW}Running integration tests...${NC}"
        pytest tests/integration/ -m integration -v
        ;;
    e2e)
        echo -e "${YELLOW}Running end-to-end tests...${NC}"
        pytest tests/e2e/ -m e2e -v
        ;;
    performance)
        echo -e "${YELLOW}Running performance tests...${NC}"
        pytest tests/performance/ -m performance -v
        ;;
    security)
        echo -e "${YELLOW}Running security tests...${NC}"
        pytest tests/security/ -m security -v
        ;;
    all)
        echo -e "${YELLOW}Running all tests...${NC}"
        pytest tests/ -v --cov=powernode.dim --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}Coverage report: htmlcov/index.html${NC}"
        ;;
    *)
        echo -e "${RED}Error: Unknown test type: $TEST_TYPE${NC}"
        echo "Usage: $0 [unit|integration|e2e|performance|security|all]"
        exit 1
        ;;
esac

echo -e "${GREEN}Tests completed!${NC}"

