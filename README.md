# DIM (Decentralized Inference Machine) Module

**Version:** 1.0.0  
**Status:** Phase 1 - Foundation Implementation

## Overview

DIM (Decentralized Inference Machine) is the "EVM for AI" - a standalone orchestration layer that executes AI inference across distributed PowerNodes while maintaining data custody, privacy, and accountability.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Node.js/TypeScript API Gateway              │
│              (Fastify REST API + WebSocket)              │
└────────────────────────┬──────────────────────────────────┘
                         │ gRPC
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Python DIM Orchestrator                    │
│  • Pattern routing logic                                │
│  • IPFS state management                                 │
│  • Node selection & load balancing                      │
│  • Job lifecycle management                             │
└────┬────────────┬────────────┬───────────────────────────┘
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│Collab   │  │Compar   │  │Chained  │
│Engine   │  │Engine   │  │Engine   │
│:8001    │  │:8002    │  │:8003    │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┴────────────┘
                  │ gRPC
                  ▼
┌─────────────────────────────────────────────────────────┐
│              DIM Daemon (on each PowerNode)             │
│  • gRPC Server (receives jobs)                          │
│  • Job Queue & Scheduler                                 │
│  • Resource Manager (CPU, Memory, GPU)                  │
│  • Model Cache Manager (50GB local cache)               │
│  • Agent Process Manager                                 │
└─────────────────────────────────────────────────────────┘
```

## Three Inference Patterns

### 1. Collaborative
**Same model on different data sets (data parallel)**

Use case: Drug discovery across multiple hospitals

- Distributes the same model to multiple nodes
- Each node processes its own data
- Results are aggregated (federated averaging, weighted average, etc.)

### 2. Comparative
**Different models on same data set (model parallel)**

Use case: Multiple diagnostic models on patient data

- Runs multiple models on the same data
- Builds consensus from model outputs
- Supports majority vote, weighted vote, expert review

### 3. Chained
**Sequential pipeline of models (workflow)**

Use case: Triage → Diagnosis → Treatment → Medication review

- Executes models in sequence
- Passes output of step N to step N+1
- Handles failures and rollback

## Project Structure

```
powernode/dim/
├── orchestrator/              # Python DIM Orchestrator
│   ├── src/
│   │   ├── orchestrator.py    # Main orchestrator class
│   │   ├── pattern_router.py  # Routes to pattern engines
│   │   ├── node_selector.py   # Node selection logic
│   │   ├── ipfs/              # IPFS integration
│   │   ├── models/            # Data models
│   │   └── utils/             # Utilities
│   ├── main.py                # Entry point
│   └── requirements.txt
│
├── pattern_engines/           # Three Pattern Engine Microservices
│   ├── base/                  # Abstract base class
│   ├── collaborative/         # Collaborative engine
│   ├── comparative/           # Comparative engine
│   └── chained/               # Chained engine
│
├── daemon/                    # DIM Daemon (runs on each PowerNode)
│   ├── src/
│   │   ├── daemon.py          # Main daemon class
│   │   ├── job_queue.py       # Job scheduling
│   │   ├── resource_manager.py # Resource management
│   │   ├── model_cache.py     # Model caching
│   │   └── agent_manager.py   # Agent process management
│   └── requirements.txt
│
├── agents/                    # Agent Execution (separate processes)
│   ├── src/
│   │   ├── inference_engine.py # Model loading & inference
│   │   └── loaders/            # Model loaders (MLX, CoreML, PyTorch, ONNX)
│   └── requirements.txt
│
├── proto/                     # gRPC Protocol Buffers
│   ├── orchestrator.proto
│   ├── daemon.proto
│   └── common.proto
│
├── config/                    # Configuration files
│   ├── dev.yaml
│   └── prod.yaml
│
└── README.md                  # This file
```

## Installation

### Prerequisites

- **Python 3.11+** - For orchestrator, pattern engines, daemon, and agents
- **Node.js 20+** - For API Gateway
- **IPFS (go-ipfs 0.24+)** - For decentralized storage and coordination
- **Tailscale** - For private network (Phase 2)
- **Protocol Buffers compiler** - For gRPC code generation (optional)

### Automated Setup

```bash
# Run setup script (handles all dependencies)
cd powernode/dim
./scripts/setup-dev.sh
```

### Manual Setup

```bash
# 1. Setup orchestrator
cd powernode/dim/orchestrator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Setup pattern engines
cd ../pattern_engines/collaborative
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Repeat for comparative and chained

