"""
Reward Calibration Module
Tunes task difficulty to maintain optimal cognitive flow.
"""


class RewardCalibrationModule:
    """
    Implements flow-state optimization by monitoring task difficulty
    and adjusting internal parameters.

    Temperature range: 0.3-1.0 (wider than before for perceptible effects).
    Context load uses turn count as a proxy instead of a non-existent attribute.
    """

    def __init__(
        self,
        emotion_regulator,
        memory,
        predictive_dreaming,
        assurance_module,
        target_flow_range: tuple[float, float] = (0.4, 0.7),
    ):
        self.emotion = emotion_regulator
        self.memory = memory
        self.dreaming = predictive_dreaming
        self.assurance = assurance_module

        self.target_min, self.target_max = target_flow_range

        # Running averages
        self.difficulty_moving_avg = 0.5
        self.alpha = 0.1  # Smoothing factor

        # Adjustable parameters — wider range for perceptible effects
        self.persistence_factor = 1.0
        self.creativity_temperature = 0.7
        self.rejection_threshold = 0.9
        self.exploration_bonus = 0.2

        # Track difficulty estimates for validation
        self.difficulty_history: list[float] = []

    def estimate_task_difficulty(self) -> tuple[float, dict]:
        """
        Compute normalized difficulty [0,1] from multiple signals.
        0 = trivial, 1 = overwhelming
        """
        signals = {}

        # 1. Predictive alignment (inverse) — low alignment = hard to predict
        recent_alignment = self.dreaming.recent_alignment_avg(n=5)
        signals["predictive"] = 1.0 - recent_alignment

        # 2. Assurance uncertainty — high uncertainty = hard
        recent_uncertainty = self.assurance.recent_uncertainty_avg(n=5)
        signals["uncertainty"] = recent_uncertainty

        # 3. Context load — use memory's current_turn as proxy for complexity
        turn_count = getattr(self.memory, "current_turn", 0)
        context_ratio = min(turn_count / 50.0, 1.0)
        signals["context_load"] = context_ratio

        # Weighted aggregate
        difficulty = (
            0.4 * signals["predictive"]
            + 0.4 * signals["uncertainty"]
            + 0.2 * signals["context_load"]
        )

        return difficulty, signals

    def update_flow_state(self, difficulty: float) -> dict:
        """Update moving average and apply calibration adjustments."""
        # Exponential moving average
        self.difficulty_moving_avg = (
            self.alpha * difficulty + (1 - self.alpha) * self.difficulty_moving_avg
        )

        # Track history
        self.difficulty_history.append(self.difficulty_moving_avg)
        if len(self.difficulty_history) > 100:
            self.difficulty_history.pop(0)

        flow_deviation = 0.0
        adjustment_label = "balanced"

        if self.difficulty_moving_avg < self.target_min:
            # Too easy → boredom risk
            flow_deviation = self.target_min - self.difficulty_moving_avg
            adjustment_label = "bored"

            # Increase creativity (wider range: up to 1.0)
            self.creativity_temperature = min(
                1.0, self.creativity_temperature + 0.1 * flow_deviation
            )
            self.exploration_bonus += 0.1 * flow_deviation
            self.persistence_factor = max(1.3, self.persistence_factor + 0.15 * flow_deviation)

        elif self.difficulty_moving_avg > self.target_max:
            # Too hard → overload risk
            flow_deviation = self.difficulty_moving_avg - self.target_max
            adjustment_label = "overloaded"

            # Reduce temperature (wider range: down to 0.3)
            self.creativity_temperature = max(
                0.3, self.creativity_temperature - 0.1 * flow_deviation
            )
            self.persistence_factor = min(0.7, self.persistence_factor - 0.15 * flow_deviation)
            self.rejection_threshold = min(0.95, self.rejection_threshold + 0.05 * flow_deviation)

        else:
            # In flow
            adjustment_label = "flow"
            flow_deviation = 0.0
            self.exploration_bonus = 0.2

        # Apply emotional reward based on flow proximity
        target_center = (self.target_min + self.target_max) / 2
        flow_reward = 1.0 - abs(self.difficulty_moving_avg - target_center) * 2

        self.emotion.apply_reward_signal(
            valence=flow_reward * 0.6,
            label=f"flow_state_{adjustment_label}",
            intensity=flow_reward * 0.5,
        )

        return {
            "current_difficulty": difficulty,
            "moving_avg": self.difficulty_moving_avg,
            "state": adjustment_label,
            "temperature": self.creativity_temperature,
            "persistence": self.persistence_factor,
            "rejection_threshold": self.rejection_threshold,
            "should_suggest_simplification": difficulty > self.rejection_threshold,
        }

    def run_cycle(self) -> dict:
        """Main hook - called after each turn or reasoning step."""
        difficulty, signals = self.estimate_task_difficulty()
        calibration_state = self.update_flow_state(difficulty)

        # Log
        self.memory.store_episodic(
            event="flow_calibration", content=calibration_state | {"signals": signals}
        )

        return calibration_state
