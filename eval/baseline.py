"""
Baseline Agent — bare LLM wrapper with NO psychological modules.
Same model, same personality prompt, same context window.
Just llm.generate(context, system=personality).
"""


class BaselineAgent:
    """
    Control group for A/B evaluation.
    Maintains conversation context and personality but has zero
    emotional state, zero dreaming, zero reflection, zero calibration.
    """

    def __init__(self, llm, personality_prompt: str = None):
        self.llm = llm
        self.personality_prompt = personality_prompt or (
            "You are a helpful, thoughtful AI assistant."
        )
        self.context: list[dict] = []
        self.turn_count = 0

    async def respond(self, user_input: str) -> str:
        """Generate a response using only context + personality."""
        self.turn_count += 1
        self.context.append({"role": "user", "content": user_input})

        context_str = self._format_context()

        response = await self.llm.generate(
            context_str,
            temperature=0.7,
            system=self.personality_prompt,
        )

        self.context.append({"role": "assistant", "content": response})
        return response

    def reset(self):
        """Reset conversation state between scenarios."""
        self.context = []
        self.turn_count = 0

    def _format_context(self, window: int = 20) -> str:
        recent = self.context[-window:]
        return "\n".join(f"{msg['role'].title()}: {msg['content']}" for msg in recent)
