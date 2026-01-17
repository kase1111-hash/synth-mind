"""
Unit tests for core modules.
Tests LLM wrapper, memory system, and tool manager.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# LLM Wrapper Tests
# =============================================================================

class TestLLMWrapper:
    """Tests for LLMWrapper."""

    def test_detect_provider_anthropic(self):
        """Test provider detection for Anthropic."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
            from core.llm_wrapper import LLMProvider, LLMWrapper

            # Need to reimport to pick up new env
            wrapper = LLMWrapper.__new__(LLMWrapper)
            provider = wrapper._detect_provider()

            assert provider == LLMProvider.ANTHROPIC

    def test_detect_provider_openai(self):
        """Test provider detection for OpenAI."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            from core.llm_wrapper import LLMProvider, LLMWrapper

            wrapper = LLMWrapper.__new__(LLMWrapper)
            provider = wrapper._detect_provider()

            assert provider == LLMProvider.OPENAI

    def test_detect_provider_ollama(self):
        """Test provider detection for Ollama."""
        with patch.dict(os.environ, {"OLLAMA_MODEL": "llama3.2"}, clear=True):
            from core.llm_wrapper import LLMProvider, LLMWrapper

            wrapper = LLMWrapper.__new__(LLMWrapper)
            provider = wrapper._detect_provider()

            assert provider == LLMProvider.OLLAMA

    def test_detect_provider_no_config(self):
        """Test error when no provider configured."""
        with patch.dict(os.environ, {}, clear=True):
            from core.llm_wrapper import LLMWrapper

            wrapper = LLMWrapper.__new__(LLMWrapper)

            with pytest.raises(ValueError, match="No LLM provider configured"):
                wrapper._detect_provider()


# =============================================================================
# Tool Manager Tests
# =============================================================================

class TestToolManager:
    """Tests for ToolManager."""

    @pytest.fixture
    def manager(self):
        from core.tools import ToolManager
        return ToolManager()

    def test_get_all_tool_info(self, manager):
        """Test retrieving all tool information."""
        tools = manager.get_all_tool_info()

        assert isinstance(tools, dict)
        assert len(tools) > 0
        assert "calculator" in tools

    def test_get_tool_info(self, manager):
        """Test retrieving specific tool info."""
        info = manager.get_tool_info("calculator")

        assert info is not None
        assert "description" in info
        assert "params" in info

    def test_calculator_tool(self, manager):
        """Test calculator tool execution."""
        result = manager.execute("calculator", expression="2 + 2")

        assert result["success"] is True
        assert result["result"] == 4

    def test_calculator_safe_expressions(self, manager):
        """Test calculator blocks dangerous expressions."""
        result = manager.execute("calculator", expression="__import__('os').system('ls')")

        assert result["success"] is False
        assert "error" in result

    def test_unknown_tool(self, manager):
        """Test handling of unknown tools."""
        result = manager.execute("nonexistent_tool")

        assert result["success"] is False
        assert "Unknown tool" in result.get("error", "")

    def test_missing_required_params(self, manager):
        """Test handling of missing required parameters."""
        result = manager.execute("calculator")  # Missing expression

        assert result["success"] is False


# =============================================================================
# Memory System Tests
# =============================================================================

class TestMemorySystem:
    """Tests for MemorySystem."""

    @pytest.fixture
    def memory(self):
        from core.memory import MemorySystem

        # Create with temp directory
        memory = MemorySystem()
        memory.state_path = Path(tempfile.mkdtemp())
        return memory

    @pytest.mark.asyncio
    async def test_initialize(self, memory):
        """Test memory initialization."""
        await memory.initialize()

        assert memory.state_path.exists()

    def test_store_turn(self, memory):
        """Test storing conversation turns."""
        memory.store_turn("Hello", "Hi there!")
        memory.store_turn("How are you?", "I'm doing well.")

        assert len(memory.conversation_history) == 2

    def test_store_episodic(self, memory):
        """Test episodic memory storage."""
        memory.store_episodic(
            event="test_event",
            content={"data": "test"},
            valence=0.5
        )

        assert len(memory.episodic_buffer) == 1
        assert memory.episodic_buffer[0]["event"] == "test_event"

    def test_embed_text(self, memory):
        """Test text embedding."""
        embedding = memory.embed("Test text for embedding")

        assert embedding is not None
        assert len(embedding) > 0

    def test_store_persistent(self, memory):
        """Test persistent storage."""
        memory.store_persistent("test_key", {"value": 42})

        retrieved = memory.retrieve_persistent("test_key")

        assert retrieved is not None
        assert retrieved["value"] == 42

    def test_retrieve_persistent_missing(self, memory):
        """Test retrieving non-existent persistent data."""
        result = memory.retrieve_persistent("nonexistent_key")

        assert result is None

    def test_grounding_confidence(self, memory):
        """Test grounding confidence calculation."""
        # Add some context
        memory.store_turn("The sky is blue", "Yes, that's correct.")

        confidence = memory.grounding_confidence("The sky is blue and clear")

        assert 0 <= confidence <= 1

    def test_detect_coherence_drift(self, memory):
        """Test coherence drift detection."""
        drift = memory.detect_coherence_drift(threshold=0.7)

        assert isinstance(drift, bool)


# =============================================================================
# Integration Tests
# =============================================================================

class TestCoreIntegration:
    """Integration tests for core modules working together."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM that doesn't require API keys."""
        class MockLLM:
            async def generate(self, prompt, **kwargs):
                return "Mock response to: " + prompt[:50]

            def get_embedding(self, text):
                import hashlib

                import numpy as np
                hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
                np.random.seed(hash_val % (2**32))
                return np.random.randn(384).tolist()

        return MockLLM()

    def test_tool_manager_initialization(self):
        """Test that tool manager initializes correctly."""
        from core.tools import ToolManager

        manager = ToolManager()
        tools = manager.get_all_tool_info()

        # Should have multiple tools
        assert len(tools) >= 5

        # Each tool should have required fields
        for _name, info in tools.items():
            assert "description" in info
            assert "params" in info

    @pytest.mark.asyncio
    async def test_memory_full_cycle(self):
        """Test full memory cycle."""
        from core.memory import MemorySystem

        memory = MemorySystem()
        memory.state_path = Path(tempfile.mkdtemp())

        await memory.initialize()

        # Store some data
        memory.store_turn("Test input", "Test output")
        memory.store_episodic("test", {"data": 1}, 0.5)
        memory.store_persistent("key", {"value": "test"})

        # Verify retrieval
        assert memory.retrieve_persistent("key")["value"] == "test"
        assert len(memory.conversation_history) == 1


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
