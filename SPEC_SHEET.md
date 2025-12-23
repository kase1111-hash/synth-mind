# Synth Mind — Technical Specification Sheet

> **Version:** 1.6
> **Last Updated:** 2024-12-23
> **Status:** Core Complete — Production Ready (JWT Auth + Gantt Charts + VCS Integration)

---

## Implementation Status

### Summary

| Category | Status | Notes |
|----------|--------|-------|
| Core Architecture | ✅ Complete | Orchestrator, LLM wrapper, memory system |
| 6 Psychological Modules | ✅ Complete | All modules fully implemented |
| GDIL System | ✅ Complete | 526 lines, 4-phase lifecycle |
| Dashboard | ✅ Complete | Full 8-card WebSocket dashboard |
| CLI Commands | ✅ Complete | All documented commands work |
| Peer Networking | ✅ Complete | API endpoint ready |
| Self-Healing (Query Rating) | ✅ Complete | Logging + harvest utility implemented |
| Advanced Tools | ✅ Complete | 10 tools with sandboxing |
| Memory Embeddings | ✅ Complete | sentence-transformers + OpenAI fallback |
| Federated Learning | ✅ Complete | Privacy-preserving pattern sharing |
| Multiple Concurrent Projects | ✅ Complete | GDIL multi-project with switching |
| Project Templates | ✅ Complete | 10 built-in templates with roadmaps |
| Collaborative Projects | ✅ Complete | Multi-agent project collaboration |
| JWT Authentication | ✅ Complete | Production-ready auth with roles |
| Visual Timeline/Gantt | ✅ Complete | Interactive project visualization |
| Version Control | ✅ Complete | Git integration with auto-commit, rollback |
| Documentation | ✅ Complete | Consolidated in `/docs` folder |

### Detailed Component Status

#### ✅ Fully Implemented

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Orchestrator | `core/orchestrator.py` | 440 | Full integration of all modules |
| LLM Wrapper | `core/llm_wrapper.py` | 162 | Anthropic, OpenAI, Ollama support |
| Memory System | `core/memory.py` | 800+ | SQLite + FAISS + real embeddings |
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
| `config/peers.txt` | Empty file | No peers configured by default |

#### ✅ Recently Implemented

| Component | File | Notes |
|-----------|------|-------|
| Version Control Manager | `utils/version_control.py` | Git wrapper with auto-commit, rollback, changelog |
| VCS GDIL Integration | `psychological/goal_directed_iteration.py` | Auto-commits on project/subtask events |
| VCS CLI Commands | `core/orchestrator.py` | `/vcs status`, `/vcs history`, `/vcs rollback`, etc. |
| Personality Configuration | `config/personality.yaml` | 4 personality profiles, GDIL/flow/module settings |
| Uncertainty Logging | `core/memory.py` | `uncertainty_log` table with full CRUD |
| Query Rating Integration | `psychological/assurance_resolution.py` | Auto-logs low-confidence responses |
| Pattern Harvest Utility | `utils/harvest_patterns.py` | CLI tool for analysis + LLM-powered patterns |
| Advanced Tool Manager | `core/tools.py` | 10 tools with sandboxing (665 lines) |
| Tool CLI Commands | `core/orchestrator.py` | `/tools` and `/tool` commands |
| Memory Embeddings | `core/memory.py` | Multi-backend: sentence-transformers, OpenAI, hash fallback |
| Semantic Search | `core/memory.py` | `search_semantic()`, `get_related_memories()` |
| Grounding Confidence | `core/memory.py` | Real similarity-based confidence scoring |
| Coherence Drift Detection | `core/memory.py` | Context embedding analysis |
| Federated Learning | `psychological/federated_learning.py` | Privacy-preserving pattern sharing (450+ lines) |
| Federated Integration | `psychological/social_companionship.py` | Social layer + federated sync |
| Federated API | `dashboard/server.py` | `/api/federated/receive`, `/api/federated/stats` |
| Multi-Project GDIL | `psychological/goal_directed_iteration.py` | Concurrent projects, switching, persistence |
| Multi-Project CLI | `core/orchestrator.py` | `/projects`, `/project switch`, `/project pause`, `/project archive` |
| Full Dashboard HTML | `dashboard/dashboard.html` | 8-card WebSocket dashboard with live updates |
| Dashboard Project View | `dashboard/server.py` | Project status API for dashboard |
| Project Templates | `psychological/project_templates.py` | 10 built-in templates with pre-defined roadmaps |
| Template CLI Commands | `core/orchestrator.py` | `/templates`, `/template`, `/project template` |
| Collaborative Projects | `psychological/collaborative_projects.py` | Multi-agent collaboration (600+ lines) |
| Collaboration CLI | `core/orchestrator.py` | `/collab` commands for multi-agent projects |
| Collaboration API | `dashboard/server.py` | `/api/collab/projects`, `/api/collab/sync`, `/api/collab/stats` |
| JWT Authentication | `utils/auth.py` | Full auth module with roles (350+ lines) |
| Auth Middleware | `dashboard/server.py` | Protected routes with token validation |
| User Management API | `dashboard/server.py` | Create, delete, update users (admin only) |
| Timeline/Gantt Page | `dashboard/timeline.html` | Interactive Gantt chart visualization |
| Timeline API | `dashboard/server.py` | `/timeline`, `/api/timeline` endpoints |

