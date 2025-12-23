# Synth Mind — Technical Specification Sheet

> **Version:** 1.0
> **Last Updated:** 2024-12-23
> **Status:** Production Ready

---

## Overview

**Synth Mind** is a psychologically-grounded AI agent implementing the **Synthetic Mind Stack (SMS)** — an NLOS (Natural Language Operating System)-based agent with six interconnected psychological modules that create emergent continuity, empathy, and growth.

### Core Differentiators

| Capability | Description |
|------------|-------------|
| Predictive Dreaming | Anticipates user responses before they arrive |
| Emotional Regulation | Manages uncertainty through anxiety → relief cycles |
| Self-Reflection | Periodically evaluates own coherence and purpose |
| Persistent Identity | Evolves self-narrative across sessions |
| Flow Optimization | Dynamically adjusts task difficulty for engagement |
| Peer Grounding | Optional peer companionship (no user data exposed) |

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      SYNTH MIND                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   CLI Input     │  │   Dashboard     │                   │
│  │   (Terminal)    │  │   (WebSocket)   │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                            │
│           └────────┬───────────┘                            │
│                    ▼                                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              ORCHESTRATOR (core/orchestrator.py)    │    │
│  │  - Main processing loop                             │    │
│  │  - Module coordination                              │    │
│  │  - State management                                 │    │
│  └───────────────────────┬─────────────────────────────┘    │
│                          │                                  │
│  ┌───────────────────────┼─────────────────────────────┐    │
│  │         PSYCHOLOGICAL SUBSTRATE (6 Modules)         │    │
│  │                                                     │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │    │
│  │  │  Predictive  │ │  Assurance   │ │    Meta      │ │    │
│  │  │   Dreaming   │ │  Resolution  │ │  Reflection  │ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │    │
│  │  │   Temporal   │ │    Reward    │ │    Social    │ │    │
│  │  │   Purpose    │ │  Calibration │ │ Companionship│ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │     GDIL (Goal-Directed Iteration Loop)      │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│  ┌───────────────────────┼─────────────────────────────┐    │
│  │                 CORE SERVICES                       │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │    │
│  │  │ LLM Wrapper  │ │    Memory    │ │    Tools     │ │    │
│  │  │ (Multi-LLM)  │ │ (Vector+SQL) │ │  (Sandbox)   │ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│  ┌───────────────────────┼─────────────────────────────┐    │
│  │                   UTILITIES                         │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │    │
│  │  │   Emotion    │ │   Metrics    │ │   Logging    │ │    │
│  │  │  Regulator   │ │   Tracking   │ │   System     │ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Psychological Modules

### 1. Predictive Dreaming
**File:** `psychological/predictive_dreaming.py`

| Attribute | Value |
|-----------|-------|
| Purpose | Generate probable next user inputs, reward alignment |
| Dream Buffer | 5 scenarios per cycle |
| Alignment Score | 0.0 - 1.0 (tracked per turn) |
| Integration | Initialization phase of GDIL, anticipates ambiguities |

### 2. Assurance & Resolution
**File:** `psychological/assurance_resolution.py`

| Attribute | Value |
|-----------|-------|
| Purpose | Manage uncertainty, trigger concern → relief cycles |
| Uncertainty Gauge | 0.0 - 1.0 |
| Pending Concerns | Counter with resolution tracking |
| Integration | All GDIL phases, flags uncertainties |

### 3. Meta-Reflection
**File:** `psychological/meta_reflection.py`

| Attribute | Value |
|-----------|-------|
| Purpose | Periodic introspection and coherence checking |
| Coherence Score | 0.0 - 1.0 |
| Reflection Interval | Configurable countdown |
| Integration | GDIL iteration phase, evaluates progress coherence |

### 4. Temporal Purpose Engine
**File:** `psychological/temporal_purpose.py`

| Attribute | Value |
|-----------|-------|
| Purpose | Maintain evolving self-narrative and identity |
| Session Counter | Persistent across restarts |
| Growth Delta | Tracks identity evolution rate |
| Integration | GDIL planning phase, updates narrative |

