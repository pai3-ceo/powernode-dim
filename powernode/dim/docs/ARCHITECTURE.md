# DIM Architecture Documentation

## System Architecture

### High-Level Overview

DIM (Decentralized Inference Machine) is a distributed AI inference orchestration system that enables:

- **Decentralized Execution**: Jobs run across multiple PowerNodes
- **Data Privacy**: Data never leaves nodes (privacy-first)
- **Multiple Patterns**: Collaborative, Comparative, and Chained inference
- **Real-time Coordination**: IPFS Pubsub for event coordination
- **Mutable State**: IPNS for node registry and job tracking

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│              (Healthcare, Government, Legal, etc.)           │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS/REST + WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         API Gateway (Node.js/TypeScript)                     │
│  • Fastify REST API                                          │
│  • WebSocket for real-time updates                          │
│  • Request validation (Zod)                                 │
│  • Authentication (PAIneer - Phase 2)                       │
└────────────────────────┬─────────────────────────────────────┘
                         │ gRPC (Phase 2) / HTTP (Phase 1)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DIM Orchestrator (Python)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Job lifecycle management                           │   │
│  │ • Pattern routing                                    │   │
│  │ • Node selection (reputation-based)                 │   │
│  │ • IPFS state management (IPNS + Pubsub)              │   │
│  │ • Event coordination                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└────┬────────────┬────────────┬───────────────────────────────┘
     │            │            │ HTTP
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│Collab   │  │Compar   │  │Chained  │
│Engine   │  │Engine   │  │Engine   │
│:8001    │  │:8002    │  │:8003    │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │ gRPC (Phase 2)
     └────────────┴────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              DIM Daemon (on each PowerNode)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • gRPC Server (receives jobs)                        │   │
│  │ • Job Queue (priority-based)                        │   │
│  │ • Resource Manager (CPU/Memory/GPU)                  │   │
│  │ • Model Cache (50GB LRU)                            │   │
│  │ • Agent Manager (process spawning)                  │   │
│  │ • Data Cabinet Access                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Agent Pool (spawned on demand)               │   │
│  │  • Separate Python processes                         │   │
│  │  • 120s timeout enforcement                          │   │
│  │  • MLX/CoreML/PyTorch/ONNX inference                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│           Private IPFS Cluster (Tailscale Network)          │
│  • Persistent Storage: Models, Jobs, Results                │
│  • Mutable State (IPNS): Node Registry, Active Jobs         │
│  • Real-time Coordination (Pubsub): Events, Heartbeats       │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Collaborative Pattern Flow

1. **Client submits job** → API Gateway
2. **API Gateway validates** → Forwards to Orchestrator
3. **Orchestrator routes** → Collaborative Engine
4. **Engine distributes** → Same model to multiple nodes
5. **Daemons execute** → Parallel inference on local data
6. **Results aggregated** → Federated averaging or weighted average
7. **Final result** → Saved to IPFS, returned to client

### Comparative Pattern Flow

1. **Client submits job** → API Gateway
2. **Orchestrator routes** → Comparative Engine
3. **Engine loads models** → Multiple models on single node
4. **Sequential execution** → Each model processes same data
5. **Consensus building** → Majority vote or weighted vote
6. **Final result** → Consensus output returned

### Chained Pattern Flow

1. **Client submits job** → API Gateway
2. **Orchestrator routes** → Chained Engine
3. **Engine executes steps** → Sequential pipeline
4. **Step N output** → Passed to step N+1
5. **Error handling** → Rollback on failure
6. **Final result** → Last step output returned

## State Management

### IPNS (Mutable State)

- **Node Registry**: `/ipns/dim-node-registry` - List of active nodes
- **Active Jobs**: `/ipns/dim-active-jobs` - Current job statuses
- **Updates**: Periodic updates via IPNS publish

### IPFS Pubsub (Real-time Events)

- **Topics**:
  - `dim.jobs.updates` - Job status changes
  - `dim.nodes.heartbeat` - Node health updates
  - `dim.results.ready` - Result availability

### State Consistency

- **Eventual Consistency**: IPNS updates propagate over time
- **Real-time Updates**: Pubsub provides immediate notifications
- **Local Cache**: Orchestrator maintains local cache for fast access

## Security & Privacy

### Data Privacy

- **Data Never Leaves Nodes**: Inference happens on node with data
- **Encrypted Communication**: TLS for all API communication
- **Private Network**: Tailscale for node-to-node communication

### Access Control

- **Authentication**: PAIneer integration (Phase 2)
- **Authorization**: Job-level permissions
- **Audit Logging**: All operations logged

## Performance

### Scalability

- **Horizontal Scaling**: Add more PowerNodes
- **Load Balancing**: Reputation-based node selection
- **Resource Management**: Per-node resource limits

### Optimization

- **Model Caching**: 50GB local cache per node
- **Connection Pooling**: Reuse connections (Phase 2)
- **Pre-warming**: Pre-load popular models (Phase 2)

## Failure Handling

### Node Failures

- **Heartbeat Monitoring**: Detect node failures via Pubsub
- **Job Retry**: Automatic retry on different node
- **Graceful Degradation**: Continue with available nodes

### Job Failures

- **Timeout Enforcement**: 120s timeout per agent
- **Error Propagation**: Errors reported via Pubsub
- **Partial Results**: Return partial results if possible

## Monitoring

### Metrics

- **Job Status**: Tracked via IPNS and local cache
- **Node Health**: Heartbeat monitoring via Pubsub
- **Resource Usage**: Per-node resource tracking
- **Performance**: Execution time, success rate

### Logging

- **Structured Logging**: JSON logs for all components
- **Log Aggregation**: Centralized logging (Phase 2)
- **Audit Trail**: Complete job execution history

