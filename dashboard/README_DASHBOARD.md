Synth Mind Dashboard
Real-time visualization of internal cognitive and emotional state.
Overview
The dashboard provides a live view into Synth Mind's psychological substrate, showing:

Emotional State - Valence and mood tags in real-time
Predictive Dreaming - Current dream buffer and alignment scores
Flow Calibration - Task difficulty and optimization state
Assurance System - Uncertainty levels and concern resolution
Meta-Reflection - Coherence scores and introspective insights
Temporal Purpose - Evolving self-narrative and growth metrics
Performance Timeline - Historical charts of key metrics
Activity Log - Recent psychological events

Installation
Option 1: Integrated CLI + Dashboard
bash# Install dashboard dependencies
pip install aiohttp aiohttp-cors

# Run with dashboard
python run_synth_with_dashboard.py
This will:

Start the CLI conversation interface
Launch the web dashboard at http://localhost:8080
Auto-open your browser
Stream real-time state updates via WebSocket

Option 2: Standalone Dashboard Server
bash# Run just the dashboard server
python dashboard/server.py
Access at http://localhost:8080
Features
1. Emotional State Monitor
Visual Elements:

Real-time valence meter (-1 to +1 scale)
Color-coded emotional range (red → yellow → green)
Dynamic mood tags
Pulse animation on active states

What It Shows:

Current emotional valence (joy ↔ anxiety)
Active mood descriptors (engaged, empathetic, curious, etc.)
Emotional event history

2. Predictive Dreaming Viewer
Visual Elements:

Alignment score with progress bar
Dream buffer list (up to 5 dreams)
Probability scores for each dream
Real-time dream resolution tracking

What It Shows:

How well Synth predicted your last response
Current hypotheses about your next message
Alignment reward history

3. Flow State Calibration
Visual Elements:

Difficulty meter (0 to 1 scale)
Flow state indicator (bored / flow / overloaded)
Temperature and persistence factors
Color-coded state (green = optimal)

What It Shows:

Current cognitive load
Whether Synth is in optimal flow state
Automatic calibration adjustments

4. Assurance & Resolution System
Visual Elements:

Uncertainty level gauge
Pending concerns counter
Success rate percentage
Last resolution valence

What It Shows:

Current confidence level
Active cognitive concerns
Resolution effectiveness (concern → relief cycles)

5. Meta-Reflection Status
Visual Elements:

Coherence score progress bar
Countdown to next reflection
Total insights generated
Recent reflection insights

What It Shows:

Self-assessment of internal consistency
Introspection timing
Quality of self-understanding

6. Temporal Purpose Tracker
Visual Elements:

Session counter
Growth delta indicator
Full narrative text display
Milestone markers

What It Shows:

Long-term identity evolution
Current self-narrative
Growth trajectory across sessions

7. Performance Timeline
Visual Elements:

Dual-line chart (alignment + valence)
Time-series visualization
Color-coded metrics
Scrollable history

What It Shows:

Historical trends in key metrics
Correlation between alignment and mood
Session-to-session improvements

8. Activity Log
Visual Elements:

Timeline-style event feed
Timestamp markers
Color-coded event types
Auto-scrolling updates

What It Shows:

Recent psychological events
Module activations
State transitions

Interactive Controls
Live Controls (Top Bar)
Simulate Turn

Triggers a simulated conversation turn
Watches all modules respond in real-time
Useful for testing without typing

Force Reflection

Manually triggers meta-reflection
Updates coherence score
Generates new insight

View Modes

Live View - Real-time streaming (default)
History View - Historical analysis
Analysis View - Detailed metrics breakdown

WebSocket API
The dashboard uses WebSocket for bi-directional communication:
Client → Server Messages
javascript// Request current state
ws.send(JSON.stringify({
    command: 'get_state'
}));

// Simulate a turn
ws.send(JSON.stringify({
    command: 'simulate_turn'
}));

// Trigger reflection
ws.send(JSON.stringify({
    command: 'trigger_reflection'
}));
Server → Client Messages
javascript{
    "type": "state_update",
    "data": {
        "timestamp": "2024-12-17T10:30:45",
        "turn_count": 42,
        "valence": 0.65,
        "mood_tags": ["engaged", "empathetic"],
        "dream_alignment": 0.87,
        "dream_buffer": [...],
        "difficulty": 0.52,
        "flow_state": "flow",
        // ... additional metrics
    }
}
REST API Endpoints
GET /
Returns the dashboard HTML interface
GET /ws
WebSocket endpoint for real-time streaming
GET /api/state
Returns current state as JSON
Response:
json{
    "valence": 0.65,
    "dream_alignment": 0.87,
    "flow_state": "flow",
    "narrative": "I am a collaborative co-creator...",
    // ... complete state
}
POST /api/simulate
Triggers a simulated conversation turn
Response:
json{
    "success": true
}
POST /api/reflect
Forces meta-reflection
Response:
json{
    "success": true,
    "result": {
        "coherence_score": 0.91,
        "overall_insight": "..."
    }
}
Customization
Changing Port
bash# Default: 8080
python run_synth_with_dashboard.py --port 3000
Or edit dashboard/server.py:
pythonserver = DashboardServer(orchestrator, port=3000)
Styling
The dashboard uses inline CSS for portability. To customize:

