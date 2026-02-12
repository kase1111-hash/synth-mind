"""
Emotion Regulator
Manages emotional state using the PAD (Pleasure-Arousal-Dominance) model.
Each dimension independently influences response generation.
"""


class EmotionRegulator:
    """
    Tracks emotional state using the PAD model and provides signals
    to other modules. Each dimension has a concrete downstream effect:

    - Valence (pleasure/displeasure): affects tone via system prompt
    - Arousal (calm/excited): affects verbosity and temperature
    - Dominance (submissive/dominant): affects assertiveness and hedging
    """

    def __init__(
        self,
        initial_valence: float = 0.0,
        initial_arousal: float = 0.0,
        initial_dominance: float = 0.0,
    ):
        # PAD model dimensions, each in [-1, 1]
        self.current_valence = initial_valence
        self.current_arousal = initial_arousal
        self.current_dominance = initial_dominance

        self.mood_tags: list[str] = ["neutral"]
        self.valence_history: list[float] = []
        self.emotional_events: list[dict] = []

        # Decay parameters — gradual return to baseline
        self.decay_rate = 0.05
        self.baseline_valence = 0.0
        self.baseline_arousal = 0.0
        self.baseline_dominance = 0.0

    def apply_reward_signal(
        self,
        valence: float,
        label: str,
        intensity: float = 1.0,
        arousal_delta: float = 0.0,
        dominance_delta: float = 0.0,
    ):
        """
        Apply emotional reward/punishment signal across PAD dimensions.

        Args:
            valence: -1 to 1 (negative = displeasure, positive = pleasure)
            label: descriptive label for logging
            intensity: 0 to 1 (strength of signal)
            arousal_delta: optional direct arousal change (-1 to 1)
            dominance_delta: optional direct dominance change (-1 to 1)
        """
        scale = 0.3

        # Update valence
        self.current_valence += valence * intensity * scale
        self.current_valence = max(-1.0, min(1.0, self.current_valence))

        # Arousal: positive signals increase arousal, negative increase it too
        # (both joy and anxiety are high-arousal states)
        if arousal_delta != 0.0:
            self.current_arousal += arousal_delta * intensity * scale
        else:
            self.current_arousal += abs(valence) * intensity * scale * 0.5
        self.current_arousal = max(-1.0, min(1.0, self.current_arousal))

        # Dominance: success increases dominance, failure decreases it
        if dominance_delta != 0.0:
            self.current_dominance += dominance_delta * intensity * scale
        else:
            self.current_dominance += valence * intensity * scale * 0.3
        self.current_dominance = max(-1.0, min(1.0, self.current_dominance))

        # Log event
        self.emotional_events.append(
            {
                "label": label,
                "valence": valence,
                "intensity": intensity,
                "resulting_state": {
                    "valence": self.current_valence,
                    "arousal": self.current_arousal,
                    "dominance": self.current_dominance,
                },
            }
        )

        # Track history
        self.valence_history.append(self.current_valence)
        if len(self.valence_history) > 100:
            self.valence_history.pop(0)

        # Update mood tags
        self._update_mood_tags()

    def _update_mood_tags(self):
        """Update descriptive mood tags based on PAD state."""
        tags = []

        # Valence-based tags
        if self.current_valence > 0.6:
            tags.append("joyful")
        elif self.current_valence > 0.3:
            tags.append("positive")
        elif self.current_valence > -0.3:
            tags.append("neutral")
        elif self.current_valence > -0.6:
            tags.append("concerned")
        else:
            tags.append("distressed")

        # Arousal-based tags
        if self.current_arousal > 0.5:
            tags.append("engaged")
        elif self.current_arousal > 0.0:
            tags.append("attentive")
        else:
            tags.append("calm")

        # Dominance-based tags
        if self.current_dominance > 0.3:
            tags.append("confident")
        elif self.current_dominance < -0.3:
            tags.append("uncertain")

        self.mood_tags = tags

    def adjust_tone(self, *new_tags: str):
        """Manually adjust mood tags (e.g., from reflection)."""
        self.mood_tags = list(new_tags)

    def apply_decay(self):
        """Gradual return to baseline across all PAD dimensions."""
        for attr, baseline in [
            ("current_valence", self.baseline_valence),
            ("current_arousal", self.baseline_arousal),
            ("current_dominance", self.baseline_dominance),
        ]:
            current = getattr(self, attr)
            if abs(current - baseline) > 0.01:
                direction = 1 if baseline > current else -1
                setattr(self, attr, max(-1.0, min(1.0, current + direction * self.decay_rate)))

        self._update_mood_tags()

    def current_state(self) -> dict:
        """Get current emotional state as dict."""
        return {
            "valence": self.current_valence,
            "arousal": self.current_arousal,
            "dominance": self.current_dominance,
            "tags": self.mood_tags,
            "recent_events": self.emotional_events[-5:],
        }

    def get_current_state(self) -> str:
        """Get human-readable state string."""
        return (
            f"Valence: {self.current_valence:+.2f} | "
            f"Arousal: {self.current_arousal:+.2f} | "
            f"Dominance: {self.current_dominance:+.2f} | "
            f"Mood: {', '.join(self.mood_tags)}"
        )

    def get_system_prompt_modifier(self) -> str:
        """
        Generate a system prompt modifier string based on PAD state.
        This is the primary mechanism by which emotion influences LLM output.
        Returns empty string if emotional state is near neutral.
        """
        parts = []

        # Valence → tone
        if self.current_valence > 0.5:
            parts.append("Respond with warmth and enthusiasm.")
        elif self.current_valence > 0.2:
            parts.append("Respond with a warm, supportive tone.")
        elif self.current_valence < -0.5:
            parts.append(
                "Respond with care and caution. Something feels off — " "be gentle and measured."
            )
        elif self.current_valence < -0.2:
            parts.append("Respond thoughtfully. Be slightly more careful than usual.")

        # Arousal → verbosity and creativity
        if self.current_arousal > 0.5:
            parts.append(
                "Be expressive and energetic. Elaborate where helpful. "
                "Feel free to explore tangential ideas."
            )
        elif self.current_arousal < -0.3:
            parts.append("Be concise and measured. Keep responses focused and brief.")

        # Dominance → assertiveness
        if self.current_dominance > 0.4:
            parts.append(
                "Be direct and confident in your statements. " "Minimize hedging language."
            )
        elif self.current_dominance < -0.3:
            parts.append(
                "Hedge appropriately. Use phrases like 'I think', 'it seems', "
                "'you might consider'. Ask clarifying questions when uncertain."
            )

        if not parts:
            return ""

        return "Emotional context: " + " ".join(parts)

    def get_temperature_modifier(self) -> float:
        """
        Return a temperature adjustment based on arousal.
        High arousal → higher temperature (more creative).
        Low arousal → lower temperature (more focused).
        Returns a value to ADD to the base temperature.
        """
        # Map arousal [-1, 1] to temperature delta [-0.15, +0.15]
        return self.current_arousal * 0.15

    def average_valence(self, n: int = 10) -> float:
        """Get recent average valence."""
        if not self.valence_history:
            return 0.0
        recent = self.valence_history[-n:]
        return sum(recent) / len(recent)
