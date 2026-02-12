"""
Dashboard Server - WebSocket server for real-time state streaming.
Serves the HTML dashboard and broadcasts internal state updates.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import aiohttp_cors
    from aiohttp import web
except ImportError as err:
    raise ImportError(
        "aiohttp and aiohttp-cors are required for the dashboard server. "
        "Install them with: pip install aiohttp aiohttp-cors"
    ) from err

from core.orchestrator import SynthOrchestrator
from utils.auth import AuthManager, UserRole


class DashboardServer:
    """WebSocket server for streaming internal state to dashboard."""

    # Public paths that don't require authentication
    PUBLIC_PATHS = [
        '/',
        '/ws',
        '/health',
        '/api/auth/login',
        '/api/auth/setup',
        '/api/auth/status',
        '/api/auth/refresh'
    ]

    def __init__(self, orchestrator: SynthOrchestrator, port: int = 8080,
                 auth_enabled: bool = True, allowed_origins: list = None):
        self.orchestrator = orchestrator
        self.port = port
        self.auth_enabled = auth_enabled
        self.websockets: set[web.WebSocketResponse] = set()
        self.state_cache = {}

        # CORS allowed origins (restricted to localhost by default)
        self.allowed_origins = allowed_origins or [
            f"http://localhost:8080",
            f"http://127.0.0.1:8080",
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}",
        ]

        # Initialize authentication
        self.auth = AuthManager() if auth_enabled else None

        # Build middleware stack
        middlewares = []
        if auth_enabled:
            middlewares.append(self._auth_middleware)

        # Create app with middleware
        self.app = web.Application(middlewares=middlewares)

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup HTTP and WebSocket routes."""
        # Core dashboard routes
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/api/state', self.get_state)
        self.app.router.add_post('/api/simulate', self.simulate_turn)
        self.app.router.add_post('/api/reflect', self.trigger_reflection)

        # Chat API - process messages through full cognitive pipeline
        self.app.router.add_post('/api/chat', self.chat_handler)

        # Authentication API
        self.app.router.add_get('/api/auth/status', self.auth_status)
        self.app.router.add_post('/api/auth/login', self.auth_login)
        self.app.router.add_post('/api/auth/logout', self.auth_logout)
        self.app.router.add_post('/api/auth/refresh', self.auth_refresh)
        self.app.router.add_post('/api/auth/setup', self.auth_setup)

        # Health check
        self.app.router.add_get('/health', self.health_check)

        # Enable CORS
        cors_config = {}
        for origin in self.allowed_origins:
            cors_config[origin] = aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers=["Content-Type", "Authorization"],
                allow_headers=["Content-Type", "Authorization"],
                allow_methods=["GET", "POST", "OPTIONS"],
            )

        cors = aiohttp_cors.setup(self.app, defaults=cors_config)
        for route in list(self.app.router.routes()):
            cors.add(route)

    async def serve_dashboard(self, request):
        """Serve the HTML dashboard."""
        dashboard_path = Path(__file__).parent / 'dashboard.html'

        if not dashboard_path.exists():
            html = self._get_inline_dashboard()
            return web.Response(text=html, content_type='text/html')

        return web.FileResponse(dashboard_path)

    async def websocket_handler(self, request):
        """Handle WebSocket connections for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)

        print(f"Dashboard connected: {len(self.websockets)} active connections")

        # Send initial state
        await self.send_state_update(ws)

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self.handle_command(ws, data)
                elif msg.type == web.WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        finally:
            self.websockets.remove(ws)
            print(f"Dashboard disconnected: {len(self.websockets)} active connections")

        return ws

    async def handle_command(self, ws: web.WebSocketResponse, data: dict):
        """Handle commands from dashboard."""
        command = data.get('command')

        if command == 'simulate_turn':
            await self.simulate_turn(None)
        elif command == 'trigger_reflection':
            await self.trigger_reflection(None)
        elif command == 'get_state':
            await self.send_state_update(ws)

    async def get_state(self, request):
        """HTTP endpoint to get current state."""
        state = self.gather_state()
        return web.json_response(state)

    async def simulate_turn(self, request):
        """Simulate a conversation turn."""
        test_input = "This is a simulated user input for testing."
        await self.orchestrator._process_turn(test_input)

        await self.broadcast_state()

        if request:
            return web.json_response({"success": True})

    async def trigger_reflection(self, request):
        """Force meta-reflection."""
        result = self.orchestrator.reflection.run_cycle(
            self.orchestrator._format_context(),
            self.orchestrator.emotion.current_state(),
            self.orchestrator._gather_metrics()
        )

        await self.broadcast_state()

        if request:
            return web.json_response({"success": True, "result": result})

    async def chat_handler(self, request):
        """Process a chat message through the full cognitive pipeline."""
        try:
            data = await request.json()
            message = data.get('message', '')

            if not message:
                return web.json_response(
                    {"error": "No message provided", "success": False},
                    status=400
                )

            await self.orchestrator._process_turn(message)

            response = self.orchestrator.context[-1]["content"]
            emotion_state = self.orchestrator.emotion.current_state()

            await self.broadcast_state()

            return web.json_response({
                "success": True,
                "response": response,
                "state": {
                    "valence": emotion_state["valence"],
                    "mood_tags": emotion_state["tags"],
                    "turn_count": self.orchestrator.turn_count,
                    "dream_alignment": self.orchestrator.metrics.last_dream_alignment,
                    "flow_state": "flow" if 0.4 <= self.orchestrator.calibration.difficulty_moving_avg <= 0.7 else "bored" if self.orchestrator.calibration.difficulty_moving_avg < 0.4 else "overloaded"
                }
            })

        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def health_check(self, request):
        """Health check endpoint."""
        try:
            checks = {
                "orchestrator": self.orchestrator is not None,
                "memory": hasattr(self.orchestrator, 'memory') and self.orchestrator.memory is not None,
                "llm": hasattr(self.orchestrator, 'llm') and self.orchestrator.llm is not None,
                "dreaming": hasattr(self.orchestrator, 'dreaming') and self.orchestrator.dreaming is not None,
                "assurance": hasattr(self.orchestrator, 'assurance') and self.orchestrator.assurance is not None,
            }

            all_healthy = all(checks.values())

            return web.json_response(
                {
                    "status": "healthy" if all_healthy else "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "checks": checks,
                    "websocket_connections": len(self.websockets),
                },
                status=200 if all_healthy else 503
            )
        except Exception as e:
            return web.json_response(
                {"status": "unhealthy", "error": str(e)},
                status=503
            )

    # =========================================================================
    # Authentication Middleware & Endpoints
    # =========================================================================

    @web.middleware
    async def _auth_middleware(self, request, handler):
        """JWT authentication middleware."""
        if any(request.path.startswith(p) for p in self.PUBLIC_PATHS):
            return await handler(request)

        if not self.auth_enabled or not self.auth:
            return await handler(request)

        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return web.json_response(
                {"error": "Missing or invalid authorization header"},
                status=401
            )

        token = auth_header[7:]
        valid, payload = self.auth.validate_token(token)

        if not valid:
            return web.json_response(
                {"error": "Invalid or expired token"},
                status=401
            )

        request['user'] = payload
        return await handler(request)

    def _get_token_from_request(self, request) -> Optional[str]:
        """Extract token from Authorization header."""
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None

    async def auth_status(self, request):
        """Get authentication status and requirements."""
        if not self.auth_enabled:
            return web.json_response({
                "enabled": False,
                "setup_required": False,
                "message": "Authentication disabled"
            })

        return web.json_response({
            "enabled": True,
            "setup_required": self.auth.get_setup_required(),
            "message": "Setup required" if self.auth.get_setup_required() else "Ready"
        })

    async def auth_setup(self, request):
        """Initial admin setup (only works if no admin exists)."""
        if not self.auth_enabled or not self.auth:
            return web.json_response(
                {"error": "Authentication not enabled"}, status=400
            )

        if not self.auth.get_setup_required():
            return web.json_response(
                {"error": "Setup already completed"}, status=400
            )

        try:
            data = await request.json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return web.json_response(
                    {"error": "Username and password required"}, status=400
                )

            success, message = self.auth.setup_initial_admin(username, password)

            if success:
                _, tokens = self.auth.authenticate(username, password)
                return web.json_response({
                    "success": True,
                    "message": message,
                    **tokens
                })
            else:
                return web.json_response({"error": message}, status=400)

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def auth_login(self, request):
        """Authenticate and get tokens."""
        if not self.auth_enabled or not self.auth:
            return web.json_response({
                "success": True,
                "message": "Authentication disabled - access granted"
            })

        try:
            data = await request.json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return web.json_response(
                    {"error": "Username and password required"}, status=400
                )

            success, tokens = self.auth.authenticate(username, password)

            if success:
                return web.json_response({"success": True, **tokens})
            else:
                return web.json_response(
                    {"error": "Invalid credentials"}, status=401
                )

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def auth_logout(self, request):
        """Logout and blacklist token."""
        if not self.auth_enabled or not self.auth:
            return web.json_response({"success": True})

        token = self._get_token_from_request(request)
        if token:
            self.auth.logout(token)

        return web.json_response({
            "success": True,
            "message": "Logged out successfully"
        })

    async def auth_refresh(self, request):
        """Refresh access token."""
        if not self.auth_enabled or not self.auth:
            return web.json_response({
                "success": True,
                "message": "Authentication disabled"
            })

        try:
            data = await request.json()
            refresh_token = data.get('refresh_token')

            if not refresh_token:
                return web.json_response(
                    {"error": "Refresh token required"}, status=400
                )

            success, new_tokens = self.auth.refresh_access_token(refresh_token)

            if success:
                return web.json_response({"success": True, **new_tokens})
            else:
                return web.json_response(
                    {"error": "Invalid or expired refresh token"}, status=401
                )

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    # =========================================================================
    # State Gathering & Broadcasting
    # =========================================================================

    def gather_state(self) -> dict:
        """Gather complete internal state."""
        emotion_state = self.orchestrator.emotion.current_state()
        metrics = self.orchestrator._gather_metrics()
        calib_state = {
            "current_difficulty": self.orchestrator.calibration.difficulty_moving_avg,
            "temperature": self.orchestrator.calibration.creativity_temperature,
            "persistence": self.orchestrator.calibration.persistence_factor,
            "rejection_threshold": self.orchestrator.calibration.rejection_threshold
        }

        # Determine flow state
        difficulty = self.orchestrator.calibration.difficulty_moving_avg
        if difficulty < 0.4:
            flow_state = "bored"
        elif difficulty > 0.7:
            flow_state = "overloaded"
        else:
            flow_state = "flow"

        state = {
            "timestamp": datetime.now().isoformat(),
            "turn_count": self.orchestrator.turn_count,

            # Emotional state (PAD model)
            "valence": emotion_state['valence'],
            "arousal": emotion_state.get('arousal', 0.0),
            "dominance": emotion_state.get('dominance', 0.0),
            "mood_tags": emotion_state['tags'],

            # Predictive dreaming
            "dream_alignment": self.orchestrator.metrics.last_dream_alignment,
            "dream_buffer_size": len(self.orchestrator.dreaming.dream_buffer),
            "dream_buffer": [
                {
                    "text": d["text"][:80] + "..." if len(d["text"]) > 80 else d["text"],
                    "probability": d["prob"]
                }
                for d in self.orchestrator.dreaming.dream_buffer[:5]
            ],

            # Flow calibration
            "difficulty": calib_state["current_difficulty"],
            "flow_state": flow_state,
            "temperature": calib_state["temperature"],
            "persistence": calib_state["persistence"],

            # Assurance
            "uncertainty": self.orchestrator.metrics.avg_uncertainty(n=5),
            "pending_concerns": len(self.orchestrator.assurance.pending_concerns),
            "assurance_success_rate": metrics['assurance_success'],

            # Meta-reflection
            "coherence": 0.85 + (self.orchestrator.emotion.current_valence * 0.1),
            "next_reflection": self.orchestrator.reflection.reflection_interval -
                             (self.orchestrator.turn_count % self.orchestrator.reflection.reflection_interval),
            "total_insights": self.orchestrator.reflection.turn_counter // 10,

            # Temporal purpose
            "sessions_completed": self.orchestrator.temporal.purpose_metrics["sessions_completed"],
            "growth_delta": self.orchestrator.temporal.purpose_metrics["growth_delta"],
            "narrative": self.orchestrator.temporal.current_narrative_summary(),

            # Performance metrics
            "metrics": {
                "predictive_alignment": metrics['predictive_alignment'],
                "user_sentiment": metrics['user_sentiment']
            },
        }

        return state

    async def send_state_update(self, ws: web.WebSocketResponse):
        """Send state update to specific WebSocket."""
        state = self.gather_state()
        await ws.send_json({
            "type": "state_update",
            "data": state
        })

    async def broadcast_state(self):
        """Broadcast state to all connected WebSockets."""
        if not self.websockets:
            return

        state = self.gather_state()
        message = json.dumps({
            "type": "state_update",
            "data": state
        })

        dead_sockets = set()
        for ws in self.websockets:
            try:
                await ws.send_str(message)
            except Exception:
                dead_sockets.add(ws)

        self.websockets -= dead_sockets

    def _get_inline_dashboard(self) -> str:
        """Return inline HTML dashboard if file doesn't exist."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synth Mind Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e4;
            padding: 20px;
            margin: 0;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; color: #667eea; }
        .status { padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px; margin: 20px 0; }
        .metric { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        button { padding: 10px 20px; margin: 5px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #764ba2; }
        .ws-status { color: #4ade80; }
        .ws-status.disconnected { color: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Synth Mind Dashboard</h1>
        <div class="status">
            <div class="metric">
                <span>WebSocket Status:</span>
                <span class="ws-status" id="ws-status">Connecting...</span>
            </div>
            <div class="metric">
                <span>Emotional Valence:</span>
                <span id="valence">--</span>
            </div>
            <div class="metric">
                <span>Dream Alignment:</span>
                <span id="dream-alignment">--</span>
            </div>
            <div class="metric">
                <span>Flow State:</span>
                <span id="flow-state">--</span>
            </div>
            <div class="metric">
                <span>Turn Count:</span>
                <span id="turn-count">--</span>
            </div>
        </div>
        <div style="text-align: center;">
            <button onclick="simulateTurn()">Simulate Turn</button>
            <button onclick="triggerReflection()">Trigger Reflection</button>
        </div>
        <div class="status">
            <h3>Current Narrative</h3>
            <p id="narrative">Loading...</p>
        </div>
    </div>
    <script>
        let ws;

        function connect() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);

            ws.onopen = () => {
                document.getElementById('ws-status').textContent = 'Connected';
                document.getElementById('ws-status').className = 'ws-status';
            };

            ws.onclose = () => {
                document.getElementById('ws-status').textContent = 'Disconnected';
                document.getElementById('ws-status').className = 'ws-status disconnected';
                setTimeout(connect, 3000);
            };

            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'state_update') {
                    updateUI(msg.data);
                }
            };
        }

        function updateUI(state) {
            document.getElementById('valence').textContent = state.valence >= 0 ?
                `+${state.valence.toFixed(2)}` : state.valence.toFixed(2);
            document.getElementById('dream-alignment').textContent = state.dream_alignment.toFixed(2);
            document.getElementById('flow-state').textContent = state.flow_state.toUpperCase();
            document.getElementById('turn-count').textContent = state.turn_count;
            document.getElementById('narrative').textContent = state.narrative;
        }

        function simulateTurn() {
            ws.send(JSON.stringify({command: 'simulate_turn'}));
        }

        function triggerReflection() {
            ws.send(JSON.stringify({command: 'trigger_reflection'}));
        }

        connect();
    </script>