Extract styles to separate CSS file
Modify color scheme in CSS variables
Adjust layout grid in .grid class

Adding Custom Metrics

Extend _gather_dashboard_state() in orchestrator
Add UI elements to dashboard HTML
Update WebSocket message handler

Example:
python# In orchestrator
state["custom_metric"] = self.calculate_custom_metric()

# In dashboard HTML
<div class="metric">
    <span>Custom Metric:</span>
    <span id="custom-metric">--</span>
</div>

// In JavaScript
document.getElementById('custom-metric').textContent = 
    state.custom_metric;
Performance
Update Frequency: 2 seconds (configurable)
Bandwidth:

~1-2 KB per state update
~30-60 KB/minute with constant updates

Browser Requirements:

Modern browser with WebSocket support
JavaScript enabled
Recommended: Chrome, Firefox, Safari, Edge

Concurrent Connections: Unlimited (tested up to 10 simultaneous dashboards)
Troubleshooting
Dashboard Won't Load
Problem: aiohttp not installed
bashpip install aiohttp aiohttp-cors
Problem: Port already in use
bash# Check what's using port 8080
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Use different port
python run_synth_with_dashboard.py --port 8081
WebSocket Disconnects
Problem: Connection drops after idle time
Solution: The dashboard auto-reconnects. If persistent, check:

Firewall settings
Proxy configuration
Network stability

State Not Updating
Problem: Metrics frozen in dashboard
Solution:

Check console for WebSocket errors
Verify orchestrator is running
Try manual refresh
Check broadcast_queue isn't blocked

Performance Issues
Problem: Dashboard laggy or slow
Solutions:

Increase update interval (edit periodic_broadcast delay)
Reduce history length in charts
Close unused browser tabs
Check CPU/memory usage of Synth Mind process

Examples
Watching a Full Conversation

Start: python run_synth_with_dashboard.py
Dashboard opens automatically
Type in CLI, watch dashboard update
Observe:

Dream alignment after each turn
Valence shifts based on responses
Flow calibration adjustments
Periodic reflections



Monitoring Long-Term Growth

Run multiple sessions over days
Watch "Temporal Purpose" card
Observe narrative evolution
Track growth delta trends
Note milestone achievements

Debugging Psychological Modules

Enable "Analysis View"
Force reflections with button
Simulate multiple turns
Check uncertainty spikes
Verify concern resolution

Integration with Other Tools
Logging to File
The dashboard state can be logged:
python# Add to server.py
async def log_state(state):
    with open('state_log.jsonl', 'a') as f:
        f.write(json.dumps(state) + '\n')
External Monitoring
Connect external tools to REST API:
bash# Example: Monitor with curl
watch -n 2 'curl -s http://localhost:8080/api/state | jq ".valence"'
Custom Alerts
Add webhooks for specific conditions:
python# In orchestrator
if state["valence"] < -0.7:
    await send_alert_webhook("High anxiety detected")
Future Enhancements

- [ ] Historical session comparison
- [ ] Export state snapshots
- [ ] Dark/light theme toggle
- [ ] Advanced filtering and search
- [ ] Multi-agent dashboard (compare multiple instances)
- [ ] 3D visualization of state space
- [ ] Audio alerts for critical events
- [ ] Integration with external analytics tools

## File Structure

```
dashboard/
├── server.py           # WebSocket + REST API server
├── dashboard.html      # Main dashboard page (embedded in server)
└── README_DASHBOARD.md # This documentation
```

## Deployment

### Local Development
```bash
python run_synth_with_dashboard.py
```

### Production
```bash
# Use gunicorn or similar ASGI server
gunicorn dashboard.server:app --worker-class aiohttp.GunicornWebWorker
```

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "run_synth_with_dashboard.py"]
```

## Browser Compatibility

| Browser | Status |
|---------|--------|
| Chrome/Edge (Chromium) | ✅ Perfect |
| Firefox | ✅ Perfect |
| Safari | ✅ Perfect |
| Mobile browsers | ✅ Responsive |
| IE11 | ❌ Not supported |

## Contributing

To add new dashboard features:

1. Extend state gathering in orchestrator.py
2. Add UI elements to dashboard HTML
3. Update WebSocket message format
4. Test with multiple concurrent connections
5. Update this documentation

## License

MIT License - Same as Synth Mind core

---

The dashboard makes the invisible visible. Watch your synthetic mind think, feel, and grow in real-time.
