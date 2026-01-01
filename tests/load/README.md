# Load Testing

Load tests for Synth Mind using [k6](https://k6.io/).

## Prerequisites

Install k6:

```bash
# macOS
brew install k6

# Linux (Debian/Ubuntu)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Docker
docker pull grafana/k6
```

## Running Tests

### Quick Smoke Test

```bash
k6 run --vus 5 --duration 10s tests/load/load_test.js
```

### Standard Load Test

```bash
k6 run tests/load/load_test.js
```

### High Load Test

```bash
k6 run --vus 100 --duration 5m tests/load/load_test.js
```

### With Authentication

```bash
k6 run -e AUTH_USER=admin -e AUTH_PASS=yourpassword tests/load/load_test.js
```

### Against Different Environment

```bash
k6 run -e BASE_URL=https://synth.example.com -e WS_URL=wss://synth.example.com/ws tests/load/load_test.js
```

### With Docker

```bash
docker run --rm -i grafana/k6 run - <tests/load/load_test.js
```

## Test Scenarios

The load test includes these scenarios:

| Scenario | Description |
|----------|-------------|
| Health Checks | Tests `/health`, `/health/live`, `/health/ready`, `/metrics` |
| State API | Tests `GET /api/state` |
| Chat API | Tests `POST /api/chat` with random messages |
| WebSocket | Tests WebSocket connection and state updates |

## Stages

Default test stages (configurable):

| Stage | Duration | VUs | Description |
|-------|----------|-----|-------------|
| 1 | 30s | 0→10 | Ramp up |
| 2 | 1m | 10 | Steady state |
| 3 | 30s | 10→25 | Increase load |
| 4 | 1m | 25 | Steady state |
| 5 | 30s | 25→50 | Peak load |
| 6 | 1m | 50 | Sustained peak |
| 7 | 30s | 50→0 | Ramp down |

## Thresholds

Tests fail if thresholds are exceeded:

| Metric | Threshold | Description |
|--------|-----------|-------------|
| `http_req_duration` | p95 < 2s | 95% of requests under 2 seconds |
| `http_req_failed` | rate < 1% | Less than 1% failed requests |
| `errors` | rate < 5% | Custom error rate under 5% |
| `chat_latency` | p95 < 5s | Chat responses under 5 seconds |

## Custom Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `errors` | Rate | Custom error rate across all tests |
| `chat_latency` | Trend | Chat API response time |
| `ws_connections` | Counter | Total WebSocket connections made |

## Output Formats

### JSON Output

```bash
k6 run --out json=results.json tests/load/load_test.js
```

### InfluxDB (for Grafana)

```bash
k6 run --out influxdb=http://localhost:8086/k6 tests/load/load_test.js
```

### Cloud (k6 Cloud)

```bash
k6 cloud tests/load/load_test.js
```

## Interpreting Results

### Good Results

```
✓ http_req_duration..............: avg=150ms  min=10ms  max=500ms  p(95)=300ms
✓ http_req_failed................: 0.00%
✓ errors.........................: 0.50%
✓ chat_latency...................: avg=1.2s   p(95)=2.5s
```

### Problems to Watch

- `http_req_duration p95 > 2s` - Slow responses
- `http_req_failed > 1%` - High error rate
- `ws_connections` not increasing - WebSocket issues
- `chat_latency p95 > 5s` - LLM bottleneck

## Recommendations

### Before Production

1. Run load test against staging environment
2. Verify thresholds are met at expected peak load
3. Monitor server resources during test (CPU, memory)
4. Check database connection pool sizing
5. Verify LLM rate limits are not exceeded

### Performance Tuning

If tests fail:

1. **High latency**: Check LLM provider response times
2. **Connection errors**: Increase server worker count
3. **Memory issues**: Check for memory leaks in long-running tests
4. **Database errors**: Verify SQLite can handle concurrent writes
