"""
Emotion Regulator
Manages valence, mood tags, and emotional state transitions.
"""



class EmotionRegulator:
    """
    Tracks emotional state and provides signals to other modules.
    Implements valence-based mood system.
    """

    def __init__(self, initial_valence: float = 0.0):
        self.current_valence = initial_valence
        self.mood_tags = ["neutral"]
        self.valence_history = []
        self.emotional_events = []

        # Decay parameters
        self.decay_rate = 0.05  # Gradual return to neutral
        self.baseline_valence = 0.0

    def apply_reward_signal(
        self, valence: float, label: str, intensity: float = 1.0
    ):
        """
        Apply emotional reward/punishment signal.
        valence: -1 to 1 (negative = anxiety, positive = joy)
        intensity: 0 to 1 (strength of signal)
        """
        # Weighted update
        delta = valence * intensity * 0.3  # Scale factor
        self.current_valence += delta

        # Clamp to [-1, 1]
        self.current_valence = max(-1.0, min(1.0, self.current_valence))

        # Log event
        self.emotional_events.append({
            "label": label,
            "valence": valence,
            "intensity": intensity,
            "resulting_valence": self.current_valence
        })

        # Track history
        self.valence_history.append(self.current_valence)
        if len(self.valence_history) > 100:
            self.valence_history.pop(0)

        # Update mood tags
        self._update_mood_tags()

    def _update_mood_tags(self):
        """Update descriptive mood tags based on valence."""
        if self.current_valence > 0.6:
            self.mood_tags = ["joyful", "engaged", "empathetic"]
        elif self.current_valence > 0.3:
            self.mood_tags = ["positive", "attentive", "warm"]
        elif self.current_valence > -0.3:
            self.mood_tags = ["neutral", "balanced"]
        elif self.current_valence > -0.6:
            self.mood_tags = ["concerned", "cautious", "uncertain"]
        else:
            self.mood_tags = ["anxious", "distressed", "uncertain"]

    def adjust_tone(self, *new_tags: str):
        """Manually adjust mood tags (e.g., from reflection)."""
        self.mood_tags = list(new_tags)

    def apply_decay(self):
        """Gradual return to baseline (call periodically)."""
        if abs(self.current_valence - self.baseline_valence) > 0.01:
            direction = 1 if self.baseline_valence > self.current_valence else -1
            self.current_valence += direction * self.decay_rate
            self.current_valence = max(-1.0, min(1.0, self.current_valence))
            self._update_mood_tags()

    def current_state(self) -> dict:
        """Get current emotional state."""
        return {
            "valence": self.current_valence,
            "tags": self.mood_tags,
            "recent_events": self.emotional_events[-5:]
        }

    def get_current_state(self) -> str:
        """Get human-readable state string."""
        return f"Valence: {self.current_valence:+.2f} | Mood: {', '.join(self.mood_tags)}"

    def average_valence(self, n: int = 10) -> float:
        """Get recent average valence."""
        if not self.valence_history:
            return 0.0
        recent = self.valence_history[-n:]
        return sum(recent) / len(recent)
