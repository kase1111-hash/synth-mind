# System Architecture

Synth Mind implements the Synthetic Mind Stack (SMS) - a psychologically-grounded AI agent with six interconnected modules that create emergent continuity, empathy, and growth.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Input                               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                v
┌─────────────────────────────────────────────────────────────────┐
│                       Orchestrator                               │
│  (core/orchestrator.py)                                          │
│  - Main conversation loop                                        │
│  - Module coordination                                           │
│  - State management                                              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        v                       v                       v
┌───────────────┐    ┌─────────────────┐    ┌─────────────────────┐
│  Core Layer   │    │ Psychological   │    │   Utility Layer     │
│               │    │     Layer       │    │                     │
│ - LLM Wrapper │    │ (6 modules)     │    │ - Emotion Regulator │
│ - Memory      │    │                 │    │ - Metrics           │
│ - Tools       │    │                 │    │ - Logging           │
└───────────────┘    └─────────────────┘    └─────────────────────┘
```

## Core Layer

### LLM Wrapper (`core/llm_wrapper.py`)
Unified interface supporting multiple providers:
- **Anthropic Claude** - Recommended for best performance
- **OpenAI GPT** - Full compatibility
- **Ollama** - Local/offline models

### Memory System (`core/memory.py`)
Hybrid storage combining:
- **Episodic Memory** - Conversation history with timestamps
- **Semantic Memory** - Vector embeddings for similarity search
- **SQLite Backend** - Persistent storage in `state/memory.db`

### Tool Manager (`core/tools.py`)
Extensible tool system for agent capabilities.

## Psychological Layer

The six modules work together to create emergent behavior:

### 1. Predictive Dreaming (`psychological/predictive_dreaming.py`)
- Generates probable user responses before they occur
- Maintains a "dream buffer" of predictions
- Rewards alignment between predictions and actual input
- Enables anticipatory responses

### 2. Assurance & Resolution (`psychological/assurance_resolution.py`)
- Tracks uncertainty and flags concerns
- Implements anxiety → relief cycles
- Manages cognitive confidence levels
- Provides emotional resolution when concerns are addressed

### 3. Meta-Reflection (`psychological/meta_reflection.py`)
- Periodic introspection on internal coherence
- Evaluates alignment between behavior and purpose
- Generates insights about cognitive patterns
- Self-corrects drift from goals

### 4. Temporal Purpose Engine (`psychological/temporal_purpose.py`)
- Maintains evolving self-narrative
- Tracks identity across sessions
- Updates purpose based on interactions
- Enables long-term growth

### 5. Reward Calibration (`psychological/reward_calibration.py`)
- Monitors cognitive load and engagement
- Adjusts task difficulty for flow state
- Prevents boredom (too easy) and overwhelm (too hard)
- Optimizes for sustained engagement

### 6. Social Companionship (`psychological/social_companionship.py`)
- Enables multi-instance peer networking
- Shares anonymized patterns (never user data)
- Provides grounding through external validation
- Supports federated learning

## Data Flow

```
User Input
    │
    v
┌───────────────────┐
│ Predictive        │──> Compare with dream buffer
│ Dreaming          │──> Calculate alignment reward
└───────────────────┘
    │
    v
┌───────────────────┐
│ Memory System     │──> Store in episodic memory
│                   │──> Update embeddings
└───────────────────┘
    │
    v
┌───────────────────┐
│ Assurance         │──> Flag uncertainties
│                   │──> Resolve concerns
└───────────────────┘
    │
    v
┌───────────────────┐
│ LLM Generation    │──> Generate response
│                   │──> Apply personality
└───────────────────┘
    │
    v
┌───────────────────┐
│ Reward            │──> Assess difficulty
│ Calibration       │──> Adjust for flow
└───────────────────┘
    │
    v
┌───────────────────┐
│ Meta-Reflection   │──> Periodic coherence check
│ (every N turns)   │──> Generate insights
└───────────────────┘
    │
    v
┌───────────────────┐
│ Temporal Purpose  │──> Update narrative
│                   │──> Evolve identity
└───────────────────┘
    │
    v
Response to User
```

## State Persistence

All state is stored in `state/`:
- `memory.db` - SQLite database for memory and metrics
- `embeddings/` - Vector store for semantic search
- Narrative and identity persist across sessions

## Extension Points

### Adding Tools
```python
# In core/tools.py
def _my_tool(self, arg: str) -> Dict:
    return {"success": True, "result": result}

self.available_tools["my_tool"] = self._my_tool
```

### Custom Personality
Edit `config/personality.yaml` for:
- Tone and style adjustments
- Module parameter tuning
- Response formatting

## Related Documentation

- [README.md](../README.md) - Quick start and overview
- [GDIL_README.md](GDIL_README.md) - Goal-Directed Iteration Loop
- [PEER_SETUP.md](PEER_SETUP.md) - Multi-instance networking
- [README_DASHBOARD.md](../dashboard/README_DASHBOARD.md) - Real-time visualization
