# Synth Mind — Technical Specification Sheet

> **Version:** 1.1
> **Last Updated:** 2024-12-23
> **Status:** Core Complete — Some Features Pending

---

## Implementation Status

### Summary

| Category | Status | Notes |
|----------|--------|-------|
| Core Architecture | ✅ Complete | Orchestrator, LLM wrapper, memory system |
| 6 Psychological Modules | ✅ Complete | All modules fully implemented |
| GDIL System | ✅ Complete | 526 lines, 4-phase lifecycle |
| Dashboard | ✅ Complete | WebSocket server with inline fallback |
| CLI Commands | ✅ Complete | All documented commands work |
| Peer Networking | ✅ Complete | API endpoint ready |
| Self-Healing (Query Rating) | ✅ Complete | Logging + harvest utility implemented |
| Advanced Tools | ✅ Complete | 10 tools with sandboxing |
| Embeddings | ⚠️ Placeholder | Uses hash-based fallback, not real embeddings |

### Detailed Component Status

#### ✅ Fully Implemented

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Orchestrator | `core/orchestrator.py` | 343 | Full integration of all modules |
| LLM Wrapper | `core/llm_wrapper.py` | 162 | Anthropic, OpenAI, Ollama support |
| Memory System | `core/memory.py` | 213 | SQLite + FAISS (with fallback) |
| Predictive Dreaming | `psychological/predictive_dreaming.py` | 143 | Dream buffer, alignment scoring |
| Assurance Resolution | `psychological/assurance_resolution.py` | 224 | Uncertainty tracking, concern resolution |
| Meta-Reflection | `psychological/meta_reflection.py` | 181 | Periodic introspection |
| Temporal Purpose | `psychological/temporal_purpose.py` | 165 | Narrative evolution, metrics |
| Reward Calibration | `psychological/reward_calibration.py` | 150 | Flow state optimization |
| Social Companionship | `psychological/social_companionship.py` | 171 | Peer communication protocol |
| GDIL | `psychological/goal_directed_iteration.py` | 526 | Full 4-phase project system |
| Dashboard Server | `dashboard/server.py` | 433 | WebSocket + REST API |
| Emotion Regulator | `utils/emotion_regulator.py` | 98 | Valence tracking |
| Metrics Tracker | `utils/metrics.py` | 117 | Performance aggregation |
| CLI Entry Point | `run_synth.py` | 101 | Full command support |

#### ⚠️ Partially Implemented

| Component | Issue | Impact |
|-----------|-------|--------|
| Memory Embeddings | Uses hash-based placeholder | Semantic search quality limited |
| `grounding_confidence()` | Returns static 0.8 | Hallucination detection limited |
| `detect_coherence_drift()` | Returns static False | Drift detection disabled |
| Dashboard HTML | Inline fallback only | Full 8-card dashboard in docs, simplified inline |
| `config/personality.yaml` | Empty file | Personality profiles not configured |
| `config/peers.txt` | Empty file | No peers configured by default |

#### ✅ Recently Implemented

| Component | File | Notes |
|-----------|------|-------|
| Uncertainty Logging | `core/memory.py` | `uncertainty_log` table with full CRUD |
| Query Rating Integration | `psychological/assurance_resolution.py` | Auto-logs low-confidence responses |
| Pattern Harvest Utility | `utils/harvest_patterns.py` | CLI tool for analysis + LLM-powered patterns |
| Advanced Tool Manager | `core/tools.py` | 10 tools with sandboxing (665 lines) |
| Tool CLI Commands | `core/orchestrator.py` | `/tools` and `/tool` commands |

#### ❌ Not Implemented (Design/Roadmap Only)

| Feature | Documentation | Notes |
|---------|---------------|-------|
| Voice Interface | README roadmap | Whisper + TTS not integrated |
| Advanced Tool Integration | README roadmap | Code execution, web search missing |
| Fine-tuned Embeddings | README roadmap | Using placeholder embeddings |
| Multiple Concurrent Projects | GDIL_COMPLETE.md | Single project only |
| Project Templates | GDIL_COMPLETE.md | Not implemented |
| Visual Timeline/Gantt | GDIL_COMPLETE.md | Not implemented |
| Version Control Integration | GDIL_COMPLETE.md | No Git integration |
| Federated Learning | README roadmap | Not implemented |

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

**Status:** ✅ Implemented

### How It Works

1. **Automatic Logging**: When confidence drops below 80%, the Assurance module logs the uncertainty
2. **Pattern Harvest**: Run `python utils/harvest_patterns.py` to analyze patterns
3. **LLM Analysis**: Use `--analyze` flag for AI-powered pattern detection