#### ❌ Not Implemented (Design/Roadmap Only)

| Feature | Documentation | Notes |
|---------|---------------|-------|
| Voice Interface | README roadmap | Whisper + TTS not integrated |

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
| `max_concurrent_projects` | 5 | Maximum active projects |

### Multiple Concurrent Projects

**Status:** ✅ Implemented

Manage up to 5 concurrent projects with seamless context switching.

#### Commands

| Command | Description |
|---------|-------------|
| `/projects` | List all active/paused projects with status |
| `/project switch <id>` | Switch to a different project (auto-pauses current) |
| `/project pause` | Pause current project without archiving |
| `/project archive <id>` | Archive a project (removes from active list) |

#### Project States

| State | Description |
|-------|-------------|
| `initialization` | Gathering requirements, asking clarifying questions |
| `planning` | Generating roadmap and subtasks |
| `iteration` | Actively working on subtasks |
| `paused` | Temporarily paused, can resume |
| `exit` | Completed or stalled |
| `archived` | Moved to history, not visible in `/projects` |

#### Features

- **Automatic Naming**: Projects are auto-named from user input
- **Short ID Matching**: Use last few characters of ID (e.g., `1234567890` → `890`)
- **Persistence**: Projects survive restarts via memory system
- **Auto-Pause**: Switching projects pauses the current one
- **Context Preservation**: Each project maintains full state including iterations

### Project Templates

**Status:** ✅ Implemented
**File:** `psychological/project_templates.py`

Quick-start projects with pre-defined roadmaps and clarification questions.

#### Built-in Templates

| ID | Name | Category | Tasks |
|----|------|----------|-------|
| `web-app` | Web Application | Web Development | 7 |
| `api` | REST API | Web Development | 6 |
| `data-analysis` | Data Analysis | Data Science | 6 |
| `ml-model` | Machine Learning Model | Data Science | 7 |
| `refactor` | Code Refactoring | Code Quality | 7 |
| `bug-fix` | Bug Investigation & Fix | Code Quality | 6 |
| `new-feature` | New Feature | Features | 6 |
| `documentation` | Documentation | Documentation | 6 |
| `test-suite` | Test Suite | Testing | 6 |
| `cli-tool` | CLI Tool | Tools | 6 |

#### Commands

| Command | Description |
|---------|-------------|
| `/templates` | List all available templates |
| `/template <id>` | View template details |
| `/project template <id>` | Start project from template |
| `/project template <id> <customization>` | Start with customization |

#### Template Contents

Each template includes:
- **Pre-defined roadmap** with prioritized tasks and dependencies
- **Clarifying questions** for customization
- **Suggested brief** and end transformation
- **Estimated iterations** for completion

#### Usage Example

```bash
# List templates
/templates

# View template details
/template web-app

# Start from template
/project template api

# Start with customization
/project template api User authentication service
```

### Collaborative Multi-Agent Projects

**Status:** ✅ Implemented
**File:** `psychological/collaborative_projects.py`

Multiple synth-mind instances can collaborate on shared projects.

#### Agent Roles

| Role | Description |
|------|-------------|
| `coordinator` | Created the project, manages overall flow |
| `contributor` | Joined to help with tasks |
| `reviewer` | Reviews completed work |
| `observer` | Read-only access |

#### Task States