# 3. Setup daemon
cd ../../daemon
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Setup agents
cd ../agents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Setup API Gateway
cd ../api-gateway
npm install

# 6. Initialize IPFS
ipfs init
ipfs daemon &
```

## Usage

### Starting Services

#### Option 1: Start All Services (Recommended for Development)

```bash
# Start all services in tmux session
./scripts/start-all.sh

# Attach to session
tmux attach -t dim-services
```

#### Option 2: Start Services Individually

```bash
# Terminal 1: Orchestrator
./scripts/start-orchestrator.sh

# Terminal 2: Collaborative Pattern Engine
./scripts/start-pattern-engine.sh collaborative

# Terminal 3: Comparative Pattern Engine
./scripts/start-pattern-engine.sh comparative

# Terminal 4: Chained Pattern Engine
./scripts/start-pattern-engine.sh chained

# Terminal 5: Daemon
export NODE_ID=node-001
./scripts/start-daemon.sh

# Terminal 6: API Gateway
./scripts/start-api-gateway.sh dev
```

### Submitting Jobs

#### Via REST API (API Gateway)

```bash
# Submit collaborative job
curl -X POST http://localhost:3000/api/inference/submit \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "collaborative",
    "config": {
      "modelId": "model-abc123",
      "nodes": ["node-001", "node-002"],
      "aggregation": {"method": "federated_averaging"}
    },
    "priority": "normal"
  }'

# Get job status
curl http://localhost:3000/api/inference/status/{jobId}

# Get job result
curl http://localhost:3000/api/inference/result/{jobId}
```

#### Via Python (Direct Orchestrator)

```python
import asyncio
from powernode.dim.orchestrator.src.orchestrator import DIMOrchestrator
from powernode.dim.orchestrator.src.models.job_spec import JobSpec, Pattern, CollaborativeConfig
from powernode.dim.orchestrator.src.utils.config import load_config

async def main():
    # Load config
    config = load_config()
    
    # Create orchestrator
    orchestrator = DIMOrchestrator(config)
    await orchestrator.start()
    
    # Submit collaborative job
    spec = JobSpec(
        pattern=Pattern.COLLABORATIVE,
        config=CollaborativeConfig(
            model_id="model-abc123",
            nodes=["node-001", "node-002"],
            aggregation={"method": "federated_averaging"}
        )
    )
    
    job_id = await orchestrator.submit_job(spec, user_id="user-123")
    print(f"Job submitted: {job_id}")
    
    # Check status
    status = await orchestrator.get_job_status(job_id)
    print(f"Job status: {status.state}")

asyncio.run(main())
```

### WebSocket Updates

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:3000/ws/jobs/{jobId}');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Job update:', update);
};
```

## Configuration

Configuration files are in `config/`:
- `dev.yaml` - Development configuration
- `prod.yaml` - Production configuration

### Key Configuration Options

```yaml
# Orchestrator
orchestrator:
  grpc_address: localhost:50051
  log_level: INFO
  engines:
    collaborative: http://localhost:8001
    comparative: http://localhost:8002
    chained: http://localhost:8003

# Daemon
daemon:
  node_id: node-001
  grpc_address: localhost:50052
  cache_dir: /var/lib/dim/models
  max_cache_gb: 50
  max_concurrent_jobs: 10

# IPFS
ipfs:
  api_url: /ip4/127.0.0.1/tcp/5001
  ipns_key_name: dim-state-key
  pubsub:
    job_updates: dim.jobs.updates
    node_heartbeat: dim.nodes.heartbeat
    results_ready: dim.results.ready
```

See `config/dev.yaml` for complete configuration options.

## Quick Start

### 1. Setup Development Environment

```bash
# Run setup script
cd powernode/dim
./scripts/setup-dev.sh
```

### 2. Start IPFS

```bash
# Start IPFS daemon (in separate terminal)
ipfs daemon

# Verify IPFS is running
./scripts/check-ipfs.sh
```

### 3. Start All Services

