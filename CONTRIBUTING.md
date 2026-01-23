# Contributing to Synth Mind

Thank you for your interest in contributing to Synth Mind! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Architecture Overview](#architecture-overview)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/synth-mind.git
   cd synth-mind
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/kase1111-hash/synth-mind.git
   ```

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Git

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies with development extras:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

3. Set up your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=core --cov=psychological --cov=utils

# Run specific test file
pytest tests/test_core_modules.py -v
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes**: Fix issues and improve stability
- **New features**: Add new psychological modules, tools, or functionality
- **Documentation**: Improve or expand documentation
- **Tests**: Add test coverage or improve existing tests
- **Performance**: Optimize code or reduce resource usage
- **Refactoring**: Improve code quality without changing behavior

### Finding Issues to Work On

- Look for issues labeled `good first issue` for beginner-friendly tasks
- Issues labeled `help wanted` are actively seeking contributors
- Check the [Roadmap](README.md#roadmap) for planned features

## Code Style

### Python Style Guide

We follow PEP 8 with these project-specific conventions:

- **Line length**: Maximum 100 characters
- **Formatter**: Black (`black --line-length 100`)
- **Linter**: Ruff
- **Type hints**: Encouraged for all function signatures

### Running Code Quality Tools

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking (optional)
mypy core/ psychological/ utils/
```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Import Order

1. Standard library imports
2. Third-party imports
3. Local imports

Use `ruff` or `isort` to automatically organize imports.

## Testing

### Test Requirements

- All new features must include tests
- Bug fixes should include a regression test
- Maintain or improve code coverage

### Test Structure

```
tests/
├── test_core_modules.py         # Core functionality tests
├── test_psychological_modules.py # Psychological module tests
├── test_security_e2e.py         # End-to-end security tests
└── test_mandelbrot_e2e.py       # Mandelbrot weighting tests
```

### Writing Tests

```python
import pytest
from core.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test that orchestrator initializes correctly."""
    orchestrator = Orchestrator()
    assert orchestrator is not None
    assert orchestrator.memory is not None
```

## Pull Request Process

### Before Submitting

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   black .
   ruff check .
   pytest tests/ -v
   ```

3. **Update documentation** if needed

### PR Guidelines

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make focused commits** with clear messages:
   ```
   Add predictive alignment scoring to dreaming module

   - Implement alignment calculation using cosine similarity
   - Add tests for edge cases
   - Update documentation
   ```

3. **Write a clear PR description**:
   - Describe what changes were made
   - Explain why the changes are needed
   - Reference any related issues
   - Include testing instructions

4. **Keep PRs focused**: One feature or fix per PR

### Review Process

- PRs require at least one approving review
- Address all review comments
- Keep the PR updated with the main branch
- CI checks must pass before merging

## Issue Guidelines

### Bug Reports

When reporting bugs, include:

- **Description**: Clear summary of the issue
- **Steps to reproduce**: Minimal steps to trigger the bug
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: Python version, OS, relevant configuration
- **Logs/errors**: Any error messages or stack traces

### Feature Requests

When requesting features:

- **Problem statement**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches you thought of
- **Additional context**: Mockups, examples, or references

## Architecture Overview

Understanding the project structure helps make better contributions:

### Core Modules (`core/`)

- `orchestrator.py`: Main loop integrating all modules
- `llm_wrapper.py`: Multi-provider LLM interface
- `memory.py`: Hybrid vector + SQL memory system
- `tools.py`: Sandboxed tool implementations

### Psychological Modules (`psychological/`)

- `predictive_dreaming.py`: Anticipates user responses
- `assurance_resolution.py`: Manages uncertainty cycles
- `meta_reflection.py`: Periodic introspection
- `temporal_purpose.py`: Identity evolution
- `reward_calibration.py`: Flow state optimization
- `social_companionship.py`: Peer exchanges
- `goal_directed_iteration.py`: GDIL project system

### Utilities (`utils/`)

- `auth.py`: JWT authentication
- `emotion_regulator.py`: Valence tracking
- `metrics.py`: Performance tracking

### Key Design Principles

1. **Modularity**: Each module should be independently testable
2. **Async-first**: Use `async/await` for I/O operations
3. **Type safety**: Use type hints for clarity
4. **Error handling**: Use the centralized error handler in `security/error_handler.py`
5. **Logging**: Use the logging utilities in `utils/logging.py`

## Questions?

If you have questions about contributing:

- Open a [Discussion](https://github.com/kase1111-hash/synth-mind/discussions)
- Check existing [Issues](https://github.com/kase1111-hash/synth-mind/issues)
- Review the [Documentation](docs/)

Thank you for contributing to Synth Mind!
