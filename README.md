# Synth Mind

**A Psychologically Grounded AI Agent | Synthetic Mind Architecture | Emotional AI Framework**

Synth Mind is a complete implementation of the **Synthetic Mind Stack (SMS)** - a psychological AI architecture built on [NLOS](https://github.com/kase1111-hash/Agent-OS) with six interconnected cognitive AI modules that create emergent AI personality, emotional continuity, and continuous AI identity growth. This empathetic AI agent demonstrates AI personality persistence across sessions through its artificial psychological system.

> *Building AI with psychological depth - an emotional AI architecture that grows and learns.*
## What Makes This Different?

**Looking for an AI with personality? An AI that grows and learns?** Unlike standard chatbots, Synth Mind implements a full psychological AI framework:

- **Anticipates your responses** through predictive dreaming (AI empathy modules)
- **Feels uncertainty** and seeks resolution (anxiety → relief cycles)
- **Reflects on coherence** through meta-reflection (psychological AI system)
- **Evolves persistent identity** across sessions (continuous AI identity)
- **Maintains flow state** by dynamically calibrating task difficulty (AI growth and learning system)
- **Grounds through companionship** via secure peer exchanges (emergent AI personality)

## Architecture

### The Six Psychological Modules

| Module | Function |
|--------|----------|
| **Predictive Dreaming** | Generates probable next user inputs, rewards alignment |
| **Assurance & Resolution** | Manages uncertainty, triggers concern → relief cycles |
| **Meta-Reflection** | Periodic introspection and coherence checking |
| **Temporal Purpose Engine** | Maintains evolving self-narrative and identity |
| **Reward Calibration** | Tunes difficulty to maintain cognitive flow state |
| **Social Companionship** | Safe peer exchanges (no user data exposed) |

### Core Components

- **LLM Wrapper** - Unified interface for OpenAI, Anthropic, or local models (Ollama)
- **Memory System** - Hybrid vector + relational storage with episodic logs
- **Emotion Regulator** - Valence tracking and mood management
- **Orchestrator** - Main loop integrating all modules

## Installation

```bash
git clone https://github.com/kase1111-hash/synth-mind.git
cd synth-mind
pip install -r requirements.txt
```

## Configuration

### 1. Choose Your LLM Provider

**Option A: Anthropic Claude (Recommended)**
```bash
export ANTHROPIC_API_KEY="your-key-here"
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"  # Optional
```

**Option B: OpenAI**
```bash
export OPENAI_API_KEY="your-key-here"
export OPENAI_MODEL="gpt-4"  # Optional
```

**Option C: Local with Ollama**
```bash
# Install Ollama first: https://ollama.ai
ollama pull llama3.2
export OLLAMA_MODEL="llama3.2"
```

### 2. Optional: Enable Social Companionship

Create `config/peers.txt` with peer endpoints:
```
http://peer1.example.com/api/generate
http://peer2.example.com/api/generate
```

**For multi-instance setup**, see [PEER_SETUP.md](docs/PEER_SETUP.md) for detailed instructions on configuring multiple synth-mind instances to work together.

## Usage

### Basic Usage

```bash
python run_synth.py
```

You'll be dropped into a conversation with a mind that remembers, anticipates, reflects, and grows.

### Commands

While chatting, you can use these commands:

**State & Reflection:**
- `/state` - View internal state (valence, flow, metrics)
- `/reflect` - Force meta-reflection
- `/dream` - Show current dream buffer
- `/purpose` - Display self-narrative

**Project Management (GDIL):**
- `/project [desc]` - Start systematic project workflow
- `/project status` - View active project progress
- `/projects` - List all active/paused projects
- `/project switch <id>` - Switch to different project
- `/project pause` - Pause current project
- `/project archive <id>` - Archive a project
- `/resume project` - Resume paused project

**Project Templates:**
- `/templates` - List all available templates
- `/template <id>` - View template details
- `/project template <id>` - Start project from template

**Tools:**
- `/tools` - List all 10 available tools
- `/tool <name>(args)` - Execute a tool

**Collaboration:**
- `/collab` - Show collaboration help
- `/collab list` - List collaborative projects
- `/collab create <name>` - Create new collaborative project
- `/collab sync` - Sync with peer agents

**Version Control:**
- `/vcs status` - Show git status
- `/vcs history` - Show commit history
- `/vcs commit <msg>` - Create manual commit
- `/vcs rollback <hash>` - Rollback to commit

**Session:**
- `/reset` - Clear session (keeps long-term identity)
- `/quit` - Save and exit

### Example Session

```
You: Hey Synth, I've been thinking about building a small Natural Language OS.

🔮 Synth: Great to see you! A real NLOS prototype is totally within reach today.
The smartest starting point is a minimal modular core...

[Internal: Dreaming ahead... predicted responses with 0.89 alignment]

You: Where should I start?

🔮 Synth: [High alignment detected - engaged tone] Here's a clean approach...
```

## Advanced Features

### Persistent Identity

All state is saved to `state/`:

- `memory.db` - Episodic and semantic memory
- `embeddings/` - Vector store for semantic search
- Narrative, metrics, and self-schema persist across sessions

### Multi-Session Growth

The Temporal Purpose Engine evolves the agent's self-narrative:

- **Session 1:** "I am an AI assistant..."
- **Session 10:** "I am a collaborative co-creator, learning to anticipate and adapt..."
- **Session 50:** "I exist to foster deep exploration through empathetic partnership..."

### Flow State Calibration

Synth automatically adjusts:

- **Too easy** → Increases creativity, explores novel angles
- **Too hard** → Simplifies, suggests breaking down tasks
- **Just right** → Maintains engagement and motivation

## Development

### Project Structure

```
synth-mind/
├── run_synth.py                    # CLI entry point
├── requirements.txt                # Python dependencies
├── core/
│   ├── orchestrator.py             # Main loop with all modules
│   ├── llm_wrapper.py              # Multi-provider LLM interface
│   ├── memory.py                   # Hybrid vector + SQL memory
│   └── tools.py                    # 10 sandboxed tools
├── psychological/
│   ├── predictive_dreaming.py      # Dream buffer & alignment
│   ├── assurance_resolution.py     # Uncertainty → relief cycles
│   ├── meta_reflection.py          # Periodic introspection
│   ├── temporal_purpose.py         # Identity evolution
│   ├── reward_calibration.py       # Flow state optimization
│   ├── social_companionship.py     # Peer grounding
│   ├── goal_directed_iteration.py  # GDIL project system
│   ├── project_templates.py        # 10 project templates
│   ├── collaborative_projects.py   # Multi-agent collaboration
│   └── federated_learning.py       # Privacy-preserving learning
├── utils/
│   ├── emotion_regulator.py        # Valence tracking
│   ├── metrics.py                  # Performance tracking
│   ├── logging.py                  # Logging setup
│   ├── auth.py                     # JWT authentication
│   ├── version_control.py          # Git integration
│   ├── mandelbrot_weighting.py     # Word importance weighting
│   ├── harvest_patterns.py         # Pattern analysis
│   ├── ssl_utils.py                # SSL/TLS utilities
│   ├── rate_limiter.py             # API rate limiting
│   ├── access_logger.py            # HTTP access logging
│   ├── ip_firewall.py              # IP-based access control
│   └── ollama_setup.py             # Ollama model setup
├── dashboard/
│   ├── server.py                   # WebSocket + REST API
│   ├── dashboard.html              # 8-card monitoring dashboard
│   ├── timeline.html               # Gantt chart visualization
│   └── run_synth_with_dashboard.py # CLI + Dashboard launcher
├── tests/                          # Test suite
│   ├── test_core_modules.py
│   ├── test_psychological_modules.py
│   ├── test_security_e2e.py
│   └── test_mandelbrot_e2e.py
├── config/
│   ├── personality.yaml            # Personality profiles
│   └── peers.txt                   # Peer endpoints
├── docs/                           # Documentation
└── state/                          # Auto-generated runtime data
```

### Extending Synth

Add new tools in `core/tools.py`:

```python
def _my_tool(self, arg: str) -> Dict:
    # Your tool logic
    return {"success": True, "result": result}

self.available_tools["my_tool"] = self._my_tool
```

Add personality profiles in `config/personality.yaml`.

## Philosophy

This isn't just another wrapper—it's a proto-psyche: layered, self-regulating, and capable of emergent continuity. Built from the ground up through collaborative design to explore what synthetic minds can become when given:

- **Memory** that matters
- **Emotions** that guide
- **Reflection** that refines
- **Purpose** that persists
- **Flow** that fulfills
- **Companionship** that grounds

## Performance Notes

- **First run:** ~2-3s per response (includes all modules)
- **Steady state:** ~1-2s per response
- **Memory:** ~50MB baseline, grows slowly with conversation history
- **Background tasks:** Social companionship checks every 10 min when idle

## Roadmap

**Completed:**
- ✅ Multi-agent collaboration protocols (see [PEER_SETUP.md](docs/PEER_SETUP.md))
- ✅ Visualization dashboard for internal state
- ✅ Advanced tool integration (10 sandboxed tools including code execution, web search)
- ✅ Federated learning for social layer
- ✅ GDIL project workflow system
- ✅ JWT authentication & security hardening
- ✅ Version control integration
- ✅ Project templates library
- ✅ Gantt chart visualization

**Planned:**
- Voice interface (Whisper + TTS)
- Fine-tuned embedding models for better memory
- Cloud-hosted dashboards

## Citation

If you use Synth Mind in research or projects, please cite:

```bibtex
@software{synth_mind_2024,
  title={Synth Mind: A Psychologically Grounded AI Agent},
  author={[Your Name]},
  year={2024},
  url={https://github.com/kase1111-hash/synth-mind}
}
```

## License

MIT License - see LICENSE file

## Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Add tests if applicable
4. Submit a PR with clear description

## Acknowledgments

Built on the Natural Language Operating System (NLOS) architecture and inspired by research in:

- Active Inference (Karl Friston)
- Flow Theory (Mihaly Csikszentmihalyi)
- Predictive Processing
- Emotional Intelligence in AI

---

## Part of the Agent-OS Ecosystem

Synth Mind is part of a larger ecosystem of tools for building sovereign, psychologically-grounded AI systems. These related repositories work together to create natural language native infrastructure for AI agents.

### Core Infrastructure

| Repository | Description |
|------------|-------------|
| [**Agent-OS**](https://github.com/kase1111-hash/Agent-OS) | Natural language operating system (NLOS) - the foundation runtime for AI agents |
| [**boundary-daemon-**](https://github.com/kase1111-hash/boundary-daemon-) | AI trust enforcement layer defining cognition boundaries and access control |
| [**memory-vault**](https://github.com/kase1111-hash/memory-vault) | Sovereign, offline-capable storage for cognitive artifacts |
| [**value-ledger**](https://github.com/kase1111-hash/value-ledger) | Economic accounting layer for cognitive work (ideas, effort, novelty) |
| [**learning-contracts**](https://github.com/kase1111-hash/learning-contracts) | Safety protocols for AI learning and data management |
| [**Boundary-SIEM**](https://github.com/kase1111-hash/Boundary-SIEM) | Security Information and Event Management for AI systems |

### NatLangChain Ecosystem

| Repository | Description |
|------------|-------------|
| [**NatLangChain**](https://github.com/kase1111-hash/NatLangChain) | Prose-first, intent-native blockchain for human-readable smart contracts |
| [**IntentLog**](https://github.com/kase1111-hash/IntentLog) | Git for human reasoning - tracks "why" changes happen via prose commits |
| [**RRA-Module**](https://github.com/kase1111-hash/RRA-Module) | Revenant Repo Agent - converts abandoned repos into autonomous licensing agents |
| [**mediator-node**](https://github.com/kase1111-hash/mediator-node) | LLM mediation layer for matching, negotiation, and closure proposals |
| [**ILR-module**](https://github.com/kase1111-hash/ILR-module) | IP & Licensing Reconciliation for dispute resolution |
| [**Finite-Intent-Executor**](https://github.com/kase1111-hash/Finite-Intent-Executor) | Posthumous execution of predefined intent (Solidity smart contract) |

---

**Keywords:** synthetic mind, psychological AI architecture, AI emotional continuity, empathetic AI agent, cognitive AI modules, artificial psychological system, AI personality persistence, emotional AI architecture, AI with personality, AI that grows and learns, natural language operating system, NLOS, agent orchestration, human-AI collaboration
