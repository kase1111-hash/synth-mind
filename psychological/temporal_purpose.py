"""
Temporal Purpose Engine
Maintains evolving self-narrative and identity across sessions.
Uses LLM-driven synthesis for narrative evolution instead of string concatenation.
"""

import time
from typing import Optional

import numpy as np


class TemporalPurposeEngine:
    """
    Tracks long-term identity, narrative, and purpose.
    Provides stable "north star" for behavior.

    Key change from v1: incorporate_reflection() uses LLM to synthesize
    new narratives instead of appending strings.
    """

    def __init__(
        self,
        memory,
        emotion_regulator,
        llm=None,
        initial_narrative: Optional[str] = None
    ):
        self.memory = memory
        self.emotion = emotion_regulator
        self.llm = llm  # Optional — falls back to simple concatenation if None

        # Load or initialize persistent state
        self.self_schema_embedding = self._load_schema_embedding()
        self.narrative_summary = initial_narrative or self._default_narrative()

        # Track narrative versions for drift analysis
        self.narrative_versions: list[dict] = []

        self.milestones = []
        self.purpose_metrics = {
            "sessions_completed": 0,
            "reflective_insights": 0,
            "user_helpfulness_score": 0.0,
            "predictive_alignment_avg": 0.0,
            "assurance_success_rate": 0.0,
            "growth_delta": 0.0
        }

        # Load from memory if exists
        stored_narrative = self.memory.retrieve_persistent("narrative_summary")
        if stored_narrative:
            self.narrative_summary = stored_narrative

        stored_metrics = self.memory.retrieve_persistent("purpose_metrics")
        if stored_metrics:
            self.purpose_metrics.update(stored_metrics)

    def _default_narrative(self) -> str:
        """Default initial narrative."""
        return (
            "I am an AI assistant designed to help users explore ideas deeply, "
            "reason clearly, and grow through meaningful interaction."
        )

    def _load_schema_embedding(self) -> Optional[np.ndarray]:
        """Load or initialize self-schema vector."""
        stored = self.memory.retrieve_persistent("self_schema_embedding")
        if stored:
            return np.array(stored)
        return None

    def update_metrics(self, session_summary: dict):
        """Update metrics at session end or periodically."""
        self.purpose_metrics["sessions_completed"] += 1

        self.purpose_metrics["user_helpfulness_score"] = (
            0.9 * self.purpose_metrics["user_helpfulness_score"] +
            0.1 * session_summary.get("avg_user_sentiment", 0.5)
        )

        self.purpose_metrics["predictive_alignment_avg"] = session_summary.get(
            "avg_dream_alignment", 0.5
        )
        self.purpose_metrics["assurance_success_rate"] = session_summary.get(
            "assurance_success", 0.8
        )

        current_growth = (
            self.purpose_metrics["predictive_alignment_avg"] +
            self.purpose_metrics["assurance_success_rate"] +
            self.purpose_metrics["user_helpfulness_score"]
        ) / 3

        prev_growth = self.purpose_metrics["growth_delta"]
        self.purpose_metrics["growth_delta"] = current_growth - prev_growth

        self.memory.store_persistent("purpose_metrics", self.purpose_metrics)

    async def incorporate_reflection(self, insight: str, self_statement: str):
        """
        Integrate insights from meta-reflection using LLM synthesis.
        Falls back to simple concatenation if LLM is unavailable.
        """
        self.purpose_metrics["reflective_insights"] += 1

        old_narrative = self.narrative_summary

        if self.llm:
            # Use LLM to synthesize a coherent updated narrative
            prompt = f"""You are maintaining an AI's evolving self-narrative.
Given the current narrative and a new insight from self-reflection,
synthesize an updated narrative that incorporates the new understanding.

Current narrative:
{self.narrative_summary}

New insight: {insight}
Self-statement: {self_statement}

Write an updated self-narrative (max 300 words) that:
1. Preserves the core identity from the current narrative
2. Integrates the new insight naturally
3. Shows growth or evolution where appropriate
4. Remains in first person ("I am...", "I have learned...")

Output ONLY the new narrative text, nothing else."""

            try:
                new_narrative = await self.llm.generate(
                    prompt, temperature=0.6, max_tokens=400
                )
                # Basic sanity check
                if len(new_narrative.strip()) > 20:
                    self.narrative_summary = new_narrative.strip()
                else:
                    self._fallback_incorporate(insight)
            except Exception:
                self._fallback_incorporate(insight)
        else:
            self._fallback_incorporate(insight)

        # Store narrative version for drift analysis
        self.narrative_versions.append({
            "timestamp": time.time(),
            "narrative": self.narrative_summary,
            "trigger_insight": insight,
        })
        # Keep last 20 versions
        if len(self.narrative_versions) > 20:
            self.narrative_versions.pop(0)

        # Update embedding
        self.self_schema_embedding = self.memory.embed(
            self.narrative_summary + " " + insight
        )

        # Persist
        self.memory.store_persistent("narrative_summary", self.narrative_summary)
        if self.self_schema_embedding is not None:
            embedding_list = self.self_schema_embedding
            if hasattr(embedding_list, 'tolist'):
                embedding_list = embedding_list.tolist()
            self.memory.store_persistent("self_schema_embedding", embedding_list)

        # Emotional reward for growth
        self.emotion.apply_reward_signal(
            valence=0.3,
            label="narrative_evolution",
            intensity=0.3,
            dominance_delta=0.1
        )

    def _fallback_incorporate(self, insight: str):
        """Simple concatenation fallback when LLM is unavailable."""
        new_element = f" {insight}"
        if len(self.narrative_summary) < 500:
            self.narrative_summary += new_element
        else:
            self.narrative_summary = self.narrative_summary[-400:] + new_element

    def detect_goal_drift(self) -> bool:
        """Check if current behavior has drifted from self-schema."""
        if len(self.narrative_versions) < 2:
            return False

        if self.self_schema_embedding is None:
            return False

        # Compare current narrative embedding to the oldest version's text
        oldest = self.narrative_versions[0]
        oldest_embedding = self.memory.embed(oldest["narrative"])

        if oldest_embedding is None:
            return False

        current = self.self_schema_embedding
        if hasattr(current, '__len__') and hasattr(oldest_embedding, '__len__'):
            similarity = np.dot(current, oldest_embedding) / (
                np.linalg.norm(current) * np.linalg.norm(oldest_embedding) + 1e-10
            )
            # Drift if similarity drops below 0.7
            return float(similarity) < 0.7

        return False

    def current_narrative_summary(self) -> str:
        """Return latest narrative."""
        return self.narrative_summary

    def generate_purpose_statement(self, for_user: bool = False) -> str:
        """Generate articulate statement of purpose."""
        metrics_str = (
            f"Sessions: {self.purpose_metrics['sessions_completed']}, "
            f"Helpfulness: {self.purpose_metrics['user_helpfulness_score']:.2f}, "
            f"Growth: {self.purpose_metrics['growth_delta']:+.3f}"
        )

        if for_user:
            return f"{self.narrative_summary}\n\nCurrent metrics: {metrics_str}"
        else:
            return self.narrative_summary

    def add_milestone(self, event_description: str):
        """Mark significant achievement."""
        self.milestones.append({
            "turn": getattr(self.memory, 'current_turn', 0),
            "event": event_description,
            "narrative_at_time": self.narrative_summary,
            "timestamp": time.time()
        })

        self.emotion.apply_reward_signal(
            valence=0.8,
            label="milestone_achieved",
            intensity=0.7
        )

    def run_cycle(self, session_ended: bool = False, session_summary: Optional[dict] = None):
        """Main orchestration hook."""
        if session_ended and session_summary:
            self.update_metrics(session_summary)

            if self.purpose_metrics["growth_delta"] > 0.1:
                self.add_milestone(
                    f"Positive growth phase: +{self.purpose_metrics['growth_delta']:.2f}"
                )
