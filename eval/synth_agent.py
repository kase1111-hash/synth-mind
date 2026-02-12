"""
Synth Agent — full psychological pipeline wrapped for evaluation.
Mirrors the orchestrator's _process_turn logic but returns structured
results instead of printing to console.
"""

from psychological.assurance_resolution import AssuranceResolutionModule
from psychological.meta_reflection import MetaReflectionModule
from psychological.predictive_dreaming import PredictiveDreamingModule
from psychological.reward_calibration import RewardCalibrationModule
from psychological.temporal_purpose import TemporalPurposeEngine
from utils.emotion_regulator import EmotionRegulator


class SynthAgent:
    """
    Treatment group for A/B evaluation.
    Full psychological pipeline: emotion, dreaming, assurance,
    reflection, calibration, temporal purpose — all wired into
    the system prompt and temperature.
    """

    def __init__(self, llm, memory, personality_prompt: str = None):
        self.llm = llm
        self.memory = memory
        self.personality_prompt = personality_prompt or (
            "You are a helpful, thoughtful AI assistant."
        )

        # Initialize all psychological modules
        self.emotion = EmotionRegulator()
        self.dreaming = PredictiveDreamingModule(llm, memory, self.emotion)
        self.assurance = AssuranceResolutionModule(llm, memory, self.emotion)
        self.temporal = TemporalPurposeEngine(memory, self.emotion, llm=llm)
        self.reflection = MetaReflectionModule(llm, memory, self.emotion, self.temporal)
        self.calibration = RewardCalibrationModule(
            self.emotion, memory, self.dreaming, self.assurance
        )

        self.context: list[dict] = []
        self.turn_count = 0

    async def respond(self, user_input: str) -> tuple[str, dict]:
        """
        Run full psychological pipeline and return (response, metrics).
        Mirrors orchestrator._process_turn without printing.
        """
        self.turn_count += 1

        # 1. Resolve previous dreams
        dream_alignment = 0.0
        if self.dreaming.dream_buffer:
            _, dream_alignment = self.dreaming.resolve_dreams(user_input)

        # 2. Update context
        self.context.append({"role": "user", "content": user_input})
        context_str = self._format_context()

        # 3. Build system prompt from psychological state
        system_prompt = self._build_system_prompt()

        # 4. Compute effective temperature
        base_temp = self.calibration.creativity_temperature
        emotion_delta = self.emotion.get_temperature_modifier()
        effective_temp = max(0.1, min(1.5, base_temp + emotion_delta))

        # 5. Generate response
        response = await self.llm.generate(
            context_str,
            temperature=effective_temp,
            system=system_prompt,
        )

        # 6. Run assurance cycle
        uncertainty, _ = self.assurance.run_cycle(
            response, context_str, {}, user_message=user_input
        )

        # 7. Run reflection cycle
        emotional_state = self.emotion.current_state()
        metrics = {
            "predictive_alignment": self.dreaming.recent_alignment_avg(),
            "assurance_success": self.assurance.assurance_success_rate(),
            "user_sentiment": 0.5,
        }
        await self.reflection.run_cycle(context_str, emotional_state, metrics)

        # 8. Calibration
        calib_state = self.calibration.run_cycle()

        # 9. Decay
        self.emotion.apply_decay()

        # 10. Update context and memory
        self.context.append({"role": "assistant", "content": response})
        self.memory.store_turn(user_input, response)

        # 11. Dream ahead
        await self.dreaming.dream_next_turn(self._format_context())

        # Collect metrics snapshot
        turn_metrics = {
            "system_prompt": system_prompt,
            "effective_temperature": effective_temp,
            "dream_alignment": dream_alignment,
            "uncertainty": uncertainty,
            "valence": self.emotion.current_valence,
            "arousal": self.emotion.current_arousal,
            "dominance": self.emotion.current_dominance,
            "mood_tags": list(self.emotion.mood_tags),
            "flow_state": calib_state["state"],
            "narrative": self.temporal.current_narrative_summary(),
        }

        return response, turn_metrics

    def _build_system_prompt(self) -> str:
        """Compose system prompt from all psychological module states."""
        sections = [self.personality_prompt]

        # Emotional state
        emotion_mod = self.emotion.get_system_prompt_modifier()
        if emotion_mod:
            sections.append(emotion_mod)

        # Narrative / identity
        narrative = self.temporal.current_narrative_summary()
        sections.append(f"Your current self-understanding: {narrative}")

        # Dream predictions
        if self.dreaming.dream_buffer:
            top_dream = max(self.dreaming.dream_buffer, key=lambda d: d["prob"])
            sections.append(
                f"You anticipated the user might say something like: "
                f"'{top_dream['text'][:100]}'. Adapt if reality differs."
            )

        # Reflection corrections
        corrective = self.reflection.get_corrective_instruction()
        if corrective:
            sections.append(f"Self-correction: {corrective}")

        # Assurance level
        recent_uncertainty = self.assurance.recent_uncertainty_avg()
        if recent_uncertainty > 0.7:
            sections.append(
                "You are uncertain about recent interactions. "
                "Be more careful, ask clarifying questions, hedge appropriately."
            )
        elif recent_uncertainty < 0.3:
            sections.append("You are confident in recent interactions. " "Be direct and helpful.")

        return "\n\n".join(sections)

    def reset(self):
        """Reset all state between scenarios."""
        self.context = []
        self.turn_count = 0
        self.emotion = EmotionRegulator()
        self.dreaming = PredictiveDreamingModule(self.llm, self.memory, self.emotion)
        self.assurance = AssuranceResolutionModule(self.llm, self.memory, self.emotion)
        self.temporal = TemporalPurposeEngine(self.memory, self.emotion, llm=self.llm)
        self.reflection = MetaReflectionModule(self.llm, self.memory, self.emotion, self.temporal)
        self.calibration = RewardCalibrationModule(
            self.emotion, self.memory, self.dreaming, self.assurance
        )

    def _format_context(self, window: int = 20) -> str:
        recent = self.context[-window:]
        return "\n".join(f"{msg['role'].title()}: {msg['content']}" for msg in recent)
