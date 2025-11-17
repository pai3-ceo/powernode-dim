# DIM API Gateway

Node.js/TypeScript REST API and WebSocket server for DIM (Decentralized Inference Machine).

## Features

- **REST API** - Fastify-based REST endpoints for job submission and status
- **WebSocket** - Real-time job updates
- **Request Validation** - Zod schema validation
- **gRPC Client** - Communication with Python orchestrator (Phase 2)

## Installation

```bash
npm install
```

## Development

```bash
# Run in development mode (with tsx)
npm run dev

# Build TypeScript
npm run build

# Run production build
npm start
```

## API Endpoints

### Submit Job
```
POST /api/inference/submit
Content-Type: application/json

{
  "pattern": "collaborative",
  "config": {
    "modelId": "model-abc123",
    "nodes": ["node-001", "node-002"],
    "aggregation": {
      "method": "federated_averaging"
    }
  },
  "priority": "normal",
  "maxCost": 5000
}
```

### Get Job Status
```
GET /api/inference/status/:jobId
```

### Get Job Result
```
GET /api/inference/result/:jobId
```

### Cancel Job
```
DELETE /api/inference/job/:jobId
```

### Health Check
```
GET /health
GET /health/ready
```

## WebSocket

Connect to `/ws/jobs/:jobId` for real-time job updates.

## Configuration

Set environment variables:
- `PORT` - Server port (default: 3000)
- `HOST` - Server host (default: 0.0.0.0)
- `ORCHESTRATOR_ADDRESS` - Orchestrator gRPC address (default: localhost:50051)
- `LOG_LEVEL` - Log level (default: info)

## Phase 1 vs Phase 2

**Phase 1 (Current):**
- HTTP communication with orchestrator (placeholder)
- Mock job responses
- Basic WebSocket implementation

**Phase 2 (Planned):**
- Full gRPC client implementation
- IPFS Pubsub integration for WebSocket
- PAIneer authentication
- Real orchestrator communication

