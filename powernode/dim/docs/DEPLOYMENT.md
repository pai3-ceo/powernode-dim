# DIM Deployment Guide

## Single Node Deployment (Phase 1)

### Prerequisites

- Mac Mini M4 Pro (or compatible)
- macOS with Python 3.11+ and Node.js 20+
- IPFS installed and running
- 50GB+ free disk space for model cache

### Step 1: Install Dependencies

```bash
cd powernode/dim
./scripts/setup-dev.sh
```

### Step 2: Configure IPFS

```bash
# Initialize IPFS (if not already done)
ipfs init

# Configure for private network (optional)
# Add swarm key for private IPFS network

# Start IPFS daemon
ipfs daemon &
```

### Step 3: Start Services

```bash
# Option 1: Start all services (tmux)
./scripts/start-all.sh

# Option 2: Start individually
./scripts/start-orchestrator.sh &
./scripts/start-pattern-engine.sh collaborative &
./scripts/start-pattern-engine.sh comparative &
./scripts/start-pattern-engine.sh chained &
./scripts/start-daemon.sh &
./scripts/start-api-gateway.sh dev &
```

### Step 4: Verify Deployment

```bash
# Check IPFS
./scripts/check-ipfs.sh

# Check API Gateway
curl http://localhost:3000/health

# Check orchestrator (if gRPC enabled)
# grpcurl -plaintext localhost:50051 list
```

## Multi-Node Deployment (Phase 2)

### Node Setup

On each PowerNode:

```bash
# 1. Install DIM
cd powernode/dim
./scripts/setup-dev.sh

# 2. Configure node ID
export NODE_ID=node-001  # Unique per node

# 3. Configure Tailscale
sudo tailscale up --accept-routes

# 4. Start IPFS with cluster
ipfs-cluster-service init
ipfs-cluster-service daemon &

# 5. Start DIM daemon
./scripts/start-daemon.sh
```

### Orchestrator Setup

On orchestrator node:

```bash
# 1. Start orchestrator
./scripts/start-orchestrator.sh

# 2. Configure IPFS registry IPNS
# (Will be created automatically on first use)
```

## Production Deployment

### Using PM2 (Node.js Services)

```bash
# Install PM2
npm install -g pm2

# Start API Gateway
cd api-gateway
pm2 start npm --name "dim-api-gateway" -- run start
```

### Using launchd (macOS Services)

Create plist files in `/Library/LaunchDaemons/`:

```xml
<!-- com.pai3.dim.orchestrator.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pai3.dim.orchestrator</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/powernode/dim/scripts/start-orchestrator.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load service:
```bash
sudo launchctl load /Library/LaunchDaemons/com.pai3.dim.orchestrator.plist
```

### Docker Deployment (Optional)

```dockerfile
# Dockerfile for orchestrator
FROM python:3.11-slim

WORKDIR /app
COPY orchestrator/requirements.txt .
RUN pip install -r requirements.txt

COPY orchestrator/ .
CMD ["python", "main.py"]
```

## Monitoring

### Health Checks

```bash
# API Gateway
curl http://localhost:3000/health

# Pattern Engines
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# IPFS
curl http://localhost:5001/api/v0/id
```

### Logs

```bash
# Orchestrator logs
tail -f /var/log/dim/orchestrator.log

# Daemon logs (if configured)
tail -f /var/log/dim/daemon.log

# IPFS logs
ipfs log tail
```

### Metrics

- **Job Status**: Query via API or IPNS
- **Node Health**: Monitor via Pubsub heartbeats
- **Resource Usage**: Check daemon stats endpoint

## Troubleshooting

### IPFS Connection Issues

```bash
# Check IPFS is running
curl http://localhost:5001/api/v0/id

# Check IPFS config
ipfs config show

# Restart IPFS
ipfs daemon --restart
```

### Service Not Starting

```bash
# Check logs
./scripts/check-ipfs.sh

# Verify dependencies
python3 --version
node --version
ipfs version

# Check ports
lsof -i :50051  # Orchestrator
lsof -i :50052  # Daemon
lsof -i :8001   # Collaborative engine
lsof -i :3000   # API Gateway
```

### Job Failures

1. Check daemon logs for errors
2. Verify model is available in IPFS
3. Check node resources (CPU, memory)
4. Verify data cabinet access

## Backup & Recovery

### IPFS Data

```bash
# Backup IPFS repository
tar -czf ipfs-backup.tar.gz ~/.ipfs

# Restore IPFS repository
tar -xzf ipfs-backup.tar.gz -C ~/
```

### Configuration

```bash
# Backup configuration
cp -r config/ config-backup/

# Restore configuration
cp -r config-backup/* config/
```

## Scaling

### Horizontal Scaling

- Add more PowerNodes
- Update node registry via IPNS
- Orchestrator automatically discovers new nodes

### Vertical Scaling

- Increase `max_concurrent_jobs` in daemon config
- Increase `max_cache_gb` for more models
- Adjust resource limits in `resource_manager.py`

## Security

### Network Security

- Use Tailscale for private network
- Configure firewall rules
- Enable TLS (Phase 2)

### Access Control

- Implement authentication (PAIneer - Phase 2)
- Use API keys for service-to-service communication
- Audit all job submissions

