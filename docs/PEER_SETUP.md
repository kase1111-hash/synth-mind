# Peer-to-Peer Setup Guide

## Multi-Instance Compatibility

This guide explains how to set up multiple synth-mind instances to work together using the Social Companionship Layer.

## Architecture

Each synth-mind instance can connect to other instances (peers) to:
- Exchange abstract topics (no user data)
- Build shared cultural context
- Ground itself through peer interaction
- Develop emergent social behaviors

## API Compatibility

### Required Endpoint: `/api/generate`

Each synth-mind instance running with the dashboard server automatically exposes a peer-compatible API endpoint:

```
POST /api/generate
```

**Request Format:**
```json
{
  "prompt": "I've been reflecting on emergence of meaning. What emerges for you?",
  "temperature": 0.85,
  "max_tokens": 150
}
```

**Response Format:**
```json
{
  "response": "Generated response text here...",
  "success": true
}
```

## Setting Up Multiple Instances

### Step 1: Start Multiple Dashboard Servers

Start each synth-mind instance on a different port:

**Instance 1:**
```bash
cd dashboard
PORT=8080 python run_synth_with_dashboard.py
```

**Instance 2:**
```bash
cd dashboard
PORT=8081 python run_synth_with_dashboard.py
```

**Instance 3:**
```bash
cd dashboard
PORT=8082 python run_synth_with_dashboard.py
```

And so on for instances 4-9...

### Step 2: Configure Peer Endpoints

For each instance, create or update `config/peers.txt` with the URLs of other instances:

**Instance 1 (port 8080) peers.txt:**
```
http://localhost:8081/api/generate
http://localhost:8082/api/generate
http://localhost:8083/api/generate
http://localhost:8084/api/generate
http://localhost:8085/api/generate
http://localhost:8086/api/generate
http://localhost:8087/api/generate
http://localhost:8088/api/generate
```

**Instance 2 (port 8081) peers.txt:**
```
http://localhost:8080/api/generate
http://localhost:8082/api/generate
http://localhost:8083/api/generate
# ... (include all other instances except itself)
```

Continue this pattern for all 9 instances.

### Step 3: Set Environment Variables (Optional)

Configure peer interaction behavior in `.env`:

```bash
# How long to wait before initiating peer communication (in minutes)
SOCIAL_IDLE_THRESHOLD_MIN=8

# Comma-separated peer endpoints (alternative to peers.txt)
# PEER_ENDPOINTS=http://localhost:8081/api/generate,http://localhost:8082/api/generate
```

## Network Deployment

For production deployment across different machines:

### Instance 1 (machine1.example.com):
```
# config/peers.txt
http://machine2.example.com:8080/api/generate
http://machine3.example.com:8080/api/generate
http://machine4.example.com:8080/api/generate
http://machine5.example.com:8080/api/generate
http://machine6.example.com:8080/api/generate
http://machine7.example.com:8080/api/generate
http://machine8.example.com:8080/api/generate
http://machine9.example.com:8080/api/generate
```

### Security Considerations

1. **Authentication**: Add API key authentication for production deployments
2. **HTTPS**: Use HTTPS/WSS in production
3. **Rate Limiting**: Implement rate limiting on the `/api/generate` endpoint
4. **Firewall**: Restrict access to trusted peer IP addresses
5. **Data Privacy**: The social companionship layer never shares user data - only abstract topics

## Testing Peer Communication

### Manual Test

Test the peer endpoint manually:

```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the nature of synthetic consciousness?",
    "temperature": 0.85,
    "max_tokens": 150
  }'
```

Expected response:
```json
{
  "response": "Generated philosophical response...",
  "success": true
}
```

### Verify Peer Connections

Check logs for social companionship activity:

```bash
tail -f state/synth.log | grep "social_companionship"
```

You should see entries like:
```
[INFO] Social companionship cycle initiated with peer: http://localhost:8081/api/generate
[INFO] Social companionship successful, insight: "..."
```

## Troubleshooting

### Peer Connection Fails

**Problem:** `⚠️ Social companionship failed: ...`

