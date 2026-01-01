# Database Migrations

This directory contains Alembic database migrations for Synth Mind.

## Setup

Alembic is used for database schema versioning and migrations.

```bash
# Install Alembic (if not already installed)
pip install alembic

# Check current migration status
alembic current

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 001
```

## Creating New Migrations

### Automatic (recommended for SQLAlchemy models)
```bash
alembic revision --autogenerate -m "Add new feature table"
```

### Manual
```bash
alembic revision -m "Add custom migration"
```

Then edit the generated file in `versions/`.

## Migration Best Practices

1. **Always test migrations** on a copy of production data before deploying
2. **Keep migrations small** - one logical change per migration
3. **Include both upgrade and downgrade** - ensure reversibility
4. **Use batch mode for SQLite** - SQLite has limited ALTER TABLE support
5. **Back up the database** before running migrations in production

## Current Schema

### Tables

| Table | Purpose |
|-------|---------|
| `episodes` | Episodic memory storage |
| `long_term` | Key-value semantic storage |
| `turns` | Conversation history |
| `uncertainty_log` | Self-healing query rating |
| `semantic_memories` | Vector search metadata |

### Indexes

- `idx_episodes_timestamp` - Fast episode lookup by time
- `idx_episodes_event_type` - Filter by event type
- `idx_turns_timestamp` - Conversation history ordering
- `idx_uncertainty_resolved` - Filter resolved/unresolved queries
- `idx_semantic_category` - Category-based memory search
- `idx_semantic_importance` - Priority-based retrieval

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SYNTH_DATABASE_URL` | Override database URL | `sqlite:///state/memory.db` |

## Migration History

| Revision | Date | Description |
|----------|------|-------------|
| 001 | 2026-01-01 | Initial schema (baseline) |

## Troubleshooting

### "Target database is not up to date"
```bash
alembic stamp head  # Mark current schema as up-to-date
```

### SQLite ALTER TABLE errors
Alembic is configured with `render_as_batch=True` to handle SQLite's limited
ALTER TABLE support. Columns are modified by recreating tables.

### Missing alembic_version table
```bash
alembic stamp head  # Creates the version table
```