```bash
# Start all services in tmux
./scripts/start-all.sh

# Or start individually:
./scripts/start-orchestrator.sh
./scripts/start-pattern-engine.sh collaborative
./scripts/start-daemon.sh
./scripts/start-api-gateway.sh dev
```

### 4. Submit a Job

```bash
# Via API Gateway (when running)
curl -X POST http://localhost:3000/api/inference/submit \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "collaborative",
    "config": {
      "modelId": "model-abc123",
      "nodes": ["node-001", "node-002"],
      "aggregation": {"method": "federated_averaging"}
    }
  }'
```

## Implementation Status

### Phase 1: Foundation ✅ (Complete)
- [x] Project structure
- [x] Data models (JobSpec, JobStatus, NodeInfo, NodeRegistry)
- [x] IPFS integration (IPNS + Pubsub)
- [x] Orchestrator core with job lifecycle
- [x] Pattern router
- [x] Node selector with reputation-based selection
- [x] Base pattern engine
- [x] All three pattern engines (Collaborative, Comparative, Chained)
- [x] DIM Daemon with job queue and resource management
- [x] Agent execution with MLX/CoreML/PyTorch/ONNX loaders
- [x] API Gateway (Node.js/TypeScript) with Fastify
- [x] gRPC Protocol Buffer definitions
- [x] IPFS state management (IPNS, Pubsub)
- [x] Configuration files and setup scripts
- [x] Documentation

### Phase 2: Distribution (Planned)
- [ ] Multi-node deployment
- [ ] Full gRPC service implementation
- [ ] Distributed orchestrators
- [ ] PAIneer integration
- [ ] Performance optimization
- [ ] Production deployment guides

## Scripts

All scripts are in `scripts/` directory:

- `setup-dev.sh` - Setup development environment
- `start-orchestrator.sh` - Start orchestrator
- `start-daemon.sh` - Start daemon
- `start-pattern-engine.sh` - Start pattern engine
- `start-api-gateway.sh` - Start API Gateway
- `start-all.sh` - Start all services (tmux)
- `stop-all.sh` - Stop all services
- `check-ipfs.sh` - Check IPFS connectivity
- `generate-proto.sh` - Generate gRPC code

## Development

### Running Tests

```bash
# Unit tests (when implemented)
pytest tests/

# Integration tests
pytest tests/integration/
```

### Code Style

- **Python**: Follow PEP 8, use `black` for formatting
- **TypeScript**: Use `prettier` and `eslint`

### Generating gRPC Code

```bash
# Generate Python and TypeScript code from .proto files
./scripts/generate-proto.sh
```

## Architecture Details

### IPFS State Management

- **IPNS**: Mutable state for node registry and active jobs
- **Pubsub**: Real-time coordination for job updates and heartbeats
- See [IPFS State Management Documentation](docs/IPFS_STATE_MANAGEMENT.md)

### Pattern Engines

Each pattern engine is a standalone HTTP service:
- **Collaborative**: Port 8001
- **Comparative**: Port 8002
- **Chained**: Port 8003

### Communication Flow

1. Client → API Gateway (REST/WebSocket)
2. API Gateway → Orchestrator (gRPC - Phase 2, HTTP - Phase 1)
3. Orchestrator → Pattern Engine (HTTP)
4. Pattern Engine → Daemon (gRPC - Phase 2, HTTP - Phase 1)
5. Daemon → Agent (Multiprocessing)
6. Coordination: IPFS Pubsub for events, IPNS for state

## Dependencies

### Python
- `pydantic>=2.5.0` - Data validation
- `httpx>=0.25.0` - Async HTTP client
- `pyyaml>=6.0.1` - YAML parsing
- `fastapi>=0.104.0` - HTTP server (pattern engines)
- `grpcio>=1.59.0` - gRPC (Phase 2)

### Node.js (API Gateway - Phase 2)
- `fastify>=4.24.0` - REST API server
- `@fastify/websocket>=8.3.0` - WebSocket support
- `@grpc/grpc-js>=1.9.0` - gRPC client

## License

Part of the PowerNode AI/ML Stack project.

## References

- [DIM Implementation Specification](../Docs/DIM%20Implementation%20Spec.md)
- [PowerNode Project Scope](../../docs/PROJECT_SCOPE.md)