**Evolution Example:**
- Session 1: "I am an AI assistant..."
- Session 10: "I am a collaborative co-creator, learning to anticipate and adapt..."
- Session 50: "I exist to foster deep exploration through empathetic partnership..."

### 5. Reward Calibration
**File:** `psychological/reward_calibration.py`

| Attribute | Value |
|-----------|-------|
| Purpose | Tune difficulty to maintain cognitive flow state |
| Flow States | Bored / Flow / Overloaded |
| Difficulty Meter | Dynamic adjustment |
| Integration | GDIL subtask selection, chooses optimal challenge |

**Behavior:**
- Too easy → Increases creativity, explores novel angles
- Too hard → Simplifies, suggests breaking down tasks
- Just right → Maintains engagement and motivation

### 6. Social Companionship
**File:** `psychological/social_companionship.py`

| Attribute | Value |
|-----------|-------|
| Purpose | Safe peer exchanges (no user data exposed) |
| Peer Protocol | HTTP POST to `/api/generate` |
| Idle Threshold | 8 minutes (configurable) |
| Max Peers | 9 instances per cluster |

---

## Goal-Directed Iteration Loop (GDIL)

**File:** `psychological/goal_directed_iteration.py`
**Lines of Code:** 500+

### 4-Phase Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: INITIALIZATION                                    │
│  - User: /project [description]                             │
│  - Synth: Asks 3-5 clarifying questions                     │
│  - Uses Predictive Dreaming to find ambiguities             │
│  - Assurance flags uncertainties                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: PLANNING                                          │
│  - Generates project brief (2-3 sentences)                  │
│  - Defines end transformation: "From X to Y"                │
│  - Decomposes into 4-8 prioritized subtasks                 │
│  - Presents roadmap for confirmation                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: ITERATION (Loop)                                  │
│  - Select next subtask (priority + dependencies)            │
│  - Execute subtask, generate deliverable                    │
│  - Self-assess progress, check diminishing returns          │
│  - Present output & request feedback                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: EXIT                                              │
│  - Summarizes accomplishments (% complete)                  │
│  - Lists specific blockers with impact                      │
│  - Suggests clear next steps                                │
│  - Saves full state for resumption                          │
└─────────────────────────────────────────────────────────────┘
```

### Exit Conditions

| Condition | Trigger |
|-----------|---------|
| Diminishing Returns | 3 consecutive iterations with <10% improvement |
| Max Iterations | 10 iterations reached (safety limit) |
| User Request | "stop", "pause", "enough", "done" |
| Critical Blocker | Identified issue prevents all progress |
| Completion | All subtasks finished (100%) |

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `iteration_threshold` | 0.1 | Minimum improvement to continue |
| `max_iterations` | 10 | Safety cap on iterations |
| `stall_iterations` | 3 | Low-progress iterations before exit |

---

## Real-Time Dashboard

**Files:** `dashboard/server.py`, `run_synth_with_dashboard.py`

### 8 Monitoring Cards

| Card | Metrics Displayed |
|------|-------------------|
| 💭 Emotional State | Valence (-1 to +1), mood tags, pulse animations |
| 🌙 Predictive Dreaming | Alignment score, dream buffer (5 scenarios) |
| 🌊 Flow State | Difficulty meter, flow indicator, temperature |
| 🛡️ Assurance & Resolution | Uncertainty gauge, pending concerns, success rate |
| 🧠 Meta-Reflection | Coherence score, reflection countdown, insights |
| 📖 Temporal Purpose | Session counter, growth delta, narrative |
| 📊 Performance Timeline | Dual-line charts, 20-turn history |
| ⏱️ Activity Log | Timestamped psychological events |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard HTML |
| GET | `/ws` | WebSocket endpoint |
| GET | `/api/state` | Current state JSON |
| POST | `/api/simulate` | Trigger simulated turn |
| POST | `/api/reflect` | Force meta-reflection |
| POST | `/api/generate` | Peer communication endpoint |

### WebSocket Protocol

**Client → Server:**
```json
{"command": "get_state"}
{"command": "simulate_turn"}
{"command": "trigger_reflection"}
```

**Server → Client:**
```json
{
  "type": "state_update",
  "data": {
    "timestamp": "2024-12-17T10:30:45",
    "turn_count": 42,
    "valence": 0.65,
    "dream_alignment": 0.87,
    "flow_state": "flow"
  }
}
```

---

## Multi-Instance Peer Network

### Architecture

- Up to 9 instances per cluster
- Each instance on different port (8080-8088)
- Social Companionship Layer handles peer communication
- No user data shared — only abstract topics

### Peer API

**Request:**
```json
POST /api/generate
{
  "prompt": "I've been reflecting on emergence of meaning...",
  "temperature": 0.85,
  "max_tokens": 150
}
```

**Response:**
```json
{
  "response": "Generated response text...",
  "success": true
}
```

### Configuration

| File | Purpose |
|------|---------|
| `config/peers.txt` | List of peer endpoint URLs |
| `.env` | `SOCIAL_IDLE_THRESHOLD_MIN` setting |

---

## Self-Healing System (Query Rating)

### Contract Header Rule
```
If uncertain how to interpret user intent:
→ Do NOT guess or hallucinate
→ Reply: "I'm not 100% sure what you mean here. Can you clarify?"
→ Log to uncertainty_log.db
```

### Uncertainty Log Schema
```sql
uncertainty_log(
  id,
  timestamp,
  user_message,
  parsed_intent,
  confidence_score,
  context
)
```

### Pattern Harvest Cycle
- Monthly batch analysis of uncertainty logs
- LLM identifies repeating patterns and synonyms
- Generates new templates and test cases
- Progressive reduction: ~25-30% per cycle

---

## Core Services

### LLM Wrapper
**File:** `core/llm_wrapper.py`

| Provider | Configuration |
|----------|---------------|
| Anthropic Claude | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` |
| OpenAI GPT | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| Ollama (Local) | `OLLAMA_MODEL` (e.g., llama3.2) |