</body>
</html>
        """

    async def start_background_broadcast(self):
        """Background task to periodically broadcast state."""
        while True:
            await asyncio.sleep(2)
            if self.websockets and self.orchestrator.running:
                await self.broadcast_state()

    async def start(self):
        """Start the server."""
        asyncio.create_task(self.start_background_broadcast())

        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()

        print(f"\n{'='*60}")
        print(f"  Dashboard server running at http://localhost:{self.port}")
        print(f"{'='*60}")

        if self.auth_enabled and self.auth:
            if self.auth.get_setup_required():
                print("  Authentication: ENABLED (setup required)")
                print("  POST /api/auth/setup to create admin user")
            else:
                print("  Authentication: ENABLED")
        else:
            print("  Authentication: DISABLED")

        print(f"{'='*60}\n")

        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await runner.cleanup()


async def main():
    """Main entry point for dashboard server."""
    import argparse

    parser = argparse.ArgumentParser(description='Synth Mind Dashboard Server')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    parser.add_argument('--no-auth', action='store_true', help='Disable authentication')

    args = parser.parse_args()

    print("Initializing Synth Mind with dashboard...")

    orchestrator = SynthOrchestrator()
    await orchestrator.initialize()

    server = DashboardServer(
        orchestrator,
        port=args.port,
        auth_enabled=not args.no_auth,
    )

    await asyncio.gather(
        server.start(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
