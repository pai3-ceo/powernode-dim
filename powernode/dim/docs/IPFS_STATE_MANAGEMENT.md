# IPFS State Management - IPNS and Pubsub

This document describes the IPFS state management implementation for DIM, including IPNS (InterPlanetary Name System) and IPFS Pubsub.

## Overview

DIM uses IPFS for decentralized state management:
- **IPNS**: Mutable pointers to IPFS content (for node registry, active jobs)
- **IPFS Pubsub**: Real-time messaging for coordination (job updates, node heartbeats)

## IPNS (InterPlanetary Name System)

IPNS provides mutable pointers to IPFS content. This allows us to update state without changing the reference.

### Features

- **Key Management**: Automatic key creation and management
- **State Updates**: Update mutable state (node registry, active jobs)
- **State Resolution**: Resolve IPNS names to current CIDs

### Usage

```python
from powernode.dim.orchestrator.src.ipfs.ipns import IPNSManager

# Initialize IPNS manager
ipns = IPNSManager(api_base="http://localhost:5001/api/v0", key_name="dim-state-key")

# Update state
state_data = {
    'nodes': [...],
    'active_jobs': {...},
    'updated_at': '2024-12-19T10:00:00Z'
}
ipns_name = ipns.update_state(state_data, lifetime="24h")

# Get state
state = ipns.get_state(ipns_name)
```

### IPNS Manager API

- `publish(cid, lifetime)`: Publish CID to IPNS
- `resolve(ipns_name)`: Resolve IPNS name to CID
- `update_state(state_data, lifetime)`: Update mutable state
- `get_state(ipns_name)`: Get mutable state
- `get_key_id()`: Get IPNS key ID

## IPFS Pubsub

IPFS Pubsub provides real-time messaging for decentralized coordination.

### Topics

- `dim.jobs.updates`: Job status updates (completed, failed, etc.)
- `dim.nodes.heartbeat`: Node heartbeat messages
- `dim.results.ready`: Result ready notifications

### Usage

```python
from powernode.dim.orchestrator.src.ipfs.pubsub import IPFSPubsub

# Initialize Pubsub
pubsub = IPFSPubsub(api_base="http://localhost:5001/api/v0")

# Publish message
await pubsub.publish('dim.jobs.updates', {
    'job_id': 'job-123',
    'event_type': 'completed',
    'data': {...}
})

# Subscribe to topic
async def handle_message(message: Dict):
    print(f"Received: {message}")

await pubsub.subscribe('dim.jobs.updates', handle_message)
```

### Pubsub API

- `publish(topic, message)`: Publish message to topic
- `subscribe(topic, handler)`: Subscribe to topic with handler
- `unsubscribe(topic)`: Unsubscribe from topic
- `list_peers(topic)`: List peers subscribed to topic
- `list_topics()`: List subscribed topics
- `stop()`: Stop all subscriptions

## IPFS State Manager

The `IPFSStateManager` combines IPNS and Pubsub for complete state management.

### Features

- **Job Status**: Track job status via IPNS
- **Node Registry**: Maintain node registry via IPNS
- **Event Publishing**: Publish events via Pubsub
- **Event Subscription**: Subscribe to events via Pubsub

### Usage

```python
from powernode.dim.orchestrator.src.ipfs.state_manager import IPFSStateManager

# Initialize
config = {
    'ipfs': {
        'api_url': '/ip4/127.0.0.1/tcp/5001',
        'ipns_key_name': 'dim-state-key',
        'pubsub': {
            'job_updates': 'dim.jobs.updates',
            'node_heartbeat': 'dim.nodes.heartbeat'
        }
    }
}
state_manager = IPFSStateManager(config)

# Update job status (via IPNS)
await state_manager.update_job_status('job-123', 'completed', result={...})

# Publish job event (via Pubsub)
await state_manager.publish_job_event('job-123', 'completed', {'result': {...}})

# Subscribe to job updates
async def handle_update(message: Dict):
    print(f"Job update: {message}")

await state_manager.subscribe_to_job_updates(handle_update)

# Update node registry (via IPNS)
registry = {'nodes': [...], 'updated_at': '...'}
ipns_name = await state_manager.update_node_registry(registry)

# Get node registry (via IPNS)
registry = await state_manager.get_node_registry()
```

## Integration

### Orchestrator Integration

The orchestrator uses IPFS state management for:
- Job status tracking (IPNS)
- Node registry (IPNS)
- Job event coordination (Pubsub)
- Node heartbeat monitoring (Pubsub)

### Daemon Integration

The daemon uses IPFS Pubsub for:
- Job completion notifications
- Job failure notifications
- Node heartbeat publishing

## Configuration

```yaml
ipfs:
  api_url: /ip4/127.0.0.1/tcp/5001
  ipns_key_name: dim-state-key
  registry_ipns: /ipns/Qm...  # Optional: specific IPNS for registry
  pubsub:
    job_updates: dim.jobs.updates
    node_heartbeat: dim.nodes.heartbeat
    results_ready: dim.results.ready
```

## Error Handling

- IPNS operations gracefully degrade if IPNS is unavailable
- Pubsub operations are best-effort (failures are logged but don't block)
- State manager continues to work even if IPNS/Pubsub fail

## Performance Considerations

- IPNS updates are relatively slow (seconds)
- Pubsub is fast (milliseconds) but best-effort
- Use IPNS for persistent state, Pubsub for real-time updates
- Cache IPNS state locally to reduce resolution calls

## Security

- IPNS keys are stored in IPFS keychain
- Pubsub messages are not encrypted by default (use private network)
- Use Tailscale private network for secure communication

## Future Enhancements (Phase 2)

- Encrypted Pubsub messages
- IPNS key rotation
- Distributed IPNS resolution
- Pubsub message persistence
- Message ordering guarantees

