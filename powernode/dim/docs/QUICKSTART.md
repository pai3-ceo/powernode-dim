# DIM Quick Start Guide

Get DIM running in 5 minutes!

## Prerequisites Check

```bash
# Check Python
python3 --version  # Should be 3.11+

# Check Node.js
node --version  # Should be 20+

# Check IPFS
ipfs version  # Should be 0.24+
```

## Quick Setup

### 1. Setup Environment

```bash
cd powernode/dim
./scripts/setup-dev.sh
```

This will:
- Create Python virtual environments
- Install all dependencies
- Setup Node.js API Gateway
- Initialize IPFS (if needed)

### 2. Start IPFS

```bash
# In a separate terminal
ipfs daemon
```

### 3. Start All Services

```bash
# Start everything in tmux
./scripts/start-all.sh

# Attach to see logs
tmux attach -t dim-services
```

### 4. Test the System

```bash
# Check health
curl http://localhost:3000/health

# Submit a test job
curl -X POST http://localhost:3000/api/inference/submit \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "collaborative",
    "config": {
      "modelId": "test-model",
      "nodes": ["node-001"],
      "aggregation": {"method": "federated_averaging"}
    }
  }'
```

## What's Running?

After `start-all.sh`, you should have:

- **Orchestrator** - Port 50051 (gRPC) or localhost
- **Collaborative Engine** - Port 8001
- **Comparative Engine** - Port 8002
- **Chained Engine** - Port 8003
- **Daemon** - Port 50052 (gRPC) or localhost
- **API Gateway** - Port 3000

## Next Steps

1. **Read the API Reference**: See `docs/API_REFERENCE.md`
2. **Understand Patterns**: See main `README.md`
3. **Explore IPFS State**: See `docs/IPFS_STATE_MANAGEMENT.md`
4. **Deploy to Production**: See `docs/DEPLOYMENT.md`

## Troubleshooting

### Services won't start?

```bash
# Check IPFS
./scripts/check-ipfs.sh

# Check logs
tail -f /var/log/dim/*.log

# Verify ports aren't in use
lsof -i :3000
lsof -i :8001
```

### IPFS not working?

```bash
# Initialize IPFS
ipfs init

# Start daemon
ipfs daemon &

# Verify
ipfs id
```

## Stopping Services

```bash
# Stop all services
./scripts/stop-all.sh

# Or manually
tmux kill-session -t dim-services
```

## Development Tips

- Use `tmux attach -t dim-services` to see all service logs
- Check `config/dev.yaml` for configuration options
- Use `./scripts/check-ipfs.sh` to verify IPFS setup
- Monitor IPFS Pubsub: `ipfs pubsub ls`

