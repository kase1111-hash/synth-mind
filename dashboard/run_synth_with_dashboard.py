#!/usr/bin/env python3
"""
Synth Mind with Dashboard
Runs both CLI interface and web dashboard simultaneously.
"""

import asyncio
import os
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import SynthOrchestrator
from utils.logging import setup_logging
from utils.ollama_setup import prompt_ollama_setup

# Import dashboard server
try:
    from aiohttp import web
    import aiohttp_cors
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("⚠️  Dashboard dependencies not installed. Install with:")
    print("   pip install aiohttp aiohttp-cors")


class DashboardIntegratedOrchestrator(SynthOrchestrator):
    """Orchestrator with dashboard broadcasting."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dashboard_clients = set()
        self.broadcast_queue = asyncio.Queue()
    
    async def _process_turn(self, user_input: str):
        """Override to broadcast state after each turn."""
        await super()._process_turn(user_input)
        # Trigger broadcast
        await self.broadcast_state()
    
    async def broadcast_state(self):
        """Put state update in queue for dashboard clients."""
        if self.dashboard_clients:
            state = self._gather_dashboard_state()
            await self.broadcast_queue.put(state)
    
    def _gather_dashboard_state(self) -> dict:
        """Gather state for dashboard."""
        from datetime import datetime
        
        emotion_state = self.emotion.current_state()
        metrics = self._gather_metrics()
        
        difficulty = self.calibration.difficulty_moving_avg
        if difficulty < 0.4:
            flow_state = "bored"
        elif difficulty > 0.7:
            flow_state = "overloaded"
        else:
            flow_state = "flow"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "turn_count": self.turn_count,
            "valence": emotion_state['valence'],
            "mood_tags": emotion_state['tags'],
            "dream_alignment": self.metrics.last_dream_alignment,
            "dream_buffer_size": len(self.dreaming.dream_buffer),
            "dream_buffer": [
                {
                    "text": d["text"][:80] + "..." if len(d["text"]) > 80 else d["text"],
                    "probability": d["prob"]
                }
                for d in self.dreaming.dream_buffer[:5]
            ],
            "difficulty": difficulty,
            "flow_state": flow_state,
            "temperature": self.calibration.creativity_temperature,
            "persistence": self.calibration.persistence_factor,
            "uncertainty": self.metrics.avg_uncertainty(n=5),
            "pending_concerns": len(self.assurance.pending_concerns),
            "assurance_success_rate": metrics['assurance_success'],
            "coherence": 0.85 + (self.emotion.current_valence * 0.1),
            "next_reflection": self.reflection.reflection_interval - 
                             (self.turn_count % self.reflection.reflection_interval),
            "total_insights": self.reflection.turn_counter // 10,
            "sessions_completed": self.temporal.purpose_metrics["sessions_completed"],
            "growth_delta": self.temporal.purpose_metrics["growth_delta"],
            "narrative": self.temporal.current_narrative_summary(),
            "metrics": {
                "predictive_alignment": metrics['predictive_alignment'],
                "user_sentiment": metrics['user_sentiment']
            }
        }


async def start_dashboard_server(orchestrator: DashboardIntegratedOrchestrator, port: int = 8080):
    """Start the dashboard web server."""
    if not DASHBOARD_AVAILABLE:
        return
    
    app = web.Application()
    
    # Serve static HTML
    async def serve_dashboard(request):
        dashboard_path = Path(__file__).parent / 'dashboard' / 'dashboard.html'
        if dashboard_path.exists():
            return web.FileResponse(dashboard_path)
        
        # Return inline minimal version
        html = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Synth Mind Dashboard</title>
<style>
body{font-family:system-ui;background:#1a1a2e;color:#e4e4e4;padding:20px;margin:0}
.container{max-width:1200px;margin:0 auto}
h1{text-align:center;color:#667eea}
.card{background:rgba(255,255,255,0.05);border-radius:10px;padding:20px;margin:20px 0;border:1px solid rgba(255,255,255,0.1)}
.metric{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05)}
.value{color:#667eea;font-weight:bold}
button{padding:10px 20px;margin:5px;background:#667eea;color:white;border:none;border-radius:5px;cursor:pointer}
button:hover{background:#764ba2}
.status{color:#4ade80}
.tag{display:inline-block;padding:4px 12px;background:rgba(102,126,234,0.2);border-radius:12px;margin:2px;font-size:0.9em}
</style></head><body>
<div class="container">
<h1>🔮 Synth Mind Dashboard</h1>
<div class="card">
<h3>Connection: <span class="status" id="status">Connecting...</span></h3>
<div class="metric"><span>Turn Count:</span><span class="value" id="turns">--</span></div>
<div class="metric"><span>Emotional Valence:</span><span class="value" id="valence">--</span></div>
<div class="metric"><span>Dream Alignment:</span><span class="value" id="alignment">--</span></div>
<div class="metric"><span>Flow State:</span><span class="value" id="flow">--</span></div>
<div class="metric"><span>Mood:</span><span id="mood">--</span></div>
</div>
<div class="card">
<h3>Current Narrative</h3>
<p id="narrative" style="line-height:1.6;color:#ccc">Loading...</p>
</div>
<div class="card">
<h3>Dream Buffer (<span id="dream-count">0</span>)</h3>
<div id="dreams"></div>
</div>
</div>
<script>
let ws=new WebSocket(`ws://${window.location.host}/ws`);
ws.onopen=()=>document.getElementById('status').textContent='Connected ✓';
ws.onclose=()=>{document.getElementById('status').textContent='Disconnected';setTimeout(()=>location.reload(),3000)};
ws.onmessage=(e)=>{
const d=JSON.parse(e.data);
if(d.type==='state'){
document.getElementById('turns').textContent=d.turn_count;
document.getElementById('valence').textContent=(d.valence>=0?'+':'')+d.valence.toFixed(2);
document.getElementById('alignment').textContent=d.dream_alignment.toFixed(2);
document.getElementById('flow').textContent=d.flow_state.toUpperCase();
document.getElementById('narrative').textContent=d.narrative;
document.getElementById('mood').innerHTML=d.mood_tags.map(t=>`<span class="tag">${t}</span>`).join('');
document.getElementById('dream-count').textContent=d.dream_buffer_size;
document.getElementById('dreams').innerHTML=d.dream_buffer.map(dr=>
`<div style="padding:8px;margin:5px 0;background:rgba(102,126,234,0.1);border-left:3px solid #667eea;border-radius:3px;font-size:0.9em">
${dr.text}<span style="float:right;background:rgba(102,126,234,0.3);padding:2px 8px;border-radius:10px;font-size:0.85em">p=${dr.probability.toFixed(2)}</span>
</div>`).join('');
}
};
</script>
</body></html>
        """
        return web.Response(text=html, content_type='text/html')
    
    # WebSocket handler
    async def websocket_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        orchestrator.dashboard_clients.add(ws)
        
        print(f"📊 Dashboard connected ({len(orchestrator.dashboard_clients)} clients)")
        
        # Send initial state
        state = orchestrator._gather_dashboard_state()
        await ws.send_json({"type": "state", **state})
        
        # Listen for broadcasts
        try:
            while True:
                # Wait for state update
                state = await orchestrator.broadcast_queue.get()
                await ws.send_json({"type": "state", **state})
        except Exception as e:
            print(f"Dashboard error: {e}")
        finally:
            orchestrator.dashboard_clients.remove(ws)
            print(f"📊 Dashboard disconnected ({len(orchestrator.dashboard_clients)} clients)")
        
        return ws
    
    app.router.add_get('/', serve_dashboard)
    app.router.add_get('/ws', websocket_handler)
    
    # Enable CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    for route in list(app.router.routes()):
        cors.add(route)
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    
    print(f"\n{'='*60}")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"{'='*60}\n")
    
    # Auto-open browser
    try:
        webbrowser.open(f'http://localhost:{port}')
    except:
        pass
    
    # Keep running
    await asyncio.Event().wait()


