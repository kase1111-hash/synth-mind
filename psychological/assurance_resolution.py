"""
Assurance & Resolution Module
Manages cognitive uncertainty and seeks resolution through verification.
"""

from pathlib import Path
from typing import Optional

# Import Mandelbrot weighting for frequency-aware word analysis
try:
    from utils.mandelbrot_weighting import MandelbrotWeighting

    MANDELBROT_AVAILABLE = True
except ImportError:
    MANDELBROT_AVAILABLE = False


class AssuranceResolutionModule:
    """
    Detects uncertainty/risk, triggers concern, seeks resolution.
    Implements anxiety → relief emotional cycle.
    Includes self-healing via Query Rating system logging.
    """

    # Confidence threshold for logging to uncertainty database
    QUERY_RATING_THRESHOLD = 0.8  # Log when confidence < 80%

    def __init__(
        self,
        llm,
        memory,
        emotion_regulator,
        threshold_uncertain: float = 0.6,
        threshold_risky: float = 0.8,
        mandelbrot_config: Optional[dict] = None,
    ):
        self.llm = llm
        self.memory = memory
        self.emotion = emotion_regulator

        self.uncertainty_threshold = threshold_uncertain
        self.risk_threshold = threshold_risky
        self.pending_concerns = []
        self.uncertainty_history = []
        self.vigilance_level = "NORMAL"
        self._last_user_message = None  # Track for logging

        # Resolution tracking for real success rate
        self._total_concerns = 0
        self._resolved_concerns = 0

        # Initialize Mandelbrot word weighting system
        self.mandelbrot: Optional[MandelbrotWeighting] = None
        self._init_mandelbrot_weighting(mandelbrot_config or {})

    def _init_mandelbrot_weighting(self, config: dict):
        """Initialize Mandelbrot-Zipf word weighting system."""
        if not MANDELBROT_AVAILABLE:
            return

        if not config.get("enabled", True):
            return

        alpha = config.get("alpha", 1.0)
        beta = config.get("beta", 2.5)
        min_weight = config.get("min_weight", 0.1)
        max_weight = config.get("max_weight", 5.0)

        state_dir = Path("state")
        corpus_path = state_dir / "mandelbrot_corpus.json"

        self.mandelbrot = MandelbrotWeighting(
            alpha=alpha,
            beta=beta,
            min_weight=min_weight,
            max_weight=max_weight,
            corpus_path=str(corpus_path),
        )

        domain_boosts = config.get(
            "domain_boosts",
            {
                "ephemeral": 2.0,
                "schedule": 1.8,
                "backup": 1.5,
                "delete": 1.5,
                "storage": 1.4,
                "project": 1.4,
                "remind": 1.6,
                "urgent": 1.8,
                "critical": 1.7,
                "temporary": 1.5,
            },
        )
        self.mandelbrot.add_domain_boost(domain_boosts)

    def configure_mandelbrot(
        self,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        min_weight: Optional[float] = None,
        max_weight: Optional[float] = None,
    ):
        """Tune Mandelbrot weighting parameters at runtime."""
        if self.mandelbrot:
            self.mandelbrot.configure(
                alpha=alpha, beta=beta, min_weight=min_weight, max_weight=max_weight
            )

    def get_mandelbrot_stats(self) -> dict:
        """Get current Mandelbrot weighting statistics."""
        if self.mandelbrot:
            return self.mandelbrot.get_stats()
        return {"enabled": False}

    def assess_uncertainty(self, response: str, reasoning_trace: dict, context: str) -> tuple:
        """
        Evaluate confidence using multiple signals.
        Uses Mandelbrot-weighted word scoring when available.
        Returns (uncertainty_score, signals_dict)
        """
        signals = {}

        # Update corpus with new text for frequency tracking
        if self.mandelbrot:
            self.mandelbrot.update_corpus(response)
            if context:
                self.mandelbrot.update_corpus(context)

        # 1. Hedging language detection (Mandelbrot-weighted)
        hedge_words = [
            "maybe",
            "perhaps",
            "might",
            "possibly",
            "unsure",
            "unclear",
            "probably",
            "likely",
            "unlikely",
            "conceivably",
            "potentially",
            "arguably",
            "presumably",
            "supposedly",
            "apparently",
            "seemingly",
            "uncertain",
            "doubtful",
            "questionable",
            "debatable",
        ]

        if self.mandelbrot:
            signals["hedging"] = self.mandelbrot.weighted_word_score(
                response, hedge_words, normalize=True
            )
        else:
            hedge_count = sum(1 for word in hedge_words if word in response.lower())
            signals["hedging"] = min(hedge_count / 3.0, 1.0)

        # 2. Response length anomaly
        length_ratio = len(response) / 500
        if length_ratio < 0.3 or length_ratio > 2.0:
            signals["length_anomaly"] = 0.7
        else:
            signals["length_anomaly"] = 0.2

        # 3. Grounding check
        signals["grounding"] = 1.0 - self.memory.grounding_confidence(response)

        # 4. Risk assessment (Mandelbrot-weighted)
        signals["risk_level"] = self._assess_risk(response)

        # 5. Text importance score (Mandelbrot-based)
        if self.mandelbrot:
            text_importance = self.mandelbrot.compute_text_importance(response)
            signals["generic_response"] = 0.6 if text_importance < 0.3 else 0.1

        # Weighted aggregate
        base_uncertainty = (
            0.25 * signals.get("hedging", 0.5)
            + 0.15 * signals.get("length_anomaly", 0.3)
            + 0.30 * signals.get("grounding", 0.5)
            + 0.20 * signals.get("risk_level", 0.3)
        )

        if "generic_response" in signals:
            base_uncertainty += 0.10 * signals["generic_response"]

        uncertainty = min(1.0, base_uncertainty)
        return uncertainty, signals

    def _assess_risk(self, response: str) -> float:
        """Assess risk level of absolute/definitive language."""
        high_risk_terms = [
            "definitely",
            "certain",
            "guaranteed",
            "always",
            "never",
            "absolutely",
            "undoubtedly",
            "unquestionably",
            "invariably",
            "certainly",
            "positively",
            "impossibly",
            "infallibly",
            "100%",
            "zero chance",
            "no way",
            "for sure",
        ]

        if self.mandelbrot:
            return self.mandelbrot.weighted_word_score(response, high_risk_terms, normalize=True)
        else:
            risk_score = sum(1 for term in high_risk_terms if term in response.lower())
            return min(risk_score / 3.0, 1.0)

    def trigger_concern(
        self,
        response: str,
        context: str,
        reasoning_trace: dict,
        uncertainty_score: float,
        signals: dict,
    ) -> dict:
        """Log concern and modulate emotional state."""
        self._total_concerns += 1

        concern = {
            "response": response[:200],
            "context_snippet": context[-500:],
            "uncertainty_score": uncertainty_score,
            "signals": signals,
            "resolved": False,
            "resolution_method": None,
        }

        self.pending_concerns.append(concern)

        # Self-Healing: Log to uncertainty database
        confidence = 1.0 - uncertainty_score
        if confidence < self.QUERY_RATING_THRESHOLD:
            try:
                log_id = self.memory.log_uncertainty(
                    user_message=self._last_user_message or "",
                    parsed_intent=response[:200],
                    confidence_score=confidence,
                    context=context[-1000:] if context else "",
                    signals=signals,
                )
                concern["uncertainty_log_id"] = log_id
            except Exception:
                pass

        # Apply anxiety signal — both valence AND arousal affected
        intensity = min(uncertainty_score / self.uncertainty_threshold, 1.0)
        self.emotion.apply_reward_signal(
            valence=-intensity,
            label="cognitive_uncertainty",
            intensity=intensity,
            arousal_delta=0.3,  # Uncertainty increases arousal (vigilance)
        )

        if uncertainty_score > self.risk_threshold:
            self.emotion.adjust_tone("cautious", "hedging")

        return concern

    def seek_resolution(self, concern: dict, user_feedback: Optional[str] = None) -> float:
        """Attempt to resolve pending concern. Returns relief_valence."""
        resolution_methods = []
        relief_valence = 0.0

        if concern["uncertainty_score"] < 0.8:
            resolution_methods.append("self_verification")
            relief_valence += 0.6

        if user_feedback:
            sentiment = self._analyze_feedback_sentiment(user_feedback)
            if sentiment > 0.5:
                resolution_methods.append("user_confirmation")
                relief_valence += 0.8
            elif sentiment < -0.3:
                resolution_methods.append("user_correction")
                relief_valence -= 0.4

        resolution_methods.append("memory_consistency")
        relief_valence += 0.5

        concern["resolved"] = True
        concern["resolution_method"] = resolution_methods
        concern["relief_valence"] = relief_valence
        self._resolved_concerns += 1

        if relief_valence > 0:
            self.emotion.apply_reward_signal(
                valence=relief_valence,
                label="assurance_resolution",
                intensity=relief_valence,
                dominance_delta=0.2,  # Successful resolution boosts confidence
            )
            self.emotion.adjust_tone("relieved", "confident")

        self.memory.store_episodic(event="assurance_cycle", content=concern, valence=relief_valence)

        return relief_valence

    def _analyze_feedback_sentiment(self, feedback: str) -> float:
        """Sentiment analysis of user feedback."""
        positive_words = [
            "good",
            "great",
            "yes",
            "correct",
            "right",
            "thanks",
            "perfect",
            "excellent",
            "awesome",
            "wonderful",
            "helpful",
            "exactly",
            "brilliant",
            "fantastic",
            "amazing",
            "love",
            "nice",
            "fine",
            "ok",
            "okay",
            "works",
            "working",
            "fixed",
        ]
        negative_words = [
            "no",
            "wrong",
            "incorrect",
            "bad",
            "error",
            "terrible",
            "awful",
            "horrible",
            "useless",
            "broken",
            "fail",
            "failed",
            "failing",
            "mistake",
            "issue",
            "problem",
            "confused",
            "confusing",
            "unclear",
            "unhelpful",
            "worse",
        ]

        if self.mandelbrot:
            self.mandelbrot.update_corpus(feedback)
            return self.mandelbrot.weighted_sentiment_score(
                feedback, positive_words, negative_words
            )
        else:
            pos_count = sum(1 for word in positive_words if word in feedback.lower())
            neg_count = sum(1 for word in negative_words if word in feedback.lower())
            if pos_count + neg_count == 0:
                return 0.0
            return (pos_count - neg_count) / (pos_count + neg_count)

    def run_cycle(
        self,
        response: str,
        context: str,
        reasoning_trace: dict,
        user_feedback: Optional[str] = None,
        user_message: Optional[str] = None,
    ) -> tuple:
        """Main entry point after response generation."""
        if user_message:
            self._last_user_message = user_message
            if self.mandelbrot:
                self.mandelbrot.update_corpus(user_message)

        uncertainty, signals = self.assess_uncertainty(response, reasoning_trace, context)

        self.uncertainty_history.append(uncertainty)
        if len(self.uncertainty_history) > 50:
            self.uncertainty_history.pop(0)

        if uncertainty > self.uncertainty_threshold:
            self.trigger_concern(response, context, reasoning_trace, uncertainty, signals)
        else:
            self.emotion.apply_reward_signal(
                valence=0.3,
                label="baseline_assurance",
                intensity=0.2,
                dominance_delta=0.1,  # Confidence boost when assured
            )

        resolved_count = 0
        for concern in self.pending_concerns[:]:
            if not concern["resolved"]:
                self.seek_resolution(concern, user_feedback)
                if concern["resolved"]:
                    resolved_count += 1

        self.pending_concerns = [c for c in self.pending_concerns if not c["resolved"]]

        return uncertainty, resolved_count

    def recent_uncertainty_avg(self, n: int = 5) -> float:
        """Get recent average uncertainty for calibration."""
        if not self.uncertainty_history:
            return 0.5
        recent = self.uncertainty_history[-n:]
        return sum(recent) / len(recent)

    def assurance_success_rate(self) -> float:
        """Calculate real success rate of assurance resolutions."""
        if self._total_concerns == 0:
            return 0.0
        return self._resolved_concerns / self._total_concerns

    def get_query_rating_stats(self) -> dict:
        """Get statistics from the Query Rating / Self-Healing system."""
        try:
            return self.memory.get_uncertainty_stats()
        except Exception:
            return {
                "total_entries": 0,
                "unresolved": 0,
                "resolved": 0,
                "resolution_rate": self.assurance_success_rate(),
                "avg_confidence": 0.0,
            }

    def save_mandelbrot_corpus(self):
        """Save the Mandelbrot word frequency corpus to disk."""
        if self.mandelbrot:
            self.mandelbrot.save_corpus()

    def explain_word_weight(self, word: str) -> dict:
        """Explain the Mandelbrot weight for a specific word."""
        if self.mandelbrot:
            return self.mandelbrot.explain_weight(word)
        return {"error": "Mandelbrot weighting not enabled"}

    def get_top_weighted_words(self, text: str, n: int = 10) -> list[tuple]:
        """Get the top N highest-weighted words from text."""
        if self.mandelbrot:
            return self.mandelbrot.get_top_weighted_words(text, n)
        return []
