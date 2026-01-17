#!/usr/bin/env python3
"""
Simple Chat Example
Demonstrates basic usage of Synth Mind in a script.
"""

import asyncio
import sys

sys.path.insert(0, '..')

from core.orchestrator import SynthOrchestrator


async def main():
    """Simple conversation demo."""
    print("Initializing Synth Mind...")

    orchestrator = SynthOrchestrator()
    await orchestrator.initialize()

    print("Synth is ready!\n")

    # Example conversation
    test_inputs = [
        "Hello! What can you help me with?",
        "I'm interested in building AI agents with memory.",
        "How would you approach designing a memory system?",
        "What about emotional intelligence in AI?"
    ]

    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n{'='*60}")
        print(f"Turn {i}")
        print(f"{'='*60}")
        print(f"You: {user_input}\n")

        # Process turn
        await orchestrator._process_turn(user_input)

        # Show internal state
        print("\n--- Internal State ---")
        state = orchestrator.emotion.current_state()
        print(f"Valence: {state['valence']:+.2f}")
        print(f"Mood: {', '.join(state['tags'])}")

        if orchestrator.dreaming.dream_buffer:
            print(f"Dreams: {len(orchestrator.dreaming.dream_buffer)} scenarios predicted")

        await asyncio.sleep(1)

    print("\n\nDemo complete!")
    print("\nFinal Narrative:")
    print(orchestrator.temporal.current_narrative_summary())

    await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
