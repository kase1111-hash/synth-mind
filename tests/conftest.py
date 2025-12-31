"""
Pytest configuration and shared fixtures for Synth Mind tests.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


# =============================================================================
# Shared Mock Classes
# =============================================================================

class MockLLM:
    """Mock LLM for testing without API calls."""

    async def generate(self, prompt, temperature=0.7, max_tokens=1000, system=None):
        """Return deterministic mock responses based on prompt content."""
        prompt_lower = prompt.lower()

        if "simulate" in prompt_lower and "user messages" in prompt_lower:
            return '''[
                {"text": "Thanks!", "probability": 0.5},
                {"text": "Can you explain?", "probability": 0.3},
                {"text": "What else?", "probability": 0.2}
            ]'''
        elif "reflection" in prompt_lower:
            return '''{
                "coherence_score": 0.85,
                "alignment_score": 0.9,
                "issues_detected": [],
                "recommended_adjustments": {},
                "self_statement": "Operating well",
                "overall_insight": "Good progress"
            }'''
        elif "project" in prompt_lower and "clarifying" in prompt_lower:
            return '''{
                "acknowledgment": "Sounds exciting!",
                "end_transformation_query": "What should the result look like?",
                "clarifying_questions": ["Question 1?", "Question 2?"],
                "identified_uncertainties": []
            }'''
        elif "roadmap" in prompt_lower:
            return '''{
                "brief": "Test project brief",
                "end_transformation": "From A to B",
                "roadmap": [
                    {"name": "Task 1", "description": "Do thing", "priority": 1, "depends_on": []}
                ],
                "confirmation_question": "Ready to start?"
            }'''
        elif "subtask" in prompt_lower:
            return '''{
                "output": "Task completed",
                "explanation": "Did the thing",
                "questions": [],
                "progress_estimate": 1.0,
                "blockers": []
            }'''

        return "Mock response"

    def get_embedding(self, text):
        """Return deterministic embedding based on text hash."""
        import hashlib
        import numpy as np

        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        return np.random.randn(384).tolist()


class MockMemory:
    """Mock memory system for testing."""

    def __init__(self):
        self.episodic_buffer = []
        self.persistent_store = {}
        self.conversation_history = []

    async def initialize(self):
        pass

    def embed(self, text):
        import numpy as np
        hash_val = hash(text) % 1000000
        np.random.seed(hash_val)
        return np.random.randn(384)

    def store_turn(self, user_input, response):
        self.conversation_history.append({
            "user": user_input,
            "assistant": response
        })

    def store_episodic(self, event, content, valence=0.0):
        self.episodic_buffer.append({
            "event": event,
            "content": content,
            "valence": valence
        })

    def store_persistent(self, key, value):
        self.persistent_store[key] = value

    def retrieve_persistent(self, key):
        return self.persistent_store.get(key)

    def detect_coherence_drift(self, threshold=0.7):
        return False

    def grounding_confidence(self, text):
        return 0.8

    def log_uncertainty(self, **kwargs):
        return 1

    def get_uncertainty_stats(self):
        return {"total_entries": 0}

    async def save_state(self):
        pass


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
        self.current_valence = max(-1, min(1, self.current_valence + valence * intensity * 0.1))

    def adjust_tone(self, *args):
        self.tone_adjustments.append(args)

    def current_state(self):
        return {"valence": self.current_valence, "tags": ["neutral"]}

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
# Fixtures
# =============================================================================

@pytest.fixture
def mock_llm():
    """Provide mock LLM instance."""
    return MockLLM()


@pytest.fixture
def mock_memory():
    """Provide mock memory instance."""
    return MockMemory()


@pytest.fixture
def mock_emotion():
    """Provide mock emotion regulator instance."""
    return MockEmotionRegulator()


@pytest.fixture
def mock_temporal():
    """Provide mock temporal purpose instance."""
    return MockTemporalPurpose()


@pytest.fixture
def temp_state_dir(tmp_path):
    """Provide temporary state directory."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir
