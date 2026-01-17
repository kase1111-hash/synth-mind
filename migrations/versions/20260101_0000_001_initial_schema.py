"""Initial schema - baseline migration

This migration documents the initial database schema for Synth Mind.
It creates the core tables used by the memory system.

Revision ID: 001
Revises: None
Create Date: 2026-01-01

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create initial database schema.

    Tables:
    - episodes: Episodic memory storage
    - long_term: Key-value long-term semantic storage
    - turns: Conversation turn history
    - uncertainty_log: Self-healing query rating system
    - semantic_memories: Vector search metadata
    """

    # Episodic memory table
    op.create_table(
        'episodes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.Float(), nullable=True),
        sa.Column('event_type', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('valence', sa.Float(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
    )

    # Long-term semantic storage
    op.create_table(
        'long_term',
        sa.Column('key', sa.Text(), primary_key=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Float(), nullable=True),
    )

    # Conversation turns
    op.create_table(
        'turns',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.Float(), nullable=True),
        sa.Column('user_input', sa.Text(), nullable=True),
        sa.Column('assistant_response', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
    )

    # Uncertainty log for self-healing (Query Rating system)
    op.create_table(
        'uncertainty_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.Float(), nullable=True),
        sa.Column('user_message', sa.Text(), nullable=True),
        sa.Column('parsed_intent', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('signals', sa.Text(), nullable=True),
        sa.Column('resolved', sa.Integer(), server_default='0'),
        sa.Column('resolution_pattern', sa.Text(), nullable=True),
    )

    # Semantic memories for vector search
    op.create_table(
        'semantic_memories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.Float(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('category', sa.Text(), nullable=True),
        sa.Column('importance', sa.Float(), server_default='0.5'),
        sa.Column('metadata', sa.Text(), nullable=True),
    )

    # Create indexes for common queries
    op.create_index('idx_episodes_timestamp', 'episodes', ['timestamp'])
    op.create_index('idx_episodes_event_type', 'episodes', ['event_type'])
    op.create_index('idx_turns_timestamp', 'turns', ['timestamp'])
    op.create_index('idx_uncertainty_resolved', 'uncertainty_log', ['resolved'])
    op.create_index('idx_semantic_category', 'semantic_memories', ['category'])
    op.create_index('idx_semantic_importance', 'semantic_memories', ['importance'])


def downgrade() -> None:
    """Remove all tables."""
    op.drop_index('idx_semantic_importance', 'semantic_memories')
    op.drop_index('idx_semantic_category', 'semantic_memories')
    op.drop_index('idx_uncertainty_resolved', 'uncertainty_log')
    op.drop_index('idx_turns_timestamp', 'turns')
    op.drop_index('idx_episodes_event_type', 'episodes')
    op.drop_index('idx_episodes_timestamp', 'episodes')

    op.drop_table('semantic_memories')
    op.drop_table('uncertainty_log')
    op.drop_table('turns')
    op.drop_table('long_term')
    op.drop_table('episodes')