async def periodic_broadcast(orchestrator: DashboardIntegratedOrchestrator):
    """Periodically broadcast state to dashboard even when idle."""
    while True:
        await asyncio.sleep(2)
        if orchestrator.dashboard_clients:
            await orchestrator.broadcast_state()


def print_banner():
    """Display startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║                  SYNTH MIND + DASHBOARD                   ║
    ║                                                           ║
    ║        Chat here + Watch internal state in browser        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Commands:
      /state           - View internal state
      /reflect         - Trigger meta-reflection
      /dream           - Show dream buffer
      /purpose         - Display self-narrative
      /project [desc]  - Start systematic project (GDIL)
      /project status  - View active project progress
      /resume project  - Resume paused project
      /reset           - Clear session (keeps long-term identity)
      /quit            - Save and exit
    
    """
    print(banner)


async def main():
    """Main entry point."""
    setup_logging()
    print_banner()

    # Initialize orchestrator
    try:
        orchestrator = DashboardIntegratedOrchestrator()
        await orchestrator.initialize()
    except ValueError as e:
        # Check if it's the "No LLM provider" error
        if "No LLM provider configured" in str(e):
            # Offer to set up Ollama
            success, model_name = prompt_ollama_setup()

            if success and model_name:
                # Set environment variable and retry
                os.environ["OLLAMA_MODEL"] = model_name
                print(f"\n✅ Using Ollama with model: {model_name}")
                print("Restarting Synth Mind...\n")

                try:
                    orchestrator = DashboardIntegratedOrchestrator()
                    await orchestrator.initialize()
                except Exception as retry_error:
                    print(f"❌ Failed to initialize after setup: {retry_error}")
                    sys.exit(1)
            else:
                print("\n❌ Cannot start without LLM provider.")
                print("\nOptions:")
                print("  1. Set API key: export ANTHROPIC_API_KEY='your-key'")
                print("  2. Set API key: export OPENAI_API_KEY='your-key'")
                print("  3. Install Ollama: https://ollama.com")
                sys.exit(1)
        else:
            print(f"❌ Failed to initialize: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    # Start dashboard server if available
    if DASHBOARD_AVAILABLE:
        dashboard_task = asyncio.create_task(start_dashboard_server(orchestrator))
        broadcast_task = asyncio.create_task(periodic_broadcast(orchestrator))
        # Give server time to start
        await asyncio.sleep(1)
    else:
        print("⚠️  Running without dashboard\n")
    
    print("✓ Synth is online. Type your message or a command.\n")
    
    # Main conversation loop
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        print("\n\nGracefully shutting down...")
    finally:
        await orchestrator.shutdown()
        print("Synth has been saved. Until next time, co-creator.")


if __name__ == "__main__":
    asyncio.run(main())
