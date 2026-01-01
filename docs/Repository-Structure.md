# Repository Structure

Complete file organization for the Synth Mind project.

```
synth-mind/
├── README.md                          # Main project documentation
├── SPEC_SHEET.md                      # Technical specification
├── SECURITY_REPORT.md                 # Security assessment report
├── requirements.txt                   # Python dependencies
├── run_synth.py                       # CLI entry point
│
├── core/                              # Core components
│   ├── __init__.py
│   ├── orchestrator.py                # Main processing loop (700+ lines)
│   ├── llm_wrapper.py                 # Multi-provider LLM interface
│   ├── memory.py                      # Hybrid vector + SQL storage (800+ lines)
│   └── tools.py                       # 10 sandboxed tools (830+ lines)
│
├── psychological/                     # Psychological substrate (6+4 modules)
│   ├── __init__.py
│   ├── predictive_dreaming.py         # Dream buffer & alignment scoring
│   ├── assurance_resolution.py        # Uncertainty → relief cycles
│   ├── meta_reflection.py             # Periodic introspection
│   ├── temporal_purpose.py            # Identity evolution
│   ├── reward_calibration.py          # Flow state optimization
│   ├── social_companionship.py        # Peer grounding layer
│   ├── goal_directed_iteration.py     # GDIL project system (526+ lines)
│   ├── project_templates.py           # 10 project templates
│   ├── collaborative_projects.py      # Multi-agent collaboration (600+ lines)
│   └── federated_learning.py          # Privacy-preserving learning (450+ lines)
│
├── utils/                             # Utility modules
│   ├── __init__.py
│   ├── emotion_regulator.py           # Valence tracking
│   ├── metrics.py                     # Performance tracking
│   ├── logging.py                     # Logging setup
│   ├── auth.py                        # JWT authentication (350+ lines)
│   ├── version_control.py             # Git VCS integration
│   ├── mandelbrot_weighting.py        # Word importance weighting (510+ lines)
│   ├── harvest_patterns.py            # Pattern analysis CLI
│   ├── ssl_utils.py                   # SSL/TLS certificate utilities
│   ├── rate_limiter.py                # API rate limiting
│   ├── access_logger.py               # HTTP access logging
│   ├── ip_firewall.py                 # IP-based access control
│   └── ollama_setup.py                # Ollama model setup helper
│
├── dashboard/                         # Web dashboard
│   ├── server.py                      # WebSocket + REST API server (430+ lines)
│   ├── dashboard.html                 # 8-card monitoring dashboard
│   ├── timeline.html                  # Gantt chart visualization
│   ├── run_synth_with_dashboard.py    # CLI + Dashboard launcher
│   └── README_DASHBOARD.md            # Dashboard documentation
│
├── examples/                          # Example scripts
│   ├── __init__.py
│   └── simple_chat.py                 # Basic usage demo
│
├── config/                            # Configuration files
│   ├── personality.yaml               # Personality profiles & module settings
│   └── peers.txt                      # Peer endpoints (optional)
│
├── docs/                              # Documentation
│   ├── QUICKSTART.md                  # 5-minute setup guide
│   ├── system-arch.md                 # High-level architecture
│   ├── GDIL_README.md                 # GDIL complete documentation
│   ├── PEER_SETUP.md                  # Multi-instance guide
│   └── Repository-Structure.md        # This file
│
├── tests/                             # Test suite
│   ├── conftest.py                    # Pytest configuration
│   ├── test_core_modules.py           # Core module tests
│   ├── test_psychological_modules.py  # Psychological module tests
│   ├── test_security_e2e.py           # Security E2E tests
│   └── test_mandelbrot_e2e.py         # Mandelbrot weighting tests
│
├── test_dashboard_integration.py      # Dashboard integration tests
├── test_gdil_integration.py           # GDIL integration tests
│
├── state/                             # Auto-generated on first run
│   ├── memory.db                      # SQLite episodic/semantic storage
│   ├── embeddings/                    # FAISS vector store
│   ├── synth.log                      # Application logs
│   └── access.log                     # HTTP access logs (if enabled)
│
└── certs/                             # Auto-generated (gitignored)
    ├── server.crt                     # SSL certificate
    └── server.key                     # SSL private key
```

## Directory Descriptions

### `/core`
Core components that form the foundation of Synth Mind:
- **orchestrator.py** - Main conversation loop integrating all modules
- **llm_wrapper.py** - Unified interface for Anthropic, OpenAI, and Ollama
- **memory.py** - SQLite + FAISS hybrid storage with semantic search
- **tools.py** - 10 sandboxed tools (calculator, web search, code execution, etc.)

### `/psychological`
The six psychological modules plus extended capabilities:
- **6 Core Modules** - Dreaming, Assurance, Reflection, Purpose, Calibration, Companionship
- **GDIL** - Goal-Directed Iteration Loop for project workflows
- **Templates** - 10 pre-built project templates
- **Collaboration** - Multi-agent project management
- **Federated Learning** - Privacy-preserving knowledge sharing

### `/utils`
Utility modules for security, logging, and analysis:
- **auth.py** - JWT authentication with role-based access
- **mandelbrot_weighting.py** - Information-theoretic word importance weighting
- **version_control.py** - Git integration with auto-commit
- **Security utilities** - SSL, rate limiting, firewall, access logging

### `/dashboard`
Real-time visualization web interface:
- **8-card WebSocket dashboard** for psychological state monitoring
- **Gantt chart timeline** for project visualization
- **REST API** for programmatic access

### `/tests`
Comprehensive test suite:
- Unit tests for core and psychological modules
- End-to-end security tests
- Integration tests for dashboard and GDIL

## Key Files by Size

| File | Lines | Description |
|------|-------|-------------|
| `core/tools.py` | 830+ | Tool manager with sandboxing |
| `core/memory.py` | 800+ | Memory system |
| `core/orchestrator.py` | 700+ | Main orchestrator |
| `psychological/collaborative_projects.py` | 600+ | Multi-agent collaboration |
| `psychological/goal_directed_iteration.py` | 526+ | GDIL system |
| `utils/mandelbrot_weighting.py` | 510+ | Word weighting |
| `psychological/federated_learning.py` | 450+ | Federated learning |
| `dashboard/server.py` | 430+ | Dashboard server |
| `utils/auth.py` | 350+ | JWT authentication |
