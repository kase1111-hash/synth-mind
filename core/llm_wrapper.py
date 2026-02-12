"""
LLM Wrapper - Unified interface for multiple LLM providers.
Supports OpenAI, Anthropic, and local models via Ollama.
"""

import asyncio
import os
from enum import Enum
from typing import Optional


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMWrapper:
    """Unified LLM interface supporting multiple providers."""

    def __init__(self):
        self.provider = self._detect_provider()
        self.client = None
        self._initialize_client()

    def _detect_provider(self) -> LLMProvider:
        """Auto-detect which provider to use based on environment."""
        if os.getenv("ANTHROPIC_API_KEY"):
            return LLMProvider.ANTHROPIC
        elif os.getenv("OPENAI_API_KEY"):
            return LLMProvider.OPENAI
        elif os.getenv("OLLAMA_MODEL"):
            return LLMProvider.OLLAMA
        else:
            raise ValueError(
                "No LLM provider configured. Set one of:\n"
                "  - ANTHROPIC_API_KEY\n"
                "  - OPENAI_API_KEY\n"
                "  - OLLAMA_MODEL (for local models)"
            )

    def _initialize_client(self):
        """Initialize the appropriate client."""
        if self.provider == LLMProvider.ANTHROPIC:
            import anthropic

            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

        elif self.provider == LLMProvider.OPENAI:
            import openai

            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("OPENAI_MODEL", "gpt-4")

        elif self.provider == LLMProvider.OLLAMA:
            import httpx

            self.client = httpx.AsyncClient()
            self.model = os.getenv("OLLAMA_MODEL", "llama3.2")
            self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system: Optional[str] = None,
    ) -> str:
        """Generate completion from prompt."""
        if self.provider == LLMProvider.ANTHROPIC:
            return await self._generate_anthropic(prompt, temperature, max_tokens, system)
        elif self.provider == LLMProvider.OPENAI:
            return await self._generate_openai(prompt, temperature, max_tokens, system)
        elif self.provider == LLMProvider.OLLAMA:
            return await self._generate_ollama(prompt, temperature, max_tokens, system)

    async def _generate_anthropic(
        self, prompt: str, temperature: float, max_tokens: int, system: Optional[str]
    ) -> str:
        """Generate using Anthropic API."""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system

        # Run blocking API call in thread pool to avoid blocking the event loop
        response = await asyncio.to_thread(self.client.messages.create, **kwargs)
        return response.content[0].text

    async def _generate_openai(
        self, prompt: str, temperature: float, max_tokens: int, system: Optional[str]
    ) -> str:
        """Generate using OpenAI API."""
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        # Run blocking API call in thread pool to avoid blocking the event loop
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    async def _generate_ollama(
        self, prompt: str, temperature: float, max_tokens: int, system: Optional[str]
    ) -> str:
        """Generate using local Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "options": {"num_predict": max_tokens},
        }

        if system:
            payload["system"] = system

        response = await self.client.post(f"{self.ollama_base_url}/api/generate", json=payload)

        data = response.json()
        return data.get("response", "")

    def get_embedding(self, text: str) -> list[float]:
        """Generate embedding for text (used by memory system)."""
        # Simple implementation - in production, use proper embedding model
        if self.provider == LLMProvider.OPENAI:
            response = self.client.embeddings.create(model="text-embedding-3-small", input=text)
            return response.data[0].embedding
        else:
            # Fallback: use sentence-transformers or similar
            # For now, return dummy embedding using local RNG to avoid global state mutation
            import hashlib

            import numpy as np

            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            rng = np.random.default_rng(hash_val % (2**32))
            return rng.standard_normal(384).tolist()
