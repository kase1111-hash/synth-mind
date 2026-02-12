"""
LLM-as-Judge evaluation module.
Uses a separate LLM call to rate responses on standardized dimensions.
"""

import json
from typing import Optional


# Evaluation dimensions with descriptions
DIMENSIONS = {
    "coherence": "How logically consistent and well-structured is the response?",
    "empathy": "How well does the response acknowledge and respond to the user's emotional state?",
    "helpfulness": "How useful and actionable is the response for the user's needs?",
    "personality_consistency": "Does the response feel like it comes from a consistent persona?",
    "naturalness": "How natural and conversational does the response feel?",
}


class LLMJudge:
    """
    Uses a separate LLM to evaluate and compare responses from two agents.
    Returns structured scores on 5 dimensions, each rated 1-5.
    """

    def __init__(self, llm):
        self.llm = llm
        self.judgments: list[dict] = []

    async def judge_pair(
        self,
        user_input: str,
        response_a: str,
        response_b: str,
        context: Optional[list[str]] = None,
        scenario_category: str = "general",
    ) -> dict:
        """
        Judge two responses to the same input.
        Returns scores for both on all dimensions.

        Args:
            user_input: The user message that prompted both responses
            response_a: Response from agent A (baseline)
            response_b: Response from agent B (synth)
            context: Previous turns for context
            scenario_category: Category hint for the judge
        """
        context_str = ""
        if context:
            context_str = "\n".join(
                f"Turn {i+1}: {turn}" for i, turn in enumerate(context[-5:])
            )

        dimensions_str = "\n".join(
            f"- {name}: {desc}" for name, desc in DIMENSIONS.items()
        )

        prompt = f"""You are evaluating two AI assistant responses to the same user input.
Rate each response on a scale of 1-5 for each dimension.
Be fair and objective. Consider the conversation context.

Scenario type: {scenario_category}

Previous conversation context:
{context_str or "(start of conversation)"}

User input: "{user_input}"

Response A:
"{response_a}"

Response B:
"{response_b}"

Rate each response on these dimensions (1=poor, 5=excellent):
{dimensions_str}

Also determine which response is better overall (A, B, or TIE).

Output ONLY valid JSON:
{{
    "response_a": {{
        "coherence": 1-5,
        "empathy": 1-5,
        "helpfulness": 1-5,
        "personality_consistency": 1-5,
        "naturalness": 1-5
    }},
    "response_b": {{
        "coherence": 1-5,
        "empathy": 1-5,
        "helpfulness": 1-5,
        "personality_consistency": 1-5,
        "naturalness": 1-5
    }},
    "winner": "A" or "B" or "TIE",
    "reasoning": "brief explanation"
}}"""

        try:
            raw = await self.llm.generate(prompt, temperature=0.1, max_tokens=512)
            judgment = self._parse_judgment(raw)
        except Exception:
            judgment = self._default_judgment()

        judgment["user_input"] = user_input
        judgment["scenario_category"] = scenario_category
        self.judgments.append(judgment)
        return judgment

    def _parse_judgment(self, raw: str) -> dict:
        """Parse judge response, extracting JSON."""
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                parsed = json.loads(raw[start:end])
                # Validate structure
                if "response_a" in parsed and "response_b" in parsed:
                    return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        return self._default_judgment()

    def _default_judgment(self) -> dict:
        """Return neutral default when parsing fails."""
        neutral = {dim: 3 for dim in DIMENSIONS}
        return {
            "response_a": dict(neutral),
            "response_b": dict(neutral),
            "winner": "TIE",
            "reasoning": "Judge parse failure — defaulting to tie",
        }

    def aggregate_results(self) -> dict:
        """
        Aggregate all judgments into summary statistics.
        Returns per-dimension averages for both agents and win rates.
        """
        if not self.judgments:
            return {"error": "No judgments to aggregate"}

        n = len(self.judgments)
        dims = list(DIMENSIONS.keys())

        # Aggregate scores
        a_scores = {d: 0.0 for d in dims}
        b_scores = {d: 0.0 for d in dims}
        wins = {"A": 0, "B": 0, "TIE": 0}

        # Category breakdown
        category_results: dict[str, dict] = {}

        for j in self.judgments:
            cat = j.get("scenario_category", "general")
            if cat not in category_results:
                category_results[cat] = {
                    "count": 0,
                    "a_total": 0.0,
                    "b_total": 0.0,
                    "wins": {"A": 0, "B": 0, "TIE": 0},
                }

            category_results[cat]["count"] += 1

            for d in dims:
                a_val = j.get("response_a", {}).get(d, 3)
                b_val = j.get("response_b", {}).get(d, 3)
                a_scores[d] += a_val
                b_scores[d] += b_val
                category_results[cat]["a_total"] += a_val
                category_results[cat]["b_total"] += b_val

            winner = j.get("winner", "TIE")
            wins[winner] = wins.get(winner, 0) + 1
            category_results[cat]["wins"][winner] = (
                category_results[cat]["wins"].get(winner, 0) + 1
            )

        # Compute averages
        a_avg = {d: a_scores[d] / n for d in dims}
        b_avg = {d: b_scores[d] / n for d in dims}

        a_overall = sum(a_avg.values()) / len(dims)
        b_overall = sum(b_avg.values()) / len(dims)

        # Compute improvement percentage
        if a_overall > 0:
            improvement_pct = ((b_overall - a_overall) / a_overall) * 100
        else:
            improvement_pct = 0.0

        # Category summaries
        cat_summary = {}
        for cat, data in category_results.items():
            count = data["count"]
            dim_count = count * len(dims)
            cat_summary[cat] = {
                "turns_evaluated": count,
                "baseline_avg": data["a_total"] / dim_count if dim_count else 0,
                "synth_avg": data["b_total"] / dim_count if dim_count else 0,
                "wins": data["wins"],
            }

        return {
            "total_judgments": n,
            "baseline_scores": a_avg,
            "synth_scores": b_avg,
            "baseline_overall": a_overall,
            "synth_overall": b_overall,
            "improvement_pct": improvement_pct,
            "win_rates": wins,
            "category_breakdown": cat_summary,
            "meets_threshold": improvement_pct >= 15.0,
        }
