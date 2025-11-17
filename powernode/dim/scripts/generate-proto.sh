#!/bin/bash
#
# Generate gRPC code from Protocol Buffer definitions
# Supports Python, TypeScript, and Go
#

set -e

PROTO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../proto" && pwd)"
OUTPUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Generating gRPC code from Protocol Buffers...${NC}"

# Check if protoc is installed
if ! command -v protoc &> /dev/null; then
    echo -e "${RED}Error: protoc not found. Please install Protocol Buffers compiler.${NC}"
    echo "  macOS: brew install protobuf"
    echo "  Linux: apt-get install protobuf-compiler"
    exit 1
fi

# Python generation
if command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Generating Python code...${NC}"
    
    # Check if grpc_tools is installed
    if python3 -c "import grpc_tools.protoc" 2>/dev/null; then
        PYTHON_OUT="${OUTPUT_DIR}/orchestrator/src/grpc_generated"
        mkdir -p "${PYTHON_OUT}"
        
        python3 -m grpc_tools.protoc \
            --python_out="${PYTHON_OUT}" \
            --grpc_python_out="${PYTHON_OUT}" \
            --proto_path="${PROTO_DIR}" \
            --proto_path="${PROTO_DIR}/.." \
            "${PROTO_DIR}/common.proto" \
            "${PROTO_DIR}/orchestrator.proto" \
            "${PROTO_DIR}/daemon.proto" \
            "${PROTO_DIR}/pattern_engine.proto"
        
        echo -e "${GREEN}Python code generated in ${PYTHON_OUT}${NC}"
    else
        echo -e "${YELLOW}Warning: grpc_tools not installed. Install with: pip install grpcio-tools${NC}"
    fi
else
    echo -e "${YELLOW}Python not found, skipping Python code generation${NC}"
fi

# TypeScript generation (if grpc-tools-node-protoc is available)
if command -v grpc_tools_node_protoc &> /dev/null; then
    echo -e "${YELLOW}Generating TypeScript code...${NC}"
    
    TS_OUT="${OUTPUT_DIR}/api-gateway/src/grpc_generated"
    mkdir -p "${TS_OUT}"
    
    grpc_tools_node_protoc \
        --js_out=import_style=commonjs:${TS_OUT} \
        --grpc_out=grpc_js:${TS_OUT} \
        --proto_path="${PROTO_DIR}" \
        --proto_path="${PROTO_DIR}/.." \
        "${PROTO_DIR}/common.proto" \
        "${PROTO_DIR}/orchestrator.proto" \
        "${PROTO_DIR}/daemon.proto" \
        "${PROTO_DIR}/pattern_engine.proto"
    
    echo -e "${GREEN}TypeScript code generated in ${TS_OUT}${NC}"
else
    echo -e "${YELLOW}grpc_tools_node_protoc not found, skipping TypeScript generation${NC}"
    echo "  Install with: npm install -g grpc-tools"
fi

# Go generation (if protoc-gen-go is available)
if command -v protoc-gen-go &> /dev/null && command -v protoc-gen-go-grpc &> /dev/null; then
    echo -e "${YELLOW}Generating Go code...${NC}"
    
    GO_OUT="${OUTPUT_DIR}/go_generated"
    mkdir -p "${GO_OUT}"
    
    protoc \
        --go_out="${GO_OUT}" \
        --go-grpc_out="${GO_OUT}" \
        --proto_path="${PROTO_DIR}" \
        --proto_path="${PROTO_DIR}/.." \
        "${PROTO_DIR}/common.proto" \
        "${PROTO_DIR}/orchestrator.proto" \
        "${PROTO_DIR}/daemon.proto" \
        "${PROTO_DIR}/pattern_engine.proto"
    
    echo -e "${GREEN}Go code generated in ${GO_OUT}${NC}"
else
    echo -e "${YELLOW}protoc-gen-go not found, skipping Go generation${NC}"
    echo "  Install with: go install google.golang.org/protobuf/cmd/protoc-gen-go@latest"
    echo "                go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest"
fi

echo -e "${GREEN}Protocol Buffer code generation complete!${NC}"