### Uncertainty Log Schema
```sql
CREATE TABLE uncertainty_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    user_message TEXT,
    parsed_intent TEXT,
    confidence_score REAL,
    context TEXT,
    signals TEXT,           -- JSON of signal weights
    resolved INTEGER,       -- 0 or 1
    resolution_pattern TEXT -- What fixed it
);
```

### CLI Commands

```bash
# Show statistics
python utils/harvest_patterns.py --stats

# Run simple pattern analysis
python utils/harvest_patterns.py

# Run LLM-powered analysis (requires API key)
python utils/harvest_patterns.py --analyze

# Export patterns to file
python utils/harvest_patterns.py --export patterns.yaml
```

### Integration Points

| Component | Integration |
|-----------|-------------|
| `AssuranceResolutionModule` | Logs uncertainties when confidence < 80% |
| `MemorySystem` | Stores/retrieves uncertainty logs |
| `harvest_patterns.py` | Analyzes logs, proposes improvements |

### Pattern Harvest Cycle
- Run periodically (recommended: weekly or after 100+ entries)
- LLM identifies repeating patterns and synonyms
- Generates new templates and test cases
- Progressive reduction: ~25-30% per cycle

---

## Advanced Tool Manager

**File:** `core/tools.py`
**Status:** ✅ Implemented (665 lines)

### Available Tools

| Tool | Description | Sandboxed |
|------|-------------|-----------|
| `calculator` | Safe math expression evaluator with functions | ✅ |
| `timer` | Wait for specified seconds (max 30) | ✅ |
| `web_search` | Search via DuckDuckGo API (no key required) | ✅ |
| `http_fetch` | Fetch URL content with text extraction | ✅ |
| `code_execute` | Python code execution with restricted builtins | ✅ |
| `file_read` | Read files from workspace directory | ✅ |
| `file_write` | Write files to workspace directory | ✅ |
| `file_list` | List files in workspace directory | ✅ |
| `shell_run` | Execute restricted shell commands | ✅ |
| `json_parse` | Parse JSON and extract data via dot notation | ✅ |

### CLI Commands

```bash
# List all available tools
/tools

# Execute a tool
/tool calculator(expression='sqrt(16) + pi')
/tool web_search(query='python asyncio tutorial')
/tool code_execute(code='print([x**2 for x in range(10)])')
/tool file_write(path='notes.txt', content='Hello World')
/tool shell_run(command='ls -la')

# Shorthand for single-argument tools
/tool calculator 2 + 2 * 3
/tool web_search python tutorials
```

### Safety Controls

| Control | Limit |
|---------|-------|
| Code execution timeout | 10 seconds |
| Output length | 10,000 characters |
| File size | 1 MB max |
| File operations | Sandboxed to `workspace/` |
| Shell commands | Whitelist: ls, pwd, date, cat, grep, etc. |
| Shell restrictions | No pipes, redirects, or chaining |

### Code Sandbox

The `code_execute` tool provides:
- **Restricted builtins**: No `open`, `exec`, `eval`, `import`
- **Safe modules**: `math`, `random`, `datetime`, `json`, `re`, `collections`
- **Output capture**: stdout and stderr captured
- **Error handling**: Syntax errors reported with line numbers

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
| `/tools` | List all available tools |
| `/tool <name>(args)` | Execute a tool |
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

### ✅ Completed
- [x] Six psychological modules (fully functional)
- [x] GDIL project workflow system (4-phase lifecycle)
- [x] Real-time visualization dashboard (WebSocket + REST)
- [x] Multi-instance peer compatibility (API endpoint)
- [x] CLI with all commands
- [x] Multi-LLM provider support (Anthropic, OpenAI, Ollama)
- [x] Persistent memory system (SQLite)
- [x] Self-healing query system (uncertainty logging + pattern harvest)
- [x] Advanced tool manager (10 sandboxed tools including code execution, web search)

### ⚠️ Partially Complete
- [~] Embedding system (placeholder, not production-ready)
- [~] Dashboard visualization (simplified inline version)

### ❌ Not Started
- [ ] Voice interface (Whisper + TTS)
- [ ] Fine-tuned embedding models
- [ ] Federated learning for social layer
- [ ] Multiple concurrent projects
- [ ] Project templates library
- [ ] Visual timeline/Gantt charts
- [ ] Version control integration
- [ ] Collaborative multi-agent projects
- [ ] Cloud-hosted dashboards
- [ ] JWT authentication for production
- [ ] HTTPS/WSS encryption

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
