# Monitoring Stack

Prometheus + Grafana monitoring for Synth Mind.

## Quick Start

```bash
# Start Synth Mind with monitoring
docker-compose -f docker-compose.yml -f monitoring/docker-compose.monitoring.yml up -d

# Access dashboards
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

## Components

| Service | Port | Description |
|---------|------|-------------|
| Synth Mind | 8080 | Application with `/metrics` endpoint |
| Prometheus | 9090 | Metrics collection and storage |
| Grafana | 3000 | Visualization and dashboards |

## Dashboards

### Synth Mind Dashboard

Pre-configured dashboard with panels for:

**Overview Row:**
- Service Status (up/down)
- WebSocket Connections
- Request Rate
- Active Projects
- Total Turns
- Success Rate

**Cognitive State Row:**
- Emotional Valence gauge (-1 to 1)
- Flow State gauge (bored/flow/overloaded)
- Uncertainty Level gauge
- Dream Alignment gauge

**HTTP Performance Row:**
- Request Rate by Endpoint (graph)
- Request Latency p50/p95 (graph)

**LLM Provider Row:**
- LLM Requests by Provider (graph)
- LLM Response Latency (graph)

**Memory & Projects Row:**
- Memory Store Size (episodic + semantic)
- Projects (active, completed, iterations)

## Metrics Reference

### HTTP Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `synth_http_requests_total` | Counter | method, endpoint, status | Total HTTP requests |
| `synth_http_request_duration_seconds` | Histogram | method, endpoint | Request latency |

### Cognitive Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `synth_emotional_valence` | Gauge | Current emotional state (-1 to 1) |
| `synth_flow_state` | Gauge | Flow state (0=bored, 0.5=flow, 1=overloaded) |
| `synth_coherence_score` | Gauge | Meta-reflection coherence |
| `synth_dream_alignment` | Gauge | Predictive dreaming alignment |
| `synth_uncertainty_level` | Gauge | Current uncertainty |

### LLM Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `synth_llm_requests_total` | Counter | provider | LLM API requests |
| `synth_llm_request_duration_seconds` | Histogram | provider | LLM latency |

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `synth_websocket_connections` | Gauge | Active WebSocket connections |
| `synth_turns_total` | Counter | Conversation turns processed |
| `synth_active_projects` | Gauge | Active GDIL projects |
| `synth_completed_projects_total` | Counter | Completed projects |
| `synth_memory_episodes` | Gauge | Episodic memory count |
| `synth_memory_semantic` | Gauge | Semantic memory count |

## Alerting (Optional)

Create alert rules in `monitoring/prometheus/alerts/`:

```yaml
# monitoring/prometheus/alerts/synth.yml
groups:
  - name: synth-mind
    rules:
      - alert: SynthMindDown
        expr: up{job="synth-mind"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Synth Mind is down"

      - alert: HighErrorRate
        expr: rate(synth_http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(synth_http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High request latency"
```

## Customization

### Add Custom Panels

1. Open Grafana (http://localhost:3000)
2. Edit the Synth Mind dashboard
3. Add panels using PromQL queries
4. Export dashboard JSON
5. Replace `monitoring/grafana/synth-mind-dashboard.json`

### Modify Scrape Interval

Edit `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'synth-mind'
    scrape_interval: 5s  # Default: 10s
```

### Add More Targets

For multiple Synth Mind instances:

```yaml
scrape_configs:
  - job_name: 'synth-mind'
    static_configs:
      - targets:
          - 'synth-1:8080'
          - 'synth-2:8080'
          - 'synth-3:8080'
```

## Troubleshooting

### No Metrics in Prometheus

1. Check Synth Mind is running: `curl http://localhost:8080/health`
2. Check metrics endpoint: `curl http://localhost:8080/metrics`
3. Check Prometheus targets: http://localhost:9090/targets

### Dashboard Not Loading

1. Check Grafana logs: `docker logs synth-grafana`
2. Verify datasource: http://localhost:3000/datasources
3. Re-import dashboard from JSON file