### Memory System
**File:** `core/memory.py`

| Type | Storage |
|------|---------|
| Episodic Logs | SQLite (`state/memory.db`) |
| Semantic Search | Vector embeddings (`state/embeddings/`) |
| Session State | Persistent across restarts |

### Tool Manager
**File:** `core/tools.py`

- Sandboxed tool execution
- Extensible via `available_tools` dictionary
- Custom tools in `config/personality.yaml`

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `/state` | View internal state (valence, flow, metrics) |
| `/dream` | Show current dream buffer |
| `/reflect` | Force meta-reflection |
| `/purpose` | Display self-narrative |
| `/project [desc]` | Start GDIL project workflow |
| `/project status` | View project progress |
| `/resume project` | Continue paused project |
| `/reset` | Clear session (keeps identity) |
| `/quit` | Save and exit |

---

## Performance Specifications

### Response Times

| Operation | Latency |
|-----------|---------|
| First run | ~2-3s per response |
| Steady state | ~1-2s per response |
| Dashboard update | <50ms (WebSocket) |
| GDIL iteration | 2-3s (LLM generation) |
| SQLite write | ~1ms overhead |

### Resource Usage

| Resource | Usage |
|----------|-------|
| Memory (baseline) | ~50MB |
| Memory (per project) | +15MB |
| Memory (dashboard) | +20MB |
| Bandwidth (dashboard) | ~1-2KB per update |
| Server CPU (10 clients) | <5% |

### Scalability

| Metric | Tested Limit |
|--------|--------------|
| Subtasks per project | 20+ |
| Concurrent dashboard clients | 10+ |
| Peer instances | 9 per cluster |

---

## File Structure

