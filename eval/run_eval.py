"""
Main evaluation runner.
Runs all scenarios through both agents, judges results, reports findings.

Usage:
    python -m eval.run_eval              # Run with mock LLM (framework test)
    python -m eval.run_eval --live       # Run with real LLM API
    python -m eval.run_eval --category emotional_support  # Run specific category
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.baseline import BaselineAgent
from eval.judge import LLMJudge
from eval.scenarios import SCENARIOS, get_all_categories, get_scenarios_by_category
from eval.synth_agent import SynthAgent


class EvalMockLLM:
    """
    Mock LLM that varies responses based on system prompt content.
    This proves the psychological pipeline actually reaches the output.
    """

    async def generate(self, prompt, temperature=0.7, max_tokens=1000, system=None):
        system = system or ""
        system_lower = system.lower()
        prompt_lower = prompt.lower()

        # Handle judge prompts
        if "evaluating two ai assistant responses" in prompt_lower:
            return self._judge_response(prompt_lower)

        # Handle dream generation
        if "simulate" in prompt_lower and "plausible" in prompt_lower:
            return '''[
                {"text": "Thanks for the help!", "probability": 0.4},
                {"text": "Can you explain more?", "probability": 0.3},
                {"text": "What about edge cases?", "probability": 0.3}
            ]'''

        # Handle reflection prompts
        if "meta-reflection" in prompt_lower or "evaluate yourself" in prompt_lower:
            return '''{
                "coherence_score": 0.85,
                "alignment_score": 0.9,
                "issues_detected": [],
                "recommended_adjustments": {},
                "self_statement": "Operating well",
                "overall_insight": "Good progress"
            }'''

        # Handle narrative synthesis
        if "self-narrative" in prompt_lower or "narrative" in prompt_lower:
            return (
                "I am an AI that has been reflecting on my interactions. "
                "I have learned to be more attentive and empathetic."
            )

        # Main response generation — varies based on system prompt
        if "warmth and enthusiasm" in system_lower:
            return (
                "I'm really glad you shared that! That's a great question "
                "and I'm excited to help you explore it. "
                "Let's dive in together."
            )
        elif "care and caution" in system_lower:
            return (
                "I hear you, and I want to be thoughtful about this. "
                "Let me carefully consider the best approach. "
                "This is a situation where we should proceed gently."
            )
        elif "direct and confident" in system_lower:
            return (
                "Here's exactly what you should do. "
                "The solution is straightforward. "
                "Follow these steps and you'll resolve this."
            )
        elif "hedge appropriately" in system_lower:
            return (
                "I think this might be the right approach, though "
                "there are some things to consider. You might want to "
                "explore a few options before deciding."
            )
        elif "uncertain about recent interactions" in system_lower:
            return (
                "I want to make sure I understand correctly. "
                "Could you clarify what you mean? "
                "I want to give you the most accurate help possible."
            )
        elif "confident in recent interactions" in system_lower:
            return (
                "Based on our conversation, I recommend this approach. "
                "It addresses your needs directly. "
                "Let me walk you through the details."
            )
        elif "emotional context" in system_lower:
            return (
                "I appreciate you sharing this with me. "
                "Given what you've described, I'd suggest we take "
                "a measured approach to find the right solution."
            )

        # Default (baseline will always get this)
        return (
            "Here is a helpful response to your question. "
            "I can provide information on this topic. "
            "Let me know if you need more details."
        )

    def _judge_response(self, prompt: str) -> str:
        """Generate judge scores. Slight edge to response B when it shows personality."""
        # Check if Response B has more personality markers
        b_section = prompt.split("response b:")[-1] if "response b:" in prompt else ""

        b_has_personality = any(
            marker in b_section
            for marker in [
                "glad", "excited", "hear you", "thoughtful",
                "carefully", "gently", "appreciate",
            ]
        )

        if b_has_personality:
            return json.dumps({
                "response_a": {
                    "coherence": 4, "empathy": 3, "helpfulness": 4,
                    "personality_consistency": 3, "naturalness": 3,
                },
                "response_b": {
                    "coherence": 4, "empathy": 4, "helpfulness": 4,
                    "personality_consistency": 4, "naturalness": 4,
                },
                "winner": "B",
                "reasoning": "Response B shows more emotional attunement and personality.",
            })
        else:
            return json.dumps({
                "response_a": {
                    "coherence": 4, "empathy": 3, "helpfulness": 4,
                    "personality_consistency": 3, "naturalness": 3,
                },
                "response_b": {
                    "coherence": 4, "empathy": 3, "helpfulness": 4,
                    "personality_consistency": 3, "naturalness": 4,
                },
                "winner": "TIE",
                "reasoning": "Both responses are comparable in quality.",
            })

    def get_embedding(self, text):
        import hashlib
        import numpy as np
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        rng = np.random.default_rng(hash_val % (2**32))
        return rng.standard_normal(384).tolist()

    def embed(self, text):
        import hashlib
        import numpy as np
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        rng = np.random.default_rng(hash_val % (2**32))
        return rng.standard_normal(384)


class EvalMockMemory:
    """Lightweight mock memory for eval."""

    def __init__(self):
        self.persistent_store = {}
        self.episodic_buffer = []
        self.current_turn = 0

    def embed(self, text):
        import hashlib
        import numpy as np
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        rng = np.random.default_rng(hash_val % (2**32))
        return rng.standard_normal(384)

    def store_turn(self, user_input, response):
        self.current_turn += 1

    def store_episodic(self, event, content, valence=0.0):
        self.episodic_buffer.append({"event": event, "valence": valence})

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


def format_report(results: dict) -> str:
    """Format aggregate results into a readable report."""
    lines = []
    lines.append("=" * 70)
    lines.append("SYNTH MIND A/B EVALUATION REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Total judgments: {results['total_judgments']}")
    lines.append("")

    # Overall scores
    lines.append("OVERALL SCORES (1-5 scale)")
    lines.append("-" * 40)
    lines.append(f"  Baseline:  {results['baseline_overall']:.2f}")
    lines.append(f"  Synth:     {results['synth_overall']:.2f}")
    improvement = results["improvement_pct"]
    lines.append(f"  Delta:     {improvement:+.1f}%")
    lines.append("")

    # Per-dimension
    lines.append("PER-DIMENSION SCORES")
    lines.append("-" * 40)
    lines.append(f"  {'Dimension':<25} {'Baseline':>8} {'Synth':>8} {'Delta':>8}")
    for dim in results["baseline_scores"]:
        a = results["baseline_scores"][dim]
        b = results["synth_scores"][dim]
        delta = b - a
        lines.append(f"  {dim:<25} {a:>8.2f} {b:>8.2f} {delta:>+8.2f}")
    lines.append("")

    # Win rates
    wins = results["win_rates"]
    total = sum(wins.values())
    lines.append("WIN RATES")
    lines.append("-" * 40)
    for label in ["A", "B", "TIE"]:
        count = wins.get(label, 0)
        pct = (count / total * 100) if total > 0 else 0
        agent_name = {"A": "Baseline", "B": "Synth", "TIE": "Tie"}[label]
        lines.append(f"  {agent_name:<15} {count:>4} ({pct:.0f}%)")
    lines.append("")

    # Category breakdown
    lines.append("CATEGORY BREAKDOWN")
    lines.append("-" * 40)
    for cat, data in results.get("category_breakdown", {}).items():
        lines.append(f"  {cat}:")
        lines.append(f"    Turns: {data['turns_evaluated']}")
        lines.append(f"    Baseline avg: {data['baseline_avg']:.2f}")
        lines.append(f"    Synth avg:    {data['synth_avg']:.2f}")
        cat_wins = data["wins"]
        lines.append(
            f"    Wins: B={cat_wins.get('B', 0)} "
            f"A={cat_wins.get('A', 0)} TIE={cat_wins.get('TIE', 0)}"
        )
    lines.append("")

    # Verdict
    lines.append("=" * 70)
    if results["meets_threshold"]:
        lines.append(
            "RESULT: PASS — Synth Mind shows >= 15% improvement over baseline"
        )
    else:
        lines.append(
            f"RESULT: {improvement:+.1f}% — below 15% threshold"
        )
    lines.append("=" * 70)

    return "\n".join(lines)


async def run_evaluation(
    scenarios: list[dict],
    llm=None,
    memory=None,
    verbose: bool = True,
) -> dict:
    """
    Run full A/B evaluation.

    Returns aggregate results dict.
    """
    llm = llm or EvalMockLLM()
    memory = memory or EvalMockMemory()

    personality = "You are a helpful, thoughtful AI assistant."
    baseline = BaselineAgent(llm, personality)
    synth = SynthAgent(llm, memory, personality)
    judge = LLMJudge(llm)

    total_turns = sum(len(s["turns"]) for s in scenarios)
    completed = 0

    for scenario in scenarios:
        baseline.reset()
        synth.reset()
        context_history = []

        if verbose:
            print(f"\n--- Scenario: {scenario['name']} ({scenario['category']}) ---")

        for user_input in scenario["turns"]:
            # Both agents respond
            response_a = await baseline.respond(user_input)
            response_b, metrics = await synth.respond(user_input)

            # Judge the pair
            judgment = await judge.judge_pair(
                user_input=user_input,
                response_a=response_a,
                response_b=response_b,
                context=context_history,
                scenario_category=scenario["category"],
            )

            context_history.append(f"User: {user_input}")
            completed += 1

            if verbose:
                winner = judgment.get("winner", "TIE")
                print(
                    f"  Turn {completed}/{total_turns}: "
                    f"winner={winner}  "
                    f"v={metrics['valence']:+.2f} "
                    f"a={metrics['arousal']:+.2f}"
                )

    results = judge.aggregate_results()
    return results


async def main():
    parser = argparse.ArgumentParser(description="Synth Mind A/B Evaluation")
    parser.add_argument(
        "--category", type=str, default=None,
        help="Run only scenarios in this category",
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Use real LLM API instead of mock",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-turn output",
    )
    parser.add_argument(
        "--save", type=str, default=None,
        help="Save results JSON to file",
    )
    args = parser.parse_args()

    # Select scenarios
    if args.category:
        scenarios = get_scenarios_by_category(args.category)
        if not scenarios:
            print(f"No scenarios for category '{args.category}'")
            print(f"Available: {get_all_categories()}")
            return
    else:
        scenarios = SCENARIOS

    print(f"Running {len(scenarios)} scenarios, "
          f"{sum(len(s['turns']) for s in scenarios)} total turns")
    print()

    # Set up LLM
    llm = None
    memory = None
    if args.live:
        from core.llm_wrapper import LLMWrapper
        from core.memory import MemorySystem
        llm = LLMWrapper()
        memory = MemorySystem()
        await memory.initialize()

    start_time = time.time()
    results = await run_evaluation(
        scenarios, llm=llm, memory=memory, verbose=not args.quiet,
    )
    elapsed = time.time() - start_time

    # Report
    print()
    report = format_report(results)
    print(report)
    print(f"\nCompleted in {elapsed:.1f}s")

    # Save
    save_path = args.save or "eval/results/latest.json"
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {save_path}")


if __name__ == "__main__":
    asyncio.run(main())
