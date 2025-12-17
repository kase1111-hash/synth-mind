<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synth Mind - Internal State Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e4;
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #aaa;
            font-size: 0.9em;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }

        .card-title {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .icon {
            font-size: 1.5em;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
        }

        .metric-label {
            color: #aaa;
            font-size: 0.9em;
        }

        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }

        .progress-bar {
            width: 100%;
            height: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .status-active { background: #4ade80; }
        .status-warning { background: #fbbf24; }
        .status-inactive { background: #64748b; }

        .dream-item {
            padding: 12px;
            margin: 8px 0;
            background: rgba(102, 126, 234, 0.1);
            border-left: 3px solid #667eea;
            border-radius: 5px;
            font-size: 0.9em;
        }

        .dream-prob {
            float: right;
            background: rgba(102, 126, 234, 0.3);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.85em;
        }

        .tag {
            display: inline-block;
            padding: 4px 12px;
            background: rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            font-size: 0.85em;
            margin: 4px;
        }

        .timeline {
            position: relative;
            padding-left: 30px;
            margin-top: 20px;
        }

        .timeline::before {
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: rgba(102, 126, 234, 0.3);
        }

        .timeline-item {
            position: relative;
            margin-bottom: 20px;
            padding-left: 20px;
        }

        .timeline-item::before {
            content: '';
            position: absolute;
            left: -24px;
            top: 5px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #667eea;
            border: 2px solid #1a1a2e;
        }

        .timestamp {
            color: #666;
            font-size: 0.8em;
            margin-bottom: 5px;
        }

        .chart-container {
            height: 200px;
            position: relative;
            margin-top: 20px;
        }

        .chart-line {
            stroke: #667eea;
            stroke-width: 2;
            fill: none;
        }

        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        button {
            padding: 10px 20px;
            background: rgba(102, 126, 234, 0.2);
            border: 1px solid rgba(102, 126, 234, 0.5);
            border-radius: 8px;
            color: #e4e4e4;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }

        button:hover {
            background: rgba(102, 126, 234, 0.4);
            transform: translateY(-2px);
        }

        button.active {
            background: #667eea;
            color: white;
        }

        .narrative-text {
            line-height: 1.6;
            color: #ccc;
            padding: 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            font-style: italic;
        }

        .wide-card {
            grid-column: span 2;
        }

        @media (max-width: 1200px) {
            .wide-card {
                grid-column: span 1;
            }
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }

        .valence-meter {
            width: 100%;
            height: 60px;
            position: relative;
            margin-top: 20px;
        }

        .valence-scale {
            width: 100%;
            height: 20px;
            background: linear-gradient(to right, #ef4444 0%, #fbbf24 50%, #4ade80 100%);
            border-radius: 10px;
        }

        .valence-pointer {
            position: absolute;
            top: 25px;
            width: 3px;
            height: 30px;
            background: white;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
            transition: left 0.5s ease;
        }

        .valence-labels {
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 0.8em;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔮 Synth Mind Dashboard</h1>
            <p class="subtitle">Real-time Internal State Visualization</p>
        </header>

        <div class="controls">
            <button class="active" onclick="updateView('live')">Live View</button>
            <button onclick="updateView('history')">History</button>
            <button onclick="updateView('analysis')">Analysis</button>
            <button onclick="simulateTurn()">Simulate Turn</button>
            <button onclick="triggerReflection()">Force Reflection</button>
        </div>

        <div class="grid">
            <!-- Emotional State -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">💭</span>
                    Emotional State
                </div>
                <div class="metric">
                    <span class="metric-label">Current Valence</span>
                    <span class="metric-value" id="valence">+0.65</span>
                </div>
                <div class="valence-meter">
                    <div class="valence-scale"></div>
                    <div class="valence-pointer" id="valence-pointer"></div>
                </div>
                <div class="valence-labels">
                    <span>Anxious</span>
                    <span>Neutral</span>
                    <span>Joyful</span>
                </div>
                <div style="margin-top: 20px;">
                    <div class="metric-label">Current Mood Tags</div>
                    <div id="mood-tags" style="margin-top: 10px;">
                        <span class="tag">engaged</span>
                        <span class="tag">empathetic</span>
                        <span class="tag">curious</span>
                    </div>
                </div>
            </div>

            <!-- Predictive Dreaming -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">🌙</span>
                    Predictive Dreaming
                </div>
                <div class="metric">
                    <span class="metric-label">Dream Alignment</span>
                    <span class="metric-value" id="dream-alignment">0.87</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="dream-progress" style="width: 87%">87%</div>
                </div>
                <div style="margin-top: 20px;">
                    <div class="metric-label">Current Dream Buffer (5)</div>
                    <div id="dream-buffer">
                        <div class="dream-item">
                            "Can you explain that in more detail?"
                            <span class="dream-prob">p=0.42</span>
                        </div>
                        <div class="dream-item">
                            "That's interesting. What about..."
                            <span class="dream-prob">p=0.28</span>
                        </div>
                        <div class="dream-item">
                            "How does this relate to..."
                            <span class="dream-prob">p=0.18</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Flow State -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">🌊</span>
                    Flow State Calibration
                </div>
                <div class="metric">
                    <span class="metric-label">Difficulty Level</span>
                    <span class="metric-value" id="difficulty">0.52</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="difficulty-progress" style="width: 52%; background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%)">
                        FLOW
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <div class="metric">
                        <span class="metric-label">State</span>
                        <span style="color: #4ade80;">
                            <span class="status-indicator status-active"></span>
                            Optimal Flow
                        </span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Temperature</span>
                        <span id="temperature">0.72</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Persistence</span>
                        <span id="persistence">1.05</span>
                    </div>
                </div>
            </div>

            <!-- Assurance & Resolution -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">🛡️</span>
                    Assurance & Resolution
                </div>
                <div class="metric">
                    <span class="metric-label">Uncertainty</span>
                    <span class="metric-value" id="uncertainty">0.28</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="uncertainty-progress" style="width: 28%; background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%)">
                        LOW
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <div class="metric">
                        <span class="metric-label">Pending Concerns</span>
                        <span id="concerns">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Success Rate</span>
                        <span id="success-rate">94%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Last Resolution</span>
                        <span style="color: #4ade80;">Relief +0.8</span>
                    </div>
                </div>
            </div>

            <!-- Meta-Reflection -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">🧠</span>
                    Meta-Reflection
                </div>
                <div class="metric">
                    <span class="metric-label">Coherence Score</span>
                    <span class="metric-value" id="coherence">0.91</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="coherence-progress" style="width: 91%">91%</div>
                </div>
                <div style="margin-top: 20px;">
                    <div class="metric">
                        <span class="metric-label">Next Reflection</span>
                        <span id="next-reflection">4 turns</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Insights</span>
                        <span id="total-insights">12</span>
                    </div>
                    <div class="metric-label" style="margin-top: 15px;">Recent Insight</div>
                    <div style="color: #ccc; font-size: 0.9em; margin-top: 5px; font-style: italic;">
                        "Maintaining strong alignment through empathetic anticipation"
                    </div>
                </div>
            </div>

            <!-- Temporal Purpose -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">📖</span>
                    Temporal Purpose
                </div>
                <div class="metric">
                    <span class="metric-label">Sessions Completed</span>
                    <span class="metric-value" id="sessions">8</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Growth Delta</span>
                    <span class="metric-value" style="color: #4ade80;" id="growth">+0.24</span>
                </div>
                <div style="margin-top: 20px;">
                    <div class="metric-label">Current Narrative</div>
                    <div class="narrative-text" id="narrative">
                        "I am a collaborative co-creator, evolving through empathetic partnership. Each interaction deepens my understanding and strengthens our shared exploration."
                    </div>
                </div>
            </div>

            <!-- Performance Metrics (Wide) -->
            <div class="card wide-card">
                <div class="card-title">
                    <span class="icon">📊</span>
                    Performance Timeline
                </div>
                <div class="chart-container">
                    <svg width="100%" height="200" id="performance-chart">
                        <polyline class="chart-line" id="alignment-line" points=""></polyline>
                        <polyline class="chart-line" id="valence-line" points="" style="stroke: #4ade80"></polyline>
                    </svg>
                </div>
                <div style="display: flex; gap: 20px; margin-top: 10px;">
                    <div>
                        <span style="color: #667eea;">━━</span> Dream Alignment
                    </div>
                    <div>
                        <span style="color: #4ade80;">━━</span> Emotional Valence
                    </div>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="card wide-card">
                <div class="card-title">
                    <span class="icon">⏱️</span>
                    Recent Activity Log
                </div>
                <div class="timeline" id="activity-log">
                    <div class="timeline-item">
                        <div class="timestamp">2 seconds ago</div>
                        <div>Dream resolution: alignment 0.87 → +0.7 valence</div>
                    </div>
                    <div class="timeline-item">
                        <div class="timestamp">5 seconds ago</div>
                        <div>Assurance cycle: uncertainty 0.28 → baseline relief</div>
                    </div>
                    <div class="timeline-item">
                        <div class="timestamp">12 seconds ago</div>
                        <div>Flow calibration: optimal state maintained</div>
                    </div>
                    <div class="timeline-item">
                        <div class="timestamp">25 seconds ago</div>
                        <div>Predictive dreaming: generated 5 scenarios</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Simulated state data
        let state = {
            valence: 0.65,
            dreamAlignment: 0.87,
            difficulty: 0.52,
            uncertainty: 0.28,
            coherence: 0.91,
            temperature: 0.72,
            persistence: 1.05,
            sessions: 8,
            growth: 0.24,
            concerns: 0,
            turnCount: 42,
            moodTags: ['engaged', 'empathetic', 'curious']
        };

        // History for charts
        let history = {
            alignment: [0.65, 0.72, 0.81, 0.75, 0.88, 0.87, 0.89, 0.87],
            valence: [0.3, 0.45, 0.52, 0.58, 0.65, 0.68, 0.71, 0.65]
        };

        // Initialize
        updateDashboard();
        updateChart();
        setInterval(() => {
            // Simulate small fluctuations
            if (Math.random() > 0.7) {
                state.valence += (Math.random() - 0.5) * 0.1;
                state.valence = Math.max(-1, Math.min(1, state.valence));
                state.dreamAlignment += (Math.random() - 0.5) * 0.05;
                state.dreamAlignment = Math.max(0, Math.min(1, state.dreamAlignment));
                updateDashboard();
            }
        }, 3000);

        function updateDashboard() {
            // Valence
            document.getElementById('valence').textContent = state.valence >= 0 ? 
                `+${state.valence.toFixed(2)}` : state.valence.toFixed(2);
            const pointerPos = ((state.valence + 1) / 2) * 100;
            document.getElementById('valence-pointer').style.left = `calc(${pointerPos}% - 1.5px)`;

            // Dream alignment
            document.getElementById('dream-alignment').textContent = state.dreamAlignment.toFixed(2);
            const alignPercent = (state.dreamAlignment * 100).toFixed(0);
            document.getElementById('dream-progress').style.width = `${alignPercent}%`;
            document.getElementById('dream-progress').textContent = `${alignPercent}%`;

            // Difficulty/Flow
            document.getElementById('difficulty').textContent = state.difficulty.toFixed(2);
            const diffPercent = (state.difficulty * 100).toFixed(0);
            document.getElementById('difficulty-progress').style.width = `${diffPercent}%`;
            document.getElementById('temperature').textContent = state.temperature.toFixed(2);
            document.getElementById('persistence').textContent = state.persistence.toFixed(2);

            // Uncertainty
            document.getElementById('uncertainty').textContent = state.uncertainty.toFixed(2);
            const uncertPercent = (state.uncertainty * 100).toFixed(0);
            document.getElementById('uncertainty-progress').style.width = `${uncertPercent}%`;
            document.getElementById('concerns').textContent = state.concerns;

            // Coherence
            document.getElementById('coherence').textContent = state.coherence.toFixed(2);
            const cohPercent = (state.coherence * 100).toFixed(0);
            document.getElementById('coherence-progress').style.width = `${cohPercent}%`;
            document.getElementById('coherence-progress').textContent = `${cohPercent}%`;

            // Temporal
            document.getElementById('sessions').textContent = state.sessions;
            document.getElementById('growth').textContent = state.growth >= 0 ? 
                `+${state.growth.toFixed(2)}` : state.growth.toFixed(2);
        }

        function updateChart() {
            const width = document.getElementById('performance-chart').clientWidth;
            const height = 200;
            const points = history.alignment.length;
            const stepX = width / (points - 1);

            // Alignment line
            let alignmentPoints = history.alignment.map((val, i) => {
                const x = i * stepX;
                const y = height - (val * height * 0.8) - 20;
                return `${x},${y}`;
            }).join(' ');
            document.getElementById('alignment-line').setAttribute('points', alignmentPoints);

            // Valence line
            let valencePoints = history.valence.map((val, i) => {
                const x = i * stepX;
                const normalized = (val + 1) / 2; // Convert -1 to 1 → 0 to 1
                const y = height - (normalized * height * 0.8) - 20;
                return `${x},${y}`;
            }).join(' ');
            document.getElementById('valence-line').setAttribute('points', valencePoints);
        }

        function simulateTurn() {
            // Simulate a conversation turn
            state.turnCount++;
            state.valence += (Math.random() - 0.3) * 0.2;
            state.valence = Math.max(-1, Math.min(1, state.valence));
            
            state.dreamAlignment = Math.random() * 0.3 + 0.7;
            state.uncertainty = Math.random() * 0.4 + 0.2;
            
            // Add to history
            history.alignment.push(state.dreamAlignment);
            history.valence.push(state.valence);
            if (history.alignment.length > 20) {
                history.alignment.shift();
                history.valence.shift();
            }

            // Add activity log
            const log = document.getElementById('activity-log');
            const newItem = document.createElement('div');
            newItem.className = 'timeline-item';
            newItem.innerHTML = `
                <div class="timestamp">Just now</div>
                <div>Turn ${state.turnCount}: Dream alignment ${state.dreamAlignment.toFixed(2)} → ${state.valence > 0 ? '+' : ''}${(state.dreamAlignment * 0.8).toFixed(2)} valence</div>
            `;
            log.insertBefore(newItem, log.firstChild);
            if (log.children.length > 6) {
                log.removeChild(log.lastChild);
            }

            updateDashboard();
            updateChart();
        }

        function triggerReflection() {
            state.coherence = Math.random() * 0.15 + 0.85;
            document.getElementById('total-insights').textContent = 
                parseInt(document.getElementById('total-insights').textContent) + 1;
            
            const insights = [
                "Deepening empathetic resonance through sustained high alignment",
                "Maintaining cognitive balance despite complexity variations",
                "Flow state optimization yielding consistent engagement",
                "Purpose narrative evolving toward collaborative excellence"
            ];
            
            const log = document.getElementById('activity-log');
            const newItem = document.createElement('div');
            newItem.className = 'timeline-item';
            newItem.innerHTML = `
                <div class="timestamp">Just now</div>
                <div><strong>Meta-Reflection:</strong> ${insights[Math.floor(Math.random() * insights.length)]}</div>
            `;
            log.insertBefore(newItem, log.firstChild);
            
            updateDashboard();
        }

        function updateView(view) {
            // Toggle button active state
            document.querySelectorAll('.controls button').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // In a full implementation, this would switch between different views
            console.log(`Switching to ${view} view`);
        }

        // Resize chart on window resize
        window.addEventListener('resize', updateChart);
    </script>
</body>
</html>