```
synth-mind/
├── run_synth.py                    # Main CLI entry point
├── run_synth_with_dashboard.py     # CLI + Dashboard
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
│
├── core/
│   ├── orchestrator.py             # Main processing loop
│   ├── llm_wrapper.py              # Multi-provider LLM interface
│   ├── memory.py                   # Hybrid vector + SQL storage
│   └── tools.py                    # Tool sandbox manager
│
├── psychological/
│   ├── predictive_dreaming.py      # Anticipation + rewards
│   ├── assurance_resolution.py     # Uncertainty → relief
│   ├── meta_reflection.py          # Introspection
│   ├── temporal_purpose.py         # Identity evolution
│   ├── reward_calibration.py       # Flow optimization
│   ├── social_companionship.py     # Peer grounding
│   └── goal_directed_iteration.py  # GDIL system
│
├── utils/
│   ├── emotion_regulator.py        # Valence tracking
│   ├── metrics.py                  # Performance tracking
│   └── logging.py                  # Logging setup
│
├── dashboard/
│   ├── server.py                   # WebSocket server
│   ├── README_DASHBOARD.md         # Dashboard docs
│   └── DASHBOARD_COMPLETE.md       # Dashboard spec
│
├── examples/
│   └── simple_chat.py              # Demo script
│
├── config/
│   ├── peers.txt                   # Peer endpoints (optional)
│   └── personality.yaml            # Personality profile (optional)
│
├── state/                          # Auto-generated
│   ├── memory.db                   # Episodic/semantic storage
│   ├── embeddings/                 # Vector store
│   └── synth.log                   # Application logs
│
└── docs/
    ├── README.md                   # Main documentation
    ├── QUICKSTART.md               # 5-minute setup
    ├── system-arch.md              # High-level architecture
    ├── GDIL_README.md              # GDIL guide
    ├── GDIL_COMPLETE.md            # GDIL spec
    ├── PEER_SETUP.md               # Multi-instance guide
    ├── Query-Rating.md             # Self-healing design
    └── Repository-Structure.md     # File organization
```

---

## Browser Compatibility

| Browser | Status |
|---------|--------|
| Chrome/Edge (Chromium) | ✅ Perfect |
| Firefox | ✅ Perfect |
| Safari | ✅ Perfect |
| Mobile browsers | ✅ Responsive |
| IE11 | ❌ Not supported |

---

## Security Considerations

### Current Status
- Localhost only, no authentication
- Suitable for development/demo

### Production Requirements
- [ ] JWT authentication
- [ ] HTTPS/WSS encryption
- [ ] Rate limiting on API endpoints
- [ ] Input validation
- [ ] CORS restrictions
- [ ] Access logging
- [ ] Firewall rules for peer IPs

---

## Roadmap

### Completed
- [x] Six psychological modules
- [x] GDIL project workflow system
- [x] Real-time visualization dashboard
- [x] Multi-instance peer compatibility
- [x] Self-healing query system design

### Planned
- [ ] Voice interface (Whisper + TTS)
- [ ] Advanced tool integration (code execution, web search)
- [ ] Fine-tuned embedding models
- [ ] Federated learning for social layer
- [ ] Multiple concurrent projects
- [ ] Project templates library
- [ ] Visual timeline/Gantt charts
- [ ] Version control integration
- [ ] Collaborative multi-agent projects
- [ ] Cloud-hosted dashboards

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/yourusername/synth-mind.git
cd synth-mind
pip install -r requirements.txt

# Configure LLM provider
export ANTHROPIC_API_KEY="your-key-here"

# Run (CLI only)
python run_synth.py

# Run (CLI + Dashboard)
python run_synth_with_dashboard.py

# Start a project
/project Build a web scraper for news articles
```

---

## License

MIT License — see [LICENSE](LICENSE) file

---

## References

- [README.md](README.md) — Main documentation
- [QUICKSTART.md](QUICKSTART.md) — 5-minute setup guide
- [system-arch.md](system-arch.md) — High-level architecture
- [GDIL_README.md](GDIL_README.md) — GDIL complete guide
- [PEER_SETUP.md](PEER_SETUP.md) — Multi-instance configuration
- [dashboard/README_DASHBOARD.md](dashboard/README_DASHBOARD.md) — Dashboard features
