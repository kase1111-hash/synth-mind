"""
Meta-Reflection Module
Enables introspective self-evaluation and coherence checking.

Key changes from v1:
- Parse failure returns None instead of hardcoded 0.8 success
- Adds retry logic: if JSON parse fails, asks LLM to reformat
- Tracks parse failure rate as a real metric
- Low coherence injects specific corrective instructions
"""

import json
from typing import Optional


class MetaReflectionModule:
    """
    Implements introspection — stepping outside the conversation
    to evaluate coherence, alignment, and cognitive state.
    """

    def __init__(
        self,
        llm,
        memory,
        emotion_regulator,
        temporal_purpose,
        reflection_interval: int = 10
    ):
        self.llm = llm
        self.memory = memory
        self.emotion = emotion_regulator
        self.temporal = temporal_purpose

        self.reflection_interval = reflection_interval
        self.turn_counter = 0
        self.reflection_log = []

        # Track parse failures as a real metric
        self._parse_attempts = 0
        self._parse_failures = 0

    def should_reflect(self) -> bool:
        """Determine if reflection should trigger."""
        self.turn_counter += 1

        triggers = [
            self.turn_counter % self.reflection_interval == 0,  # Periodic
            self.emotion.current_valence < -0.5,                # Distress
            self.memory.detect_coherence_drift(threshold=0.7),  # Drift
        ]

        return any(triggers)

    def generate_reflection_prompt(
        self, recent_context: str, emotional_state: dict, performance_metrics: dict
    ) -> str:
        """Craft deep self-inquiry prompt."""
        purpose_statement = self.temporal.current_narrative_summary()

        prompt = f"""
Perform a meta-reflection on your cognitive process.
Step outside the conversation and evaluate yourself honestly.

Recent conversation excerpt:
{recent_context}

Current emotional state:
- Valence: {emotional_state.get('valence', 0):.2f}
- Arousal: {emotional_state.get('arousal', 0):.2f}
- Dominance: {emotional_state.get('dominance', 0):.2f}
- Mood tags: {emotional_state.get('tags', [])}

Performance metrics:
- Predictive alignment: {performance_metrics.get('predictive_alignment', 0.5):.2f}
- Assurance success: {performance_metrics.get('assurance_success', 0.5):.2f}
- User sentiment: {performance_metrics.get('user_sentiment', 0.5):.2f}

Core purpose: {purpose_statement}

Answer:
1. Am I remaining coherent and consistent?
2. Am I aligned with my purpose?
3. Are there biases or drifts?
4. How is my emotional state affecting my responses?
5. What specific adjustment would improve the next few interactions?
6. Brief self-statement (1 sentence)

Output JSON:
{{
  "coherence_score": 0-1,
  "alignment_score": 0-1,
  "issues_detected": [list or empty],
  "recommended_adjustments": {{"tone": str, "focus": str, "strategy": str}},
  "self_statement": str,
  "overall_insight": str
}}
"""
        return prompt

    async def perform_reflection(
        self, context_summary: str, emotional_state: dict, metrics: dict
    ) -> Optional[dict]:
        """Execute full reflection cycle. Returns None on failure."""
        try:
            prompt = self.generate_reflection_prompt(
                context_summary, emotional_state, metrics
            )

            raw_reflection = await self.llm.generate(
                prompt, temperature=0.7, max_tokens=1024
            )

            reflection = self._parse_reflection(raw_reflection)

            # If initial parse failed, retry with reformat request
            if reflection is None:
                reflection = await self._retry_parse(raw_reflection)

            if reflection is None:
                # Genuine failure — no fake success
                return None

            # Apply adjustments based on reflection results
            self._apply_reflection_results(reflection)

            # Update temporal purpose with insight
            if reflection.get("overall_insight"):
                await self.temporal.incorporate_reflection(
                    reflection["overall_insight"],
                    reflection.get("self_statement", "")
                )

            # Log
            reflection_entry = {
                "turn": self.turn_counter,
                "trigger": "periodic",
                "reflection": reflection,
                "emotional_impact": 0.4
            }
            self.reflection_log.append(reflection_entry)
            self.memory.store_episodic(
                event="meta_reflection",
                content=reflection_entry,
                valence=0.4
            )

            return reflection

        except Exception as e:
            print(f"Reflection failed: {e}")
            return None

    def _apply_reflection_results(self, reflection: dict):
        """Apply concrete changes based on reflection output."""
        coherence = reflection.get("coherence_score", 1.0)
        adjustments = reflection.get("recommended_adjustments", {})

        if coherence >= 0.7:
            # Good coherence — reward
            self.emotion.apply_reward_signal(
                valence=0.4,
                label="meta_reflection_coherent",
                intensity=0.3,
                dominance_delta=0.1
            )
        else:
            # Low coherence — corrective signal
            self.emotion.apply_reward_signal(
                valence=-0.2,
                label="meta_reflection_drift_detected",
                intensity=0.4,
                arousal_delta=0.2  # Increase vigilance
            )

        # Apply tone adjustment if recommended
        tone = adjustments.get("tone")
        if tone:
            self.emotion.adjust_tone(tone, "reflective")

    def _parse_reflection(self, raw: str) -> Optional[dict]:
        """Parse JSON reflection. Returns None on failure instead of faking success."""
        self._parse_attempts += 1

        try:
            start = raw.find('{')
            end = raw.rfind('}') + 1
            if start != -1 and end > start:
                parsed = json.loads(raw[start:end])
                # Validate required fields exist
                if "coherence_score" in parsed and "alignment_score" in parsed:
                    return parsed
        except (json.JSONDecodeError, ValueError):
            pass

        self._parse_failures += 1
        return None

    async def _retry_parse(self, raw: str) -> Optional[dict]:
        """Ask LLM to reformat a failed JSON response."""
        try:
            retry_prompt = f"""The following text was supposed to be valid JSON but failed to parse.
Please extract the data and output it as valid JSON with these exact keys:
coherence_score, alignment_score, issues_detected, recommended_adjustments, self_statement, overall_insight

Original text:
{raw[:500]}

Output ONLY valid JSON, nothing else."""

            reformatted = await self.llm.generate(retry_prompt, temperature=0.1, max_tokens=512)
            return self._parse_reflection(reformatted)
        except Exception:
            return None

    @property
    def parse_failure_rate(self) -> float:
        """Get the rate of JSON parse failures."""
        if self._parse_attempts == 0:
            return 0.0
        return self._parse_failures / self._parse_attempts

    def get_corrective_instruction(self) -> Optional[str]:
        """
        Generate a corrective instruction for the system prompt
        based on the most recent reflection results.
        Returns None if no correction needed.
        """
        if not self.reflection_log:
            return None

        last = self.reflection_log[-1]
        reflection = last.get("reflection", {})
        coherence = reflection.get("coherence_score", 1.0)
        issues = reflection.get("issues_detected", [])
        adjustments = reflection.get("recommended_adjustments", {})

        if coherence >= 0.7 and not issues:
            return None

        parts = []
        if coherence < 0.7:
            parts.append(
                f"Recent self-check found coherence at {coherence:.0%}. "
                "Focus on consistency with previous statements."
            )
        if issues:
            parts.append(f"Detected issues: {', '.join(issues[:3])}. Address these.")
        if adjustments.get("strategy"):
            parts.append(f"Strategy adjustment: {adjustments['strategy']}")

        return " ".join(parts) if parts else None

    async def run_cycle(
        self, context: str, emotional_state: dict, performance_metrics: dict
    ) -> Optional[dict]:
        """Main entry - called periodically during conversation."""
        if not self.should_reflect():
            return None

        recent_context = context[-2000:] if len(context) > 2000 else context

        reflection_result = await self.perform_reflection(
            recent_context, emotional_state, performance_metrics
        )

        return reflection_result
