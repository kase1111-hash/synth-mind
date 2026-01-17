"""
Temporal Purpose Engine
Maintains evolving self-narrative and identity across sessions.
"""

import time
from typing import Optional

import numpy as np


class TemporalPurposeEngine:
    """
    Tracks long-term identity, narrative, and purpose.
    Provides stable "north star" for behavior.
    """

    def __init__(
        self,
        memory,
        emotion_regulator,
        initial_narrative: Optional[str] = None
    ):
        self.memory = memory
        self.emotion = emotion_regulator

        # Load or initialize persistent state
        self.self_schema_embedding = self._load_schema_embedding()
        self.narrative_summary = initial_narrative or self._default_narrative()

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

        # Exponential moving average for helpfulness
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

        # Compute growth delta
        current_growth = (
            self.purpose_metrics["predictive_alignment_avg"] +
            self.purpose_metrics["assurance_success_rate"] +
            self.purpose_metrics["user_helpfulness_score"]
        ) / 3

        prev_growth = self.purpose_metrics["growth_delta"]
        self.purpose_metrics["growth_delta"] = current_growth - prev_growth

        # Persist
        self.memory.store_persistent("purpose_metrics", self.purpose_metrics)

    def incorporate_reflection(self, insight: str, self_statement: str):
        """Integrate insights from meta-reflection."""
        self.purpose_metrics["reflective_insights"] += 1

        # Evolve narrative incrementally
        # In production: use LLM to synthesize
        # For now: simple append with trimming
        new_element = f" {insight}"
        if len(self.narrative_summary) < 500:
            self.narrative_summary += new_element
        else:
            # Keep last 400 chars + new
            self.narrative_summary = self.narrative_summary[-400:] + new_element

        # Update embedding
        self.self_schema_embedding = self.memory.embed(
            self.narrative_summary + " " + insight
        )

        # Persist
        self.memory.store_persistent("narrative_summary", self.narrative_summary)
        self.memory.store_persistent(
            "self_schema_embedding",
            self.self_schema_embedding.tolist()
        )

    def detect_goal_drift(self) -> bool:
        """Check if current behavior aligns with self-schema."""
        # Simplified: always aligned for now
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
            "turn": self.memory.current_turn,
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

            # Check for milestone
            if self.purpose_metrics["growth_delta"] > 0.1:
                self.add_milestone(
                    f"Positive growth phase: +{self.purpose_metrics['growth_delta']:.2f}"
                )
