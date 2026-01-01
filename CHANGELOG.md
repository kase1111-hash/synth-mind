# Changelog

All notable changes to Synth Mind will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-alpha] - 2026-01-01

> **First public alpha release** - Synth Mind is now production-ready for early adopters.

### Core Features

- **Six Psychological Modules**
  - Predictive Dreaming - Anticipates user responses, rewards alignment
  - Assurance & Resolution - Manages uncertainty with concern → relief cycles
  - Meta-Reflection - Periodic introspection and coherence checking
  - Temporal Purpose Engine - Maintains evolving self-narrative and identity
  - Reward Calibration - Tunes difficulty to maintain cognitive flow state
  - Social Companionship - Safe peer exchanges (no user data exposed)

- **GDIL System (Goal-Directed Iteration Loop)**
  - 4-phase project lifecycle (EXPLORE → PLAN → ITERATE → SHIP)
  - Progress tracking with diminishing returns detection
  - Exit conditions and blockers
  - 10 built-in project templates

- **Multi-LLM Support**
  - Anthropic Claude (recommended)
  - OpenAI GPT models
  - Local Ollama models

- **Hybrid Memory System**
  - SQLite + FAISS vector store
  - Sentence-transformers embeddings
  - Semantic search and coherence drift detection

### Dashboard & API

- **WebSocket Dashboard**
  - 8-card real-time monitoring
  - Project timeline/Gantt charts
  - Interactive controls

- **REST API**
  - 40+ endpoints documented in OpenAPI 3.1
  - Chat API with full cognitive pipeline
  - Prometheus metrics endpoint

### Security

- **Authentication**
  - JWT with role-based access control (admin, operator, viewer)
  - PBKDF2-SHA256 password hashing (100k iterations)
  - Token refresh mechanism

- **Protection Layers**
  - Rate limiting (tiered: auth 5/min, API 60/min)
  - IP firewall (whitelist/blacklist/peers modes)
  - HTTPS/WSS encryption with TLS 1.2+
  - Tool sandboxing with resource limits

- **Boundary Security Integration**
  - SIEM event reporting (HTTP API + CEF/Syslog)
  - Daemon policy enforcement (6 security modes)
  - Centralized error handling with violation detection

### DevOps & Deployment

- **Container Support**
  - Multi-stage Dockerfile
  - docker-compose for local development
  - Kubernetes Helm chart

- **CI/CD**
  - GitHub Actions pipeline (lint, test, security, build)
  - Automated Docker image builds

- **Monitoring**
  - Health check endpoints (/health, /health/live, /health/ready)
  - Prometheus metrics exposition
  - Grafana dashboards
  - k6 load testing scripts

- **Database**
  - Alembic migration framework
  - Initial schema with optimized indexes

### Platform Support

- **Windows**
  - `setup.bat` - Initial project setup
  - `start.bat` - CLI startup
  - `start_dashboard.bat` - Dashboard startup

- **Linux/macOS**
  - Standard Python virtualenv workflow
  - Shell-based startup scripts

### Collaboration

- **Multi-Agent Projects**
  - Task claiming and assignment
  - Inter-agent messaging
  - Project sync via API

- **Federated Learning**
  - Privacy-preserving pattern sharing
  - Differential privacy (ε=1.0)
  - K-anonymity enforcement

### Tools

- 10 sandboxed tools: calculator, web_search, code_execute, file_read, file_write, image_analyze, json_parse, text_summarize, translate, datetime
- Resource limits: 10s timeout, 100MB memory
- Restricted builtins for safe code execution

---

## Development History

Prior to v0.1.0-alpha, Synth Mind used internal versioning (1.0.0-1.8.0) during development.
This history is preserved for reference:

| Internal | Date | Highlights |
|----------|------|------------|
| 1.8.0 | 2026-01-01 | Boundary security integration, Windows .bat files |
| 1.7.0 | 2026-01-01 | Production infrastructure, Prometheus, OpenAPI |
| 1.6.0 | 2025-12-31 | Documentation consolidation |
| 1.5.0 | 2025-12-30 | Security hardening (firewall, rate limiting, HTTPS) |
| 1.4.0 | 2025-12-28 | Mandelbrot weighting, /api/chat |
| 1.3.0 | 2025-12-25 | JWT auth, Gantt charts, VCS integration |
| 1.2.0 | 2025-12-20 | Collaboration, templates, federated learning |
| 1.1.0 | 2025-12-15 | Multi-project, tools, embeddings |
| 1.0.0 | 2025-12-01 | Initial internal release |

---

## Upgrading

### Fresh Install (Recommended for Alpha)

```bash
git clone https://github.com/yourusername/synth-mind.git
cd synth-mind
pip install -r requirements.txt
```

### Docker Deployment

```bash
docker-compose up
```

### Database Migrations (if upgrading from development builds)

```bash
pip install alembic
alembic upgrade head
```

---

## Known Issues

- WebSocket connections may timeout after extended idle periods
- Ollama local models require manual installation
- Collaborative features require network connectivity between peers

---

## Roadmap to v1.0.0

- [ ] Comprehensive integration test suite
- [ ] PostgreSQL support for multi-instance deployments
- [ ] Plugin system for custom psychological modules
- [ ] Web-based admin interface
- [ ] Mobile-responsive dashboard
