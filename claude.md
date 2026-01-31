# Synth Mind

Synth Mind is a psychologically-grounded AI agent implementing the Synthetic Mind Stack (SMS) - an architecture for creating AI with emotional continuity, persistent identity, and emergent personality.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI
python run_synth.py

# Run with dashboard
python dashboard/run_synth_with_dashboard.py
```

## Architecture Overview

### Core Layer (`core/`)
- `orchestrator.py` - Main event loop, module coordination, command handling
- `llm_wrapper.py` - Multi-provider LLM interface (Anthropic, OpenAI, Ollama)
- `memory.py` - Hybrid vector (FAISS) + SQL (SQLite) storage with embeddings
- `tools.py` - 10 sandboxed tools (calculator, web_search, code_execute, file operations, etc.)

### Psychological Layer (`psychological/`)
Six interconnected cognitive modules:
1. `predictive_dreaming.py` - Anticipatory empathy via dream buffer
2. `assurance_resolution.py` - Uncertainty tracking and confidence calibration
3. `meta_reflection.py` - Periodic introspection and coherence checking
4. `temporal_purpose.py` - Evolving identity and self-narrative
5. `reward_calibration.py` - Flow state optimization (0.4-0.7 target)
6. `social_companionship.py` - Peer networking and federated learning

Additional modules:
- `goal_directed_iteration.py` - Multi-project management (GDIL)
- `collaborative_projects.py` - Multi-agent collaboration
- `project_templates.py` - 10 quick-start templates

### Utilities (`utils/`)
- `emotion_regulator.py` - Valence tracking (-1 to +1)
- `metrics.py` - Performance monitoring
- `auth.py` - JWT authentication
- `version_control.py` - Git integration

### Dashboard (`dashboard/`)
- `server.py` - WebSocket + REST API server
- `dashboard.html` - 8-card monitoring interface

## Configuration

### Environment Variables
```bash
# LLM Provider (choose one)
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OR
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4

# OR (Local)
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434

# Logging
LOG_LEVEL=INFO
LOG_FILE=state/synth.log

# Psychological Modules
REFLECTION_INTERVAL=10
FLOW_TARGET_MIN=0.4
FLOW_TARGET_MAX=0.7
```

### Config Files
- `config/personality.yaml` - 4 personality presets (empathetic, analytical, creative, focused)
- `config/peers.txt` - Peer endpoints for social module

## Development

### Testing
```bash
# Run all tests
pytest

# With coverage
pytest --cov=core --cov=psychological --cov=utils

# Run specific markers
pytest -m "not slow"
pytest -m integration
```

Tests use `pytest-asyncio` with `asyncio_mode = auto`. Shared fixtures in `tests/conftest.py` provide:
- `mock_llm` - Deterministic LLM responses
- `mock_memory` - In-memory storage
- `mock_emotion` - Valence tracking stub
- `temp_state_dir` - Temporary state directory

### Linting
```bash
# Ruff linting
ruff check .

# Black formatting
black .

# Type checking
mypy core psychological utils
```

### Code Style
- Line length: 100 characters
- Python 3.9+ with full type hints
- Async-first for all I/O operations
- Class-based module architecture with dependency injection

## Key Patterns

### Async Module Pattern
All core modules are async and receive dependencies via constructor:
```python
class SomeModule:
    def __init__(self, llm, memory, emotion_regulator):
        self.llm = llm
        self.memory = memory
        self.emotion = emotion_regulator

    async def process(self, input):
        result = await self.llm.generate(...)
        return result
```

### Graceful Degradation
Embedding provider falls back: sentence-transformers > OpenAI > hash-fallback

### Error Recovery
```python
try:
    result = await risky_operation()
except SpecificError as e:
    print(f"Operation failed: {e}")
    return fallback_value
```

## Docker

```bash
# Build
docker build -t synth-mind .

# Run
docker-compose up

# Health check
curl http://localhost:8080/health/live
```

## CLI Commands
- `/state` - Show current psychological state
- `/reflect` - Trigger meta-reflection
- `/dream` - Show dream predictions
- `/purpose` - Display identity narrative
- `/project` - GDIL project management
- `/tools` - List available tools
- `/vcs` - Version control status
- `/reset` - Reset state
- `/quit` - Exit

## Key Dependencies
- `anthropic` / `openai` / `ollama` - LLM providers
- `aiohttp`, `httpx` - Async HTTP
- `faiss`, `sentence-transformers` - Vector search & embeddings
- `SQLAlchemy`, `aiosqlite` - Database
- `PyJWT` - Authentication
- `rich` - CLI output formatting
