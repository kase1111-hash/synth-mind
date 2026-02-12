# Synth Mind

Synth Mind is a psychologically-grounded AI agent implementing the Synthetic Mind Stack (SMS) - an architecture for creating AI with emotional continuity, persistent identity, and emergent personality.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI
python run_synth.py

# Run with dashboard
python -m dashboard.server
```

## Architecture Overview

### Core Layer (`core/`)
- `orchestrator.py` - Main event loop, module coordination, command handling
- `llm_wrapper.py` - Multi-provider LLM interface (Anthropic, OpenAI, Ollama)
- `memory.py` - Hybrid vector (FAISS) + SQL (SQLite) storage with embeddings
- `tools.py` - 3 sandboxed tools (calculator, code_execute, json_parse)

### Psychological Layer (`psychological/`)
Five interconnected cognitive modules:
1. `predictive_dreaming.py` - Anticipatory empathy via dream buffer
2. `assurance_resolution.py` - Uncertainty tracking and confidence calibration
3. `meta_reflection.py` - Periodic introspection and coherence checking
4. `temporal_purpose.py` - Evolving identity and self-narrative
5. `reward_calibration.py` - Flow state optimization (0.4-0.7 target)

### Utilities (`utils/`)
- `emotion_regulator.py` - Valence tracking (-1 to +1)
- `metrics.py` - Performance monitoring
- `mandelbrot_weighting.py` - Frequency-aware word weighting
- `auth.py` - JWT authentication
- `logging.py` - Logging configuration

### Dashboard (`dashboard/`)
- `server.py` - WebSocket + REST API server with state streaming
- `dashboard.html` - Monitoring interface

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

## CLI Commands
- `/state` - Show current psychological state
- `/reflect` - Trigger meta-reflection
- `/dream` - Show dream predictions
- `/purpose` - Display identity narrative
- `/tools` - List available tools
- `/tool <name>` - Execute a tool
- `/reset` - Reset state
- `/quit` - Exit

## Key Dependencies
- `anthropic` / `openai` - LLM providers
- `aiohttp`, `httpx` - Async HTTP
- `faiss-cpu` - Vector search
- `numpy`, `scikit-learn` - Embeddings
- `PyJWT` - Authentication
- `rich` - CLI output formatting