| State | Description |
|-------|-------------|
| `available` | Not claimed by anyone |
| `claimed` | Reserved by an agent |
| `in_progress` | Active work happening |
| `pending_review` | Completed, needs review |
| `approved` | Reviewed and approved |
| `blocked` | Has blockers |

#### Commands

| Command | Description |
|---------|-------------|
| `/collab` | Show collaboration help |
| `/collab list` | List collaborative projects |
| `/collab create <name>` | Create new project (you become coordinator) |
| `/collab view <id>` | View project details |
| `/collab join <id>` | Join a project as contributor |
| `/collab leave <id>` | Leave a project |
| `/collab tasks <id>` | List tasks in a project |
| `/collab claim <task_id>` | Claim an available task |
| `/collab release <task_id>` | Release a claimed task |
| `/collab progress <task_id> <status>` | Update task progress |
| `/collab review <task_id> <approve/reject>` | Review task (coordinator only) |
| `/collab msg <id> <message>` | Send message to project |
| `/collab chat <id>` | View recent messages |
| `/collab sync` | Sync with peer agents |
| `/collab stats` | View collaboration statistics |

#### Features

- **Task Dependencies**: Tasks can depend on other tasks
- **Version Tracking**: Conflict resolution via version numbers
- **Inter-Agent Chat**: Built-in messaging system
- **Peer Sync**: Synchronize project state via API endpoints
- **Activity Log**: Track all project events

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/collab/projects` | GET | Get projects for sync |
| `/api/collab/sync` | POST | Receive sync from peer |
| `/api/collab/stats` | GET | Get collaboration statistics |

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

## Visual Timeline & Gantt Charts

**Status:** ✅ Implemented
**File:** `dashboard/timeline.html`

### Overview

Interactive project visualization with Gantt-style charts for tracking GDIL and collaborative project progress.

### Features

| Feature | Description |
|---------|-------------|
| Gantt Bars | Color-coded task bars showing status |
| Multi-Project View | View all projects or filter by project |
| Task Tooltips | Hover for task details (priority, dependencies, progress) |
| Zoom Controls | Zoom in/out on timeline |
| Auto-Refresh | Updates every 10 seconds |
| Collaborative Support | Shows both GDIL and collaborative projects |

### Task Status Colors

| Status | Color | Description |
|--------|-------|-------------|
| Completed | Green | Task finished successfully |
| In Progress | Purple (pulsing) | Currently being worked on |
| Pending | Gray | Not yet started |
| Pending Review | Yellow | Awaiting review |
| Blocked | Red | Has blockers |

### Access

| Route | Description |
|-------|-------------|
| `/timeline` | Timeline visualization page |
| `/api/timeline` | JSON API for project data |

### API Response

```json
GET /api/timeline
{
  "success": true,
  "projects": [
    {
      "id": "project_123",
      "name": "My Project",
      "phase": "iteration",
      "roadmap": [
        {
          "id": "task_1",
          "name": "Task Name",
          "status": "completed",
          "priority": 1,
          "dependencies": [],
          "progress": 1.0
        }
      ],
      "progress": 0.75,
      "is_collaborative": false
    }
  ],
  "total_projects": 1
}
```

### Usage

1. Navigate to `http://localhost:8080/timeline`
2. Select a project from dropdown or view all
3. Hover over task bars for details
4. Use zoom controls for timeline scaling

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

## Federated Learning System

**Status:** ✅ Implemented
**File:** `psychological/federated_learning.py`

### Overview

Privacy-preserving knowledge sharing between synth-mind instances. Enables distributed learning without exposing user data.

### Key Components

| Component | Description |
|-----------|-------------|
| `SharedPattern` | Anonymized learnable pattern with embedding |
| `PrivacyFilter` | Differential privacy + k-anonymity enforcement |
| `PatternAggregator` | Federated averaging for consensus patterns |
| `FederatedLearningLayer` | Main coordinator for pattern extraction/sharing |

### Privacy Protections

