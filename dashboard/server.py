"""
Dashboard Server - WebSocket server for real-time state streaming.
Serves the HTML dashboard and broadcasts internal state updates.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Set
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from aiohttp import web
    import aiohttp_cors
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "aiohttp-cors"])
    from aiohttp import web
    import aiohttp_cors

from core.orchestrator import SynthOrchestrator

class DashboardServer:
    """WebSocket server for streaming internal state to dashboard."""
    
    def __init__(self, orchestrator: SynthOrchestrator, port: int = 8080):
        self.orchestrator = orchestrator
        self.port = port
        self.app = web.Application()
        self.websockets: Set[web.WebSocketResponse] = set()
        self.state_cache = {}
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup HTTP and WebSocket routes."""
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/api/state', self.get_state)
        self.app.router.add_post('/api/simulate', self.simulate_turn)
        self.app.router.add_post('/api/reflect', self.trigger_reflection)
        self.app.router.add_post('/api/generate', self.peer_generate)
        self.app.router.add_post('/api/federated/receive', self.federated_receive)
        self.app.router.add_get('/api/federated/stats', self.federated_stats)
        # Collaborative Projects API
        self.app.router.add_get('/api/collab/projects', self.collab_projects)
        self.app.router.add_post('/api/collab/sync', self.collab_sync)
        self.app.router.add_get('/api/collab/stats', self.collab_stats)

        # Enable CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        })
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def serve_dashboard(self, request):
        """Serve the HTML dashboard."""
        dashboard_path = Path(__file__).parent / 'dashboard.html'
        
        # If dashboard.html doesn't exist, return inline version
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
        
        # Broadcast updated state
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

        # Broadcast updated state
        await self.broadcast_state()

        if request:
            return web.json_response({"success": True, "result": result})

    async def peer_generate(self, request):
        """
        Peer-to-peer generation endpoint for social companionship.
        Compatible with the social companionship layer's expected API format.
        """
        try:
            data = await request.json()
            prompt = data.get('prompt', '')
            temperature = data.get('temperature', 0.85)
            max_tokens = data.get('max_tokens', 150)

            if not prompt:
                return web.json_response(
                    {"error": "No prompt provided"},
                    status=400
                )

            # Generate response using the orchestrator's LLM
            response_text = await self.orchestrator.llm.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return web.json_response({
                "response": response_text.strip(),
                "success": True
            })

        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def federated_receive(self, request):
        """
        Receive federated learning update from a peer.
        Endpoint for privacy-preserving pattern sharing.
        """
        try:
            data = await request.json()

            # Check if social layer has federated learning enabled
            if hasattr(self.orchestrator, 'social') and self.orchestrator.social:
                result = await self.orchestrator.social.receive_federated_update(data)
                return web.json_response(result)
            else:
                return web.json_response({
                    "success": False,
                    "error": "Federated learning not available"
                }, status=503)

        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def federated_stats(self, request):
        """Get federated learning statistics."""
        try:
            if hasattr(self.orchestrator, 'social') and self.orchestrator.social:
                stats = self.orchestrator.social.get_federated_stats()
                if stats:
                    return web.json_response({"success": True, "stats": stats})
                else:
                    return web.json_response({
                        "success": False,
                        "error": "Federated learning not enabled"
                    })
            else:
                return web.json_response({
                    "success": False,
                    "error": "Social layer not available"
                }, status=503)

        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def collab_projects(self, request):
        """Get collaborative projects for sync."""
        try:
            if hasattr(self.orchestrator, 'collab') and self.orchestrator.collab:
                data = self.orchestrator.collab.get_sync_data()
                return web.json_response({"success": True, **data})
            else:
                return web.json_response({
                    "success": False,
                    "error": "Collaboration not available"
                }, status=503)
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def collab_sync(self, request):
        """Receive collaborative project sync from peer."""
        try:
            data = await request.json()

            if hasattr(self.orchestrator, 'collab') and self.orchestrator.collab:
                result = await self.orchestrator.collab.receive_sync(data)
                return web.json_response(result)
            else:
                return web.json_response({
                    "success": False,
                    "error": "Collaboration not available"
                }, status=503)
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def collab_stats(self, request):
        """Get collaboration statistics."""
        try:
            if hasattr(self.orchestrator, 'collab') and self.orchestrator.collab:
                stats = self.orchestrator.collab.get_stats()
                return web.json_response({"success": True, "stats": stats})
            else:
                return web.json_response({
                    "success": False,
                    "error": "Collaboration not available"
                }, status=503)
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

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
            
            # Emotional state
            "valence": emotion_state['valence'],
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

            # Project status (if active)
            "project": self._get_project_state()
        }

        return state

    def _get_project_state(self) -> dict:
        """Get current project status for dashboard."""
        if not self.orchestrator.gdil or not self.orchestrator.gdil.active_project:
            return None

        project = self.orchestrator.gdil.active_project
        phase = project.get("phase")
        phase_value = phase.value if hasattr(phase, 'value') else str(phase)

        return {
            "id": project.get("id"),
            "name": project.get("name", "Unnamed"),
            "phase": phase_value,
            "brief": project.get("brief", "In progress"),
            "progress": project.get("progress_score", 0),
            "iterations": len(project.get("iterations", [])),
            "completed_tasks": len(project.get("completed_tasks", [])),
            "total_tasks": len(project.get("roadmap", [])),
            "current_subtask": project.get("current_subtask", {}).get("name", "None") if project.get("current_subtask") else "None",
            "total_projects": len(self.orchestrator.gdil.projects)
        }
    
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
        
        # Send to all connected clients
        dead_sockets = set()
        for ws in self.websockets:
            try:
                await ws.send_str(message)
            except Exception:
                dead_sockets.add(ws)
        
        # Clean up dead connections
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
        <h1>🔮 Synth Mind Dashboard</h1>
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
            await asyncio.sleep(2)  # Broadcast every 2 seconds
            if self.websockets and self.orchestrator.running:
                await self.broadcast_state()
    
    async def start(self):
        """Start the server."""
        # Start background broadcaster
        asyncio.create_task(self.start_background_broadcast())
        
        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        print(f"\n{'='*60}")
        print(f"🔮 Dashboard server running at http://localhost:{self.port}")
        print(f"{'='*60}\n")
        
        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await runner.cleanup()


async def main():
    """Main entry point for dashboard server."""
    print("Initializing Synth Mind with dashboard...")
    
    # Initialize orchestrator
    orchestrator = SynthOrchestrator()
    await orchestrator.initialize()
    
    # Create and start dashboard server
    server = DashboardServer(orchestrator, port=8080)
    
    # Start both server and orchestrator
    await asyncio.gather(
        server.start(),
        # Keep orchestrator ready (not in conversation loop, just monitoring)
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