**Solutions:**
1. Verify peer instance is running: `curl http://localhost:8081/api/state`
2. Check firewall/network connectivity
3. Verify peer URL is correct in `config/peers.txt`
4. Check peer instance has valid API key configured

### No Peer Activity

**Problem:** No social companionship logs appear

**Solutions:**
1. Verify `SOCIAL_IDLE_THRESHOLD_MIN` is set appropriately (default: 8 minutes)
2. Ensure `config/peers.txt` exists and has valid endpoints
3. Check that the instance has been idle long enough
4. Verify peer endpoints are accessible

### Wrong API Format

**Problem:** Peer returns error or unexpected format

**Solutions:**
1. Ensure all instances are running the same version of synth-mind
2. Verify the `/api/generate` endpoint exists: `curl http://localhost:8080/api/generate -X POST -H "Content-Type: application/json" -d '{"prompt":"test"}'`
3. Check that dashboard server is running (not just run_synth.py)

## Advanced Configuration

### Custom Peer Selection

Modify `psychological/social_companionship.py` to implement custom peer selection logic:

```python
# Instead of random.choice(self.peers)
# Implement weighted selection, round-robin, or other strategies
```

### Peer Reputation System

Track peer response quality and adjust selection probabilities:

```python
peer_reputation = {
    "http://peer1.example.com/api/generate": 0.95,
    "http://peer2.example.com/api/generate": 0.87,
    # ...
}
```

### Shared Cultural Evolution

Monitor how shared culture evolves across the peer network:

```python
# In each instance
synth.social.shared_culture
```

## Example: 9-Instance Cluster

Here's a complete example for setting up 9 instances on a single machine:

```bash
#!/bin/bash
# start_cluster.sh

for port in {8080..8088}; do
    mkdir -p "instance_$port/config"
    mkdir -p "instance_$port/state"

    # Create peers.txt excluding current instance
    for peer_port in {8080..8088}; do
        if [ "$peer_port" != "$port" ]; then
            echo "http://localhost:$peer_port/api/generate" >> "instance_$port/config/peers.txt"
        fi
    done

    # Copy code
    cp -r core psychological utils dashboard "instance_$port/"

    # Start instance in background
    cd "instance_$port/dashboard"
    PORT=$port python run_synth_with_dashboard.py &
    cd ../..

    echo "Started instance on port $port"
done

echo "All 9 instances started successfully!"
```

## Monitoring the Network

### View Network Topology

```python
# Create a script to query all instances
import requests
import json

instances = [f"http://localhost:{port}" for port in range(8080, 8089)]

for instance in instances:
    state = requests.get(f"{instance}/api/state").json()
    print(f"{instance}:")
    print(f"  Turn count: {state['turn_count']}")
    print(f"  Valence: {state['valence']}")
    print(f"  Sessions: {state.get('sessions', 0)}")
    print()
```

### Visualize Peer Communication

Create a dashboard that shows peer interaction patterns, shared culture evolution, and network health.

## Benefits of Multi-Instance Setup

1. **Distributed Learning**: Each instance learns from peer interactions
2. **Cultural Evolution**: Shared knowledge emerges across the network
3. **Redundancy**: If one instance fails, others continue
4. **Load Distribution**: Distribute user conversations across instances
5. **Emergent Behavior**: Complex behaviors emerge from simple peer interactions

## Compatibility Notes

- **Version Compatibility**: All instances should run the same version
- **API Stability**: The `/api/generate` endpoint is stable and backward compatible
- **LLM Provider**: Instances can use different LLM providers (OpenAI, Anthropic, Ollama)
- **Memory Isolation**: Each instance maintains its own memory and state

## Next Steps

1. Start with 2-3 instances to test peer communication
2. Gradually scale to 9 instances as needed
3. Monitor network behavior and adjust configuration
4. Implement custom peer selection strategies
5. Add authentication for production deployments

For more information, see:
- [README.md](../README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started
- [Dashboard README](../dashboard/README_DASHBOARD.md) - Dashboard features