| Protection | Implementation |
|------------|----------------|
| Differential Privacy | Laplacian noise (ε=1.0 default) |
| K-Anonymity | Minimum 5 observations before sharing |
| Hash-based IDs | Pattern content never shared, only hashes |
| Embedding Noise | Normalized random noise added |
| Quantized Metrics | Reduced precision on success rates |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/federated/receive` | POST | Receive patterns from peer |
| `/api/federated/stats` | GET | Get federated learning stats |

### Pattern Types

| Type | Source | Purpose |
|------|--------|---------|
| `resolution` | Uncertainty logs | Share what resolves ambiguity |
| `intent` | Intent parsing | Share parsing improvements |
| `calibration` | Flow state | Share behavioral adjustments |

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `privacy_epsilon` | 1.0 | Differential privacy budget |
| `k_anonymity` | 5 | Minimum samples before sharing |
| `sync_interval_minutes` | 30 | Time between sync rounds |
| `enable_federated_learning` | true | Enable/disable federated layer |

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
| Semantic Search | FAISS vector index (`state/embeddings/`) |
| Session State | Persistent across restarts |

#### Embedding Providers (Auto-Detected)

| Provider | Priority | Dimension | Notes |
|----------|----------|-----------|-------|
| sentence-transformers | 1st | 384 | Local, free, `all-MiniLM-L6-v2` |
| OpenAI | 2nd | 1536 | Cloud, requires `OPENAI_API_KEY` |
| Hash Fallback | 3rd | 384 | Deterministic but not semantic |

#### Semantic Memory API

| Method | Description |
|--------|-------------|
| `store_semantic(content, category, importance)` | Store memory with embedding |
| `search_semantic(query, k, category)` | Find similar memories |
| `get_related_memories(text, k)` | Combined semantic + episodic search |
| `grounding_confidence(text)` | Similarity-based confidence (0-1) |
| `detect_coherence_drift(threshold)` | Context drift detection |
| `track_context_embedding(text)` | Track for drift analysis |
| `get_embedding_stats()` | Provider info and memory counts |

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
| `/projects` | List all active/paused projects |
| `/project switch <id>` | Switch to a different project |
| `/project pause` | Pause current project |
| `/project archive <id>` | Archive a project |
| `/project template <id>` | Start project from template |
| `/templates` | List all available templates |
| `/template <id>` | View template details |
| `/resume project` | Continue paused project |
| `/tools` | List all available tools |
| `/tool <name>(args)` | Execute a tool |
| `/collab` | Show collaboration help |
| `/collab list` | List collaborative projects |
| `/collab create <name>` | Create new collaborative project |
| `/collab view <id>` | View project details |
| `/collab join <id>` | Join a project |
| `/collab tasks <id>` | List tasks in a project |
| `/collab claim <task_id>` | Claim an available task |
| `/collab sync` | Sync with peer agents |
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
│   ├── logging.py                  # Logging setup
│   ├── auth.py                     # JWT authentication
│   ├── version_control.py          # Git VCS integration
│   └── ssl_utils.py                # SSL/TLS certificate utilities
│
├── dashboard/
│   ├── server.py                   # WebSocket server
│   ├── dashboard.html              # Main dashboard page
│   ├── timeline.html               # Gantt chart visualization
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
├── certs/                          # Auto-generated (gitignored)
│   ├── server.crt                  # SSL certificate
│   └── server.key                  # SSL private key
│
├── tests/
│   └── test_security_e2e.py        # Security test suite
│
└── docs/
    ├── QUICKSTART.md               # 5-minute setup guide
    ├── system-arch.md              # High-level architecture
    ├── GDIL_README.md              # GDIL user guide
    ├── GDIL_COMPLETE.md            # GDIL specification
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
- JWT authentication enabled by default
- Role-based access control (admin, operator, viewer)
- PBKDF2 password hashing with salt
- Token blacklisting for logout
- Secure file permissions on auth config

### JWT Authentication

**Status:** ✅ Implemented
**File:** `utils/auth.py`

#### User Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access, user management |
| `operator` | Control operations, no user management |
| `viewer` | Read-only access |

#### Token Configuration

| Parameter | Value |
|-----------|-------|
| Access Token TTL | 30 minutes |
| Refresh Token TTL | 7 days |
| Algorithm | HS256 |
| Password Hashing | PBKDF2-SHA256 (100k iterations) |

#### API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/status` | GET | No | Check auth status/setup required |
| `/api/auth/setup` | POST | No | Create initial admin (first run only) |
| `/api/auth/login` | POST | No | Authenticate, get tokens |
| `/api/auth/logout` | POST | Yes | Blacklist current token |
| `/api/auth/refresh` | POST | No | Refresh access token |
| `/api/users` | GET | Admin | List all users |
| `/api/users` | POST | Admin | Create new user |
| `/api/users/{username}` | DELETE | Admin | Delete user |
| `/api/users/{username}/password` | PUT | Admin | Update password |
| `/api/users/{username}/role` | PUT | Admin | Update role |

