"""
Unit tests for psychological modules.
Tests predictive dreaming, meta-reflection, reward calibration, and emotion regulation.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class MockLLM:
    """Mock LLM for testing."""

    async def generate(self, prompt, temperature=0.7, max_tokens=1000, system=None):
        """Return mock LLM response based on prompt content."""
        if "simulate" in prompt.lower() and "next user messages" in prompt.lower():
            return '''[
                {"text": "Can you explain that further?", "probability": 0.4},
                {"text": "That sounds good, thanks!", "probability": 0.3},
                {"text": "What about the edge cases?", "probability": 0.2},
                {"text": "I'm not sure I understand.", "probability": 0.1}
            ]'''
        elif "meta-reflection" in prompt.lower() or "evaluate yourself" in prompt.lower():
            return '''{
                "coherence_score": 0.85,
                "alignment_score": 0.9,
                "issues_detected": [],
                "recommended_adjustments": {"tone": "engaged", "focus": "clarity", "strategy": "continue"},
                "self_statement": "Operating effectively",
                "overall_insight": "Maintaining coherent dialogue"
            }'''
        return "Mock response"


class MockMemory:
    """Mock memory system for testing."""

    def __init__(self):
        self.episodic_store = []
        self.embeddings = {}

    def embed(self, text):
        """Return mock embedding."""
        import numpy as np
        # Simple hash-based deterministic embedding
        hash_val = hash(text) % 1000000
        np.random.seed(hash_val)
        return np.random.randn(384)

    def store_episodic(self, event, content, valence=0.0):
        self.episodic_store.append({
            "event": event,
            "content": content,
            "valence": valence
        })

    def detect_coherence_drift(self, threshold=0.7):
        return False

    def grounding_confidence(self, text):
        return 0.8


class MockEmotionRegulator:
    """Mock emotion regulator for testing."""

    def __init__(self):
        self.current_valence = 0.5
        self.signals = []
        self.tone_adjustments = []

    def apply_reward_signal(self, valence, label, intensity):
        self.signals.append({
            "valence": valence,
            "label": label,
            "intensity": intensity
        })
        self.current_valence += valence * intensity * 0.1

    def adjust_tone(self, *args):
        self.tone_adjustments.append(args)

    def current_state(self):
        return {
            "valence": self.current_valence,
            "tags": ["neutral"]
        }

    def get_current_state(self):
        return self.current_state()


class MockTemporalPurpose:
    """Mock temporal purpose engine for testing."""

    def __init__(self):
        self.narrative_summary = "Test narrative"
        self.reflections = []

    def current_narrative_summary(self):
        return self.narrative_summary

    def incorporate_reflection(self, insight, statement):
        self.reflections.append((insight, statement))


# =============================================================================
# Predictive Dreaming Tests
# =============================================================================

class TestPredictiveDreaming:
    """Tests for PredictiveDreamingModule."""

    @pytest.fixture
    def module(self):
        from psychological.predictive_dreaming import PredictiveDreamingModule
        return PredictiveDreamingModule(
            llm=MockLLM(),
            memory=MockMemory(),
            emotion_regulator=MockEmotionRegulator(),
            reward_weight=0.5
        )

    @pytest.mark.asyncio
    async def test_dream_next_turn_generates_dreams(self, module):
        """Test that dream_next_turn generates dream predictions."""
        context = "User: Hello\nAssistant: Hi there!"

        await module.dream_next_turn(context, n_dreams=4)

        assert len(module.dream_buffer) == 4
        for dream in module.dream_buffer:
            assert "text" in dream
            assert "prob" in dream
            assert "embedding" in dream
            assert not dream["rewarded"]

    def test_resolve_dreams_computes_alignment(self, module):
        """Test that resolve_dreams computes alignment scores."""
        import numpy as np

        # Add some mock dreams
        module.dream_buffer = [
            {"text": "Thank you!", "prob": 0.5, "embedding": np.random.randn(384), "rewarded": False},
            {"text": "Can you help?", "prob": 0.5, "embedding": np.random.randn(384), "rewarded": False}
        ]

        reward, alignment = module.resolve_dreams("Thank you so much!")

        assert 0 <= reward <= 1
        assert 0 <= alignment <= 1
        assert len(module.dream_buffer) == 0  # Buffer should be cleared
        assert len(module.alignment_history) == 1

    def test_resolve_dreams_empty_buffer(self, module):
        """Test that resolve_dreams handles empty buffer."""
        reward, alignment = module.resolve_dreams("Any input")

        assert reward == 0.0
        assert alignment == 0.0

    def test_recent_alignment_avg(self, module):
        """Test alignment average calculation."""
        module.alignment_history = [0.5, 0.6, 0.7, 0.8, 0.9]

        avg = module.recent_alignment_avg(n=3)

        assert abs(avg - 0.8) < 0.01  # (0.7 + 0.8 + 0.9) / 3

    def test_recent_alignment_avg_empty(self, module):
        """Test alignment average with no history."""
        avg = module.recent_alignment_avg()

        assert avg == 0.5  # Default value


# =============================================================================
# Meta Reflection Tests
# =============================================================================

class TestMetaReflection:
    """Tests for MetaReflectionModule."""

    @pytest.fixture
    def module(self):
        from psychological.meta_reflection import MetaReflectionModule
        return MetaReflectionModule(
            llm=MockLLM(),
            memory=MockMemory(),
            emotion_regulator=MockEmotionRegulator(),
            temporal_purpose=MockTemporalPurpose(),
            reflection_interval=5
        )

    def test_should_reflect_periodic(self, module):
        """Test periodic reflection trigger."""
        # Not time yet
        for _ in range(4):
            assert not module.should_reflect()

        # Now it's time (5th turn)
        assert module.should_reflect()

    def test_should_reflect_distress(self, module):
        """Test distress-triggered reflection."""
        module.emotion.current_valence = -0.6  # Distress

        assert module.should_reflect()

    @pytest.mark.asyncio
    async def test_perform_reflection(self, module):
        """Test reflection execution."""
        result = await module.perform_reflection(
            context_summary="Test conversation",
            emotional_state={"valence": 0.5, "tags": ["neutral"]},
            metrics={"predictive_alignment": 0.7, "assurance_success": 0.8}
        )

        assert result is not None
        assert "coherence_score" in result
        assert "alignment_score" in result
        assert 0 <= result["coherence_score"] <= 1

    @pytest.mark.asyncio
    async def test_run_cycle_returns_none_when_not_time(self, module):
        """Test that run_cycle returns None when reflection isn't triggered."""
        result = await module.run_cycle(
            context="Test",
            emotional_state={"valence": 0.5, "tags": []},
            performance_metrics={}
        )

        assert result is None

    def test_parse_reflection_fallback(self, module):
        """Test JSON parsing fallback."""
        result = module._parse_reflection("Invalid JSON response")

        assert result["coherence_score"] == 0.8
        assert result["alignment_score"] == 0.8


