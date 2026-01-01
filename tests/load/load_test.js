/**
 * Synth Mind - k6 Load Testing Suite
 *
 * Run with: k6 run tests/load/load_test.js
 *
 * Options:
 *   k6 run --vus 10 --duration 30s tests/load/load_test.js  # Quick test
 *   k6 run --vus 50 --duration 5m tests/load/load_test.js   # Standard test
 *   k6 run tests/load/load_test.js                          # Use built-in stages
 */

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const chatLatency = new Trend('chat_latency');
const wsConnections = new Counter('ws_connections');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const WS_URL = __ENV.WS_URL || 'ws://localhost:8080/ws';

// Test options with ramping stages
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 10 },    // Stay at 10 users
    { duration: '30s', target: 25 },   // Ramp up to 25 users
    { duration: '1m', target: 25 },    // Stay at 25 users
    { duration: '30s', target: 50 },   // Ramp up to 50 users
    { duration: '1m', target: 50 },    // Stay at 50 users
    { duration: '30s', target: 0 },    // Ramp down to 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // 95% of requests under 2s
    http_req_failed: ['rate<0.01'],     // Error rate under 1%
    errors: ['rate<0.05'],              // Custom error rate under 5%
    chat_latency: ['p(95)<5000'],       // Chat responses under 5s
  },
};

// Authentication token (set after login)
let authToken = null;

// Setup function - runs once before test
export function setup() {
  // Check if auth is required
  const authStatus = http.get(`${BASE_URL}/api/auth/status`);
  const status = JSON.parse(authStatus.body);

  if (status.enabled && !status.setup_required) {
    // Login to get token
    const loginRes = http.post(
      `${BASE_URL}/api/auth/login`,
      JSON.stringify({
        username: __ENV.AUTH_USER || 'admin',
        password: __ENV.AUTH_PASS || 'admin123',
      }),
      { headers: { 'Content-Type': 'application/json' } }
    );

    if (loginRes.status === 200) {
      const tokens = JSON.parse(loginRes.body);
      return { token: tokens.access_token };
    }
  }

  return { token: null };
}

// Main test function - runs for each VU
export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (data.token) {
    headers['Authorization'] = `Bearer ${data.token}`;
  }

  // Test groups
  group('Health Checks', function () {
    testHealthEndpoints();
  });

  group('State API', function () {
    testStateAPI(headers);
  });

  group('Chat API', function () {
    testChatAPI(headers);
  });

  group('WebSocket', function () {
    testWebSocket(data.token);
  });

  sleep(1);
}

// Health endpoint tests
function testHealthEndpoints() {
  // Liveness probe
  const liveRes = http.get(`${BASE_URL}/health/live`);
  check(liveRes, {
    'liveness returns 200': (r) => r.status === 200,
    'liveness returns alive': (r) => JSON.parse(r.body).status === 'alive',
  }) || errorRate.add(1);

  // Readiness probe
  const readyRes = http.get(`${BASE_URL}/health/ready`);
  check(readyRes, {
    'readiness returns 200': (r) => r.status === 200,
    'readiness returns ready': (r) => JSON.parse(r.body).status === 'ready',
  }) || errorRate.add(1);

  // Full health check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health returns 200': (r) => r.status === 200,
    'health returns healthy': (r) => JSON.parse(r.body).status === 'healthy',
  }) || errorRate.add(1);

  // Metrics endpoint
  const metricsRes = http.get(`${BASE_URL}/metrics`);
  check(metricsRes, {
    'metrics returns 200': (r) => r.status === 200,
    'metrics contains synth_': (r) => r.body.includes('synth_'),
  }) || errorRate.add(1);
}

// State API tests
function testStateAPI(headers) {
  const stateRes = http.get(`${BASE_URL}/api/state`, { headers });

  const stateOk = check(stateRes, {
    'state returns 200': (r) => r.status === 200,
    'state has valence': (r) => {
      try {
        const body = JSON.parse(r.body);
        return typeof body.valence === 'number';
      } catch {
        return false;
      }
    },
    'state has turn_count': (r) => {
      try {
        const body = JSON.parse(r.body);
        return typeof body.turn_count === 'number';
      } catch {
        return false;
      }
    },
  });

  if (!stateOk) {
    errorRate.add(1);
  }
}

// Chat API tests
function testChatAPI(headers) {
  const messages = [
    'Hello, how are you today?',
    'What can you help me with?',
    'Tell me about your capabilities.',
    'Can you explain flow state?',
    'What is predictive dreaming?',
  ];

  const message = messages[Math.floor(Math.random() * messages.length)];

  const start = Date.now();
  const chatRes = http.post(
    `${BASE_URL}/api/chat`,
    JSON.stringify({ message }),
    { headers, timeout: '30s' }
  );
  const duration = Date.now() - start;

  chatLatency.add(duration);

  const chatOk = check(chatRes, {
    'chat returns 200': (r) => r.status === 200,
    'chat has response': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.success && body.response && body.response.length > 0;
      } catch {
        return false;
      }
    },
    'chat under 10s': (r) => duration < 10000,
  });

  if (!chatOk) {
    errorRate.add(1);
  }
}

// WebSocket tests
function testWebSocket(token) {
  const wsUrl = token ? `${WS_URL}?token=${token}` : WS_URL;

  const res = ws.connect(wsUrl, {}, function (socket) {
    wsConnections.add(1);

    socket.on('open', function () {
      // Request state update
      socket.send(JSON.stringify({ command: 'get_state' }));
    });

    socket.on('message', function (msg) {
      const data = JSON.parse(msg);
      check(data, {
        'ws message has type': (d) => d.type !== undefined,
        'ws state_update has data': (d) =>
          d.type !== 'state_update' || d.data !== undefined,
      });
    });

    socket.on('error', function (e) {
      errorRate.add(1);
    });

    // Keep connection open briefly
    socket.setTimeout(function () {
      socket.close();
    }, 2000);
  });

  check(res, {
    'ws connection successful': (r) => r && r.status === 101,
  }) || errorRate.add(1);
}

// Teardown function - runs once after test
export function teardown(data) {
  // Logout if we have a token
  if (data.token) {
    http.post(
      `${BASE_URL}/api/auth/logout`,
      null,
      {
        headers: {
          'Authorization': `Bearer ${data.token}`,
        },
      }
    );
  }
}
