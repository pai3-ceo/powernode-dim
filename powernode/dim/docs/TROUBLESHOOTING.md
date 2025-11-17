# DIM Troubleshooting Guide

Common issues and solutions for DIM deployment and operation.

## IPFS Issues

### IPFS Daemon Not Running

**Symptoms**: Connection errors, "Failed to connect to IPFS daemon"

**Solution**:
```bash
# Check if IPFS is running
curl http://localhost:5001/api/v0/id

# Start IPFS daemon
ipfs daemon &

# Verify
./scripts/check-ipfs.sh
```

### IPNS Not Working

**Symptoms**: "Failed to initialize IPNS manager", state not updating

**Solution**:
```bash
# Check IPNS keys
ipfs key list

# Create key if needed
ipfs key gen dim-state-key

# Verify key
ipfs key list | grep dim-state-key
```

### Pubsub Not Receiving Messages

**Symptoms**: No events, heartbeats not updating

**Solution**:
```bash
# Check pubsub subscriptions
ipfs pubsub ls

# Test pubsub manually
ipfs pubsub pub dim.jobs.updates '{"test": true}'
ipfs pubsub sub dim.jobs.updates
```

## Service Startup Issues

### Orchestrator Won't Start

**Symptoms**: Import errors, connection failures

**Solution**:
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Verify virtual environment
cd orchestrator
source venv/bin/activate
pip list

# Check dependencies
pip install -r requirements.txt

# Check IPFS connection
curl http://localhost:5001/api/v0/id
```

### Pattern Engine Won't Start

**Symptoms**: Port already in use, import errors

**Solution**:
```bash
# Check if port is in use
lsof -i :8001  # Collaborative
lsof -i :8002  # Comparative
lsof -i :8003  # Chained

# Kill process if needed
kill -9 <PID>

# Verify dependencies
cd pattern_engines/collaborative
source venv/bin/activate
pip install -r requirements.txt
```

### Daemon Won't Start

**Symptoms**: Resource errors, import failures

**Solution**:
```bash
# Check node ID
export NODE_ID=node-001

# Verify resources
# Check CPU, memory availability

# Check dependencies
cd daemon
source venv/bin/activate
pip install -r requirements.txt

# Check IPFS
curl http://localhost:5001/api/v0/id
```

### API Gateway Won't Start

**Symptoms**: Port in use, TypeScript errors

**Solution**:
```bash
# Check port
lsof -i :3000

# Install dependencies
cd api-gateway
npm install

# Build TypeScript
npm run build

# Check for errors
npm run dev
```

## Job Execution Issues

### Job Stuck in Pending

**Symptoms**: Job never starts, no progress

**Solution**:
1. Check orchestrator logs
2. Verify pattern engine is running
3. Check IPFS connectivity
4. Verify node selection (check node registry)

### Job Timeout

**Symptoms**: "Agent timeout after 120s"

**Solution**:
1. Increase timeout in job spec
2. Check model size (may be too large)
3. Verify node resources (CPU, memory)
4. Check for deadlocks in agent code

### Model Not Found

**Symptoms**: "Model not found", download failures

**Solution**:
```bash
# Check model in IPFS
ipfs ls /pai3/dim/models/

# Verify model cache
ls -lh /var/lib/dim/models/

# Check cache size
du -sh /var/lib/dim/models/
```

### Node Selection Fails

**Symptoms**: "No eligible nodes found"

**Solution**:
1. Check node registry (IPNS)
2. Lower reputation threshold
3. Verify node heartbeats (Pubsub)
4. Check node status in registry

## Performance Issues

### Slow Job Execution

**Symptoms**: Jobs take too long

**Solution**:
1. Check node resources (CPU, memory)
2. Verify model is cached (not downloading)
3. Check network latency
4. Optimize model size

### High Memory Usage

**Symptoms**: Out of memory errors

**Solution**:
1. Reduce `max_concurrent_jobs` in daemon config
2. Increase `max_memory_gb` limit
3. Clear model cache
4. Check for memory leaks

### IPFS Slow

**Symptoms**: Slow state updates, Pubsub delays

**Solution**:
1. Check IPFS daemon resources
2. Verify network connectivity
3. Check IPFS repo size
4. Consider IPFS cluster for production

## Configuration Issues

### Config Not Loading

**Symptoms**: Using default values, errors

**Solution**:
```bash
# Verify config file exists
ls -la config/dev.yaml

# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config/dev.yaml'))"

# Check environment variables
env | grep DIM_
```

### Wrong IPFS Address

**Symptoms**: Connection failures, wrong API endpoint

**Solution**:
```bash
# Check IPFS API address
ipfs config Addresses.API

# Update config
# api_url: /ip4/127.0.0.1/tcp/5001
```

## Network Issues

### Services Can't Communicate

**Symptoms**: Connection refused, timeouts

**Solution**:
1. Check firewall rules
2. Verify ports are open
3. Check service addresses in config
4. Test connectivity: `curl http://localhost:8001/health`

### Tailscale Not Working (Phase 2)

**Symptoms**: Nodes can't discover each other

**Solution**:
```bash
# Check Tailscale status
tailscale status

# Verify network
tailscale ping <node-ip>

# Check routes
tailscale routes
```

## Debugging Tips

### Enable Debug Logging

```yaml
# config/dev.yaml
orchestrator:
  log_level: DEBUG

daemon:
  log_level: DEBUG
```

### Check Service Logs

```bash
# Orchestrator
tail -f /var/log/dim/orchestrator.log

# Daemon
tail -f /var/log/dim/daemon.log

# IPFS
ipfs log tail
```

### Test Components Individually

```bash
# Test IPFS
./scripts/check-ipfs.sh

# Test orchestrator
cd orchestrator
source venv/bin/activate
python -c "from src.orchestrator import DIMOrchestrator; print('OK')"

# Test pattern engine
curl http://localhost:8001/health
```

### Monitor Resources

```bash
# CPU and memory
top

# Disk usage
df -h

# Network
netstat -an | grep LISTEN
```

## Getting Help

1. Check logs first
2. Verify configuration
3. Test components individually
4. Check IPFS connectivity
5. Review documentation

For more help, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Deployment Guide](DEPLOYMENT.md)

