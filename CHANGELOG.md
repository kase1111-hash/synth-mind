# Changelog

All notable changes to Synth Mind will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.0] - 2026-01-01

### Added

- **Production Readiness Infrastructure**
  - Health check endpoints (`/health`, `/health/live`, `/health/ready`) for Kubernetes
  - Prometheus metrics endpoint (`/metrics`) for monitoring
  - Dockerfile with multi-stage build
  - docker-compose.yml for local development
  - GitHub Actions CI/CD pipeline (lint, test, security scan, Docker build)

- **API Documentation**
  - OpenAPI 3.1 specification (`docs/openapi.yaml`)
  - Complete documentation for all 40+ endpoints

- **Database Migrations**
  - Alembic migration framework setup
  - Initial schema migration with indexes

### Changed

- Updated PRODUCTION_READINESS.md with completed items
- Production readiness improved from 70% to 95%

## [1.6.0] - 2025-12-31

### Added

- **Comprehensive Documentation Update**
  - Consolidated documentation in `/docs` folder
  - Updated SPEC_SHEET.md with current implementation status
  - Added Repository-Structure.md

### Changed

- Updated GDIL documentation to reflect implemented features
- Cleaned up redundant documentation files

## [1.5.0] - 2025-12-30

### Added

- **Security Hardening**
  - IP firewall with whitelist/blacklist/peers-only modes
  - HTTP access logging with multiple formats (JSON, Common, Combined)
  - Rate limiting with tiered limits (auth: 5/min, API: 60/min)
  - HTTPS/WSS encryption support with auto-generated dev certificates

- **Security Test Suite**
  - End-to-end security tests for command injection
  - Code execution sandbox tests
  - Path traversal protection tests

### Fixed

- All medium severity security issues (eval, CORS, auto-install)
- All low severity security issues (gitignore, token blacklist)

## [1.4.0] - 2025-12-28

### Added

- **Mandelbrot-Zipf Word Weighting**
  - Information-theoretic word importance scoring
  - Stopword handling with minimum weights
  - Domain boost support for technical terms
  - Integration with Assurance Resolution module

- **Chat API Endpoint**
  - `/api/chat` for full cognitive pipeline integration
  - Returns response with emotional state

### Changed

- Improved intent detection accuracy with weighted word matching

## [1.3.0] - 2025-12-25

### Added

- **JWT Authentication**
  - Role-based access control (admin, operator, viewer)
  - PBKDF2-SHA256 password hashing (100k iterations)
  - Token refresh mechanism
  - User management API

- **Visual Timeline/Gantt Charts**
  - Interactive project visualization
  - Task status colors and tooltips
  - Multi-project view

- **Version Control Integration**
  - Git auto-commit on project milestones
  - Rollback capability
  - `/vcs` CLI commands

## [1.2.0] - 2025-12-20

### Added

- **Collaborative Multi-Agent Projects**
  - Task claiming and assignment
  - Inter-agent messaging
  - Project sync via API
  - Agent roles (coordinator, contributor, reviewer)

- **Project Templates**
  - 10 built-in templates (web-app, api, data-analysis, etc.)
  - Pre-defined roadmaps and clarification questions
  - `/templates` and `/project template` commands

- **Federated Learning**
  - Privacy-preserving pattern sharing
  - Differential privacy (ε=1.0)
  - K-anonymity enforcement

## [1.1.0] - 2025-12-15

### Added

- **Multiple Concurrent Projects**
  - Support for up to 5 active projects
  - Project switching and pausing
  - `/projects`, `/project switch`, `/project pause` commands

- **Advanced Tool Manager**
  - 10 sandboxed tools (calculator, web_search, code_execute, etc.)
  - Resource limits (10s timeout, 100MB memory)
  - Restricted builtins for code execution

- **Memory Embeddings**
  - sentence-transformers integration (all-MiniLM-L6-v2)
  - OpenAI embeddings fallback
  - Semantic search and grounding confidence
  - Coherence drift detection

## [1.0.0] - 2025-12-01

### Added

- **Core Architecture**
  - Main orchestrator with module integration
  - LLM wrapper (Anthropic, OpenAI, Ollama support)
  - Hybrid memory system (SQLite + FAISS)

- **Six Psychological Modules**
  - Predictive Dreaming (anticipation + alignment scoring)
  - Assurance & Resolution (uncertainty → relief cycles)
  - Meta-Reflection (periodic introspection)
  - Temporal Purpose Engine (identity evolution)
  - Reward Calibration (flow state optimization)
  - Social Companionship (peer grounding)

- **GDIL System**
  - 4-phase project lifecycle
  - Progress tracking with diminishing returns detection
  - Exit conditions and blockers

- **Dashboard**
  - 8-card WebSocket monitoring
  - Real-time state updates
  - REST API for programmatic access

- **CLI Interface**
  - Full command support (/state, /dream, /project, etc.)
  - Signal handling for graceful shutdown

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 1.7.0 | 2026-01-01 | Production infrastructure, Prometheus, OpenAPI |
| 1.6.0 | 2025-12-31 | Documentation consolidation |
| 1.5.0 | 2025-12-30 | Security hardening (firewall, rate limiting, HTTPS) |
| 1.4.0 | 2025-12-28 | Mandelbrot weighting, /api/chat |
| 1.3.0 | 2025-12-25 | JWT auth, Gantt charts, VCS integration |
| 1.2.0 | 2025-12-20 | Collaboration, templates, federated learning |
| 1.1.0 | 2025-12-15 | Multi-project, tools, embeddings |
| 1.0.0 | 2025-12-01 | Initial release |

---

## Upgrading

### From 1.6.x to 1.7.x

1. Install new dependencies:
   ```bash
   pip install alembic
   ```

2. Run database migrations (optional, for new indexes):
   ```bash
   alembic upgrade head
   ```

3. Docker deployment now available:
   ```bash
   docker-compose up
   ```

### From 1.4.x to 1.5.x

No breaking changes. Rate limiting and HTTPS are optional features.

### From 1.0.x to 1.1.x

Memory system upgraded. Existing memories are preserved but new indexes are created on first run.
