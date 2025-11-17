# DIM gRPC Protocol Definitions

This directory contains Protocol Buffer definitions for all DIM gRPC services.

## Files

- **common.proto** - Shared messages and enums used across all services
- **orchestrator.proto** - Orchestrator service definitions
- **daemon.proto** - Daemon service definitions
- **pattern_engine.proto** - Pattern engine service definitions (Phase 2)

## Generating Code

### Python

```bash
# Install protoc compiler
brew install protobuf  # macOS
# or
apt-get install protobuf-compiler  # Linux

# Install Python gRPC tools
pip install grpcio grpcio-tools

# Generate Python code
python -m grpc_tools.protoc \
  --python_out=. \
  --grpc_python_out=. \
  --proto_path=. \
  orchestrator.proto daemon.proto common.proto pattern_engine.proto
```

### TypeScript/JavaScript

```bash
# Install protoc and plugins
npm install -g grpc-tools
npm install @grpc/proto-loader

# Generate TypeScript code (using grpc-tools)
grpc_tools_node_protoc \
  --plugin=protoc-gen-ts=./node_modules/.bin/protoc-gen-ts \
  --ts_out=./generated \
  --js_out=import_style=commonjs:./generated \
  --grpc_out=./generated \
  --proto_path=. \
  orchestrator.proto daemon.proto common.proto pattern_engine.proto
```

### Go

```bash
# Install protoc and Go plugins
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Generate Go code
protoc \
  --go_out=. \
  --go-grpc_out=. \
  --proto_path=. \
  orchestrator.proto daemon.proto common.proto pattern_engine.proto
```

## Service Overview

### Orchestrator Service

Main service for job submission and management:
- `SubmitJob` - Submit new inference job
- `GetJobStatus` - Get current job status
- `CancelJob` - Cancel running job
- `GetJobResult` - Get job result
- `ListJobs` - List active jobs (monitoring)

### Daemon Service

Service running on each PowerNode:
- `SubmitJob` - Submit job to daemon for execution
- `GetJobStatus` - Get job status on this daemon
- `CancelJob` - Cancel job on this daemon
- `GetHealth` - Get daemon health and resources
- `GetStats` - Get daemon statistics

### Pattern Engine Service (Phase 2)

Optional service for pattern engines (currently use HTTP):
- `Execute` - Execute pattern inference
- `GetHealth` - Get engine health

## Usage

### Python Example

```python
import grpc
from dim.proto import orchestrator_pb2, orchestrator_pb2_grpc

# Create channel
channel = grpc.insecure_channel('localhost:50051')

# Create stub
stub = orchestrator_pb2_grpc.OrchestratorStub(channel)

# Submit job
request = orchestrator_pb2.SubmitJobRequest(
    user_id='user-123',
    pattern=orchestrator_pb2.PATTERN_COLLABORATIVE,
    config_json='{"model_id": "model-abc", "nodes": ["node-001"]}',
    priority=orchestrator_pb2.PRIORITY_NORMAL
)

response = stub.SubmitJob(request)
print(f"Job ID: {response.job_id}")
```

### TypeScript Example

```typescript
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import { OrchestratorClient } from './generated/orchestrator_grpc_pb';

// Load proto
const packageDefinition = protoLoader.loadSync('orchestrator.proto', {
  includeDirs: ['./proto']
});

// Create client
const client = new OrchestratorClient(
  'localhost:50051',
  grpc.credentials.createInsecure()
);

// Submit job
const request = {
  userId: 'user-123',
  pattern: 'PATTERN_COLLABORATIVE',
  configJson: JSON.stringify({ modelId: 'model-abc', nodes: ['node-001'] }),
  priority: 'PRIORITY_NORMAL'
};

client.submitJob(request, (error, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log(`Job ID: ${response.jobId}`);
  }
});
```

## Notes

- All timestamps use ISO 8601 format strings
- JSON fields are used for flexible configuration (pattern-specific)
- Error handling uses the common Error message
- Services are designed for async/streaming (Phase 2)

