#!/bin/bash
#
# Setup test environment for DIM
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIM_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "Setting up DIM test environment..."

# Create test directories
mkdir -p /tmp/dim-test-models
mkdir -p /tmp/dim-test-data
mkdir -p /tmp/dim-test-logs

# Install test dependencies
cd "$DIM_ROOT"
pip install -r tests/requirements.txt

echo "Test environment setup complete!"