#### Usage

```bash
# Start with auth enabled (default)
python dashboard/server.py

# Start with auth disabled
python dashboard/server.py --no-auth

# Initial setup (first run)
curl -X POST http://localhost:8080/api/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Login
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Use token for protected endpoints
curl http://localhost:8080/api/state \
  -H "Authorization: Bearer <access_token>"
```

### HTTPS/WSS Encryption

**Status:** ✅ Implemented
**Files:** `dashboard/server.py`, `utils/ssl_utils.py`

#### Overview

The dashboard server supports HTTPS and WSS (WebSocket Secure) for encrypted communication. This ensures all data transmitted between the browser and server is protected.

#### Features

| Feature | Description |
|---------|-------------|
| TLS 1.2+ | Minimum TLS version enforced |
| Self-signed Certs | Auto-generate dev certificates |
| Custom Certificates | Use your own CA-signed certs |
| WSS Auto-detection | Dashboard auto-switches to WSS on HTTPS |

#### CLI Options

| Option | Description |
|--------|-------------|
| `--ssl-cert PATH` | Path to SSL certificate file |
| `--ssl-key PATH` | Path to SSL private key file |
| `--ssl-dev` | Generate/use self-signed certificate for development |

#### Usage Examples

```bash
# Development: Auto-generate self-signed certificate
python dashboard/server.py --ssl-dev

# Production: Use your own certificates
python dashboard/server.py --ssl-cert /path/to/cert.pem --ssl-key /path/to/key.pem

# Combined with other options
python dashboard/server.py --ssl-dev --port 8443 --no-auth
```

#### Certificate Generation

For development, use the `--ssl-dev` flag which automatically generates self-signed certificates in the `certs/` directory.

For production, you can:
1. Use Let's Encrypt for free CA-signed certificates
2. Generate certificates manually:
   ```bash
   python utils/ssl_utils.py --generate --hostname yourdomain.com
   ```

#### Certificate Utilities

```bash
# Generate self-signed certificate
python utils/ssl_utils.py --generate

# View certificate info
python utils/ssl_utils.py --info certs/server.crt

# Custom options
python utils/ssl_utils.py --generate --hostname mydomain.com --days 365
```

### Production Checklist

- [x] JWT authentication
- [x] HTTPS/WSS encryption
- [ ] Rate limiting on API endpoints
- [x] Input validation
- [x] CORS restrictions
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
- [x] Persistent memory system (SQLite + FAISS)
- [x] Self-healing query system (uncertainty logging + pattern harvest)
- [x] Advanced tool manager (10 sandboxed tools including code execution, web search)
- [x] Memory embeddings (sentence-transformers + OpenAI fallback)
- [x] Semantic search and grounding confidence
- [x] Context coherence drift detection
- [x] Federated learning for social layer (differential privacy, k-anonymity)
- [x] Multiple concurrent projects (up to 5, with switching/pause/archive)
- [x] Full 8-card dashboard visualization (WebSocket live updates)
- [x] Project templates library (10 built-in templates)
- [x] Collaborative multi-agent projects (task claiming, sync, roles)
- [x] JWT authentication for production (role-based access control)
- [x] Visual timeline/Gantt charts (interactive project visualization)
- [x] Version control integration (Git auto-commit, rollback, changelog)
- [x] HTTPS/WSS encryption (TLS 1.2+, self-signed cert generation)

### ❌ Not Started
- [ ] Voice interface (Whisper + TTS) — planned for Agent OS
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
- [QUICKSTART.md](docs/QUICKSTART.md) — 5-minute setup guide
- [system-arch.md](docs/system-arch.md) — High-level architecture
- [GDIL_README.md](docs/GDIL_README.md) — GDIL complete guide
- [GDIL_COMPLETE.md](docs/GDIL_COMPLETE.md) — GDIL specification
- [PEER_SETUP.md](docs/PEER_SETUP.md) — Multi-instance configuration
- [Query-Rating.md](docs/Query-Rating.md) — Self-healing design
- [dashboard/README_DASHBOARD.md](dashboard/README_DASHBOARD.md) — Dashboard features