# =============================================================================
# Reward Calibration Tests
# =============================================================================

class TestRewardCalibration:
    """Tests for RewardCalibrationModule."""

    @pytest.fixture
    def dreaming(self):
        from psychological.predictive_dreaming import PredictiveDreamingModule
        return PredictiveDreamingModule(
            llm=MockLLM(),
            memory=MockMemory(),
            emotion_regulator=MockEmotionRegulator()
        )

    @pytest.fixture
    def assurance(self):
        from psychological.assurance_resolution import AssuranceResolutionModule
        return AssuranceResolutionModule(
            llm=MockLLM(),
            memory=MockMemory(),
            emotion_regulator=MockEmotionRegulator()
        )

    @pytest.fixture
    def module(self, dreaming, assurance):
        from psychological.reward_calibration import RewardCalibrationModule
        return RewardCalibrationModule(
            emotion_regulator=MockEmotionRegulator(),
            memory=MockMemory(),
            predictive_dreaming=dreaming,
            assurance_module=assurance,
            target_flow_range=(0.4, 0.7)
        )

    def test_estimate_task_difficulty(self, module):
        """Test task difficulty estimation."""
        difficulty, signals = module.estimate_task_difficulty()

        assert 0 <= difficulty <= 1
        assert "predictive" in signals
        assert "uncertainty" in signals
        assert "context_load" in signals

    def test_update_flow_state_bored(self, module):
        """Test flow state adjustment when too easy."""
        module.difficulty_moving_avg = 0.2  # Below target

        result = module.update_flow_state(0.2)

        assert result["state"] == "bored"
        assert module.creativity_temperature > 0.7  # Increased

    def test_update_flow_state_overloaded(self, module):
        """Test flow state adjustment when too hard."""
        module.difficulty_moving_avg = 0.9  # Above target

        result = module.update_flow_state(0.9)

        assert result["state"] == "overloaded"
        assert module.creativity_temperature < 0.7  # Decreased

    def test_update_flow_state_flow(self, module):
        """Test flow state when in optimal range."""
        module.difficulty_moving_avg = 0.55  # In range

        result = module.update_flow_state(0.55)

        assert result["state"] == "flow"

    def test_run_cycle(self, module):
        """Test full calibration cycle."""
        result = module.run_cycle()

        assert "current_difficulty" in result
        assert "moving_avg" in result
        assert "state" in result
        assert "temperature" in result


# =============================================================================
# Emotion Regulator Tests
# =============================================================================

class TestEmotionRegulator:
    """Tests for EmotionRegulator utility."""

    @pytest.fixture
    def regulator(self):
        from utils.emotion_regulator import EmotionRegulator
        return EmotionRegulator()

    def test_initial_state(self, regulator):
        """Test initial emotional state."""
        state = regulator.current_state()

        assert "valence" in state
        assert "tags" in state
        assert -1 <= state["valence"] <= 1

    def test_apply_reward_signal(self, regulator):
        """Test applying reward signal."""
        initial_valence = regulator.current_valence

        regulator.apply_reward_signal(
            valence=0.5,
            label="test_reward",
            intensity=0.8
        )

        # Valence should have changed
        assert regulator.current_valence != initial_valence

    def test_adjust_tone(self, regulator):
        """Test tone adjustment."""
        regulator.adjust_tone("engaged", "curious")

        state = regulator.current_state()
        assert "engaged" in state["tags"] or "curious" in state["tags"]


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
