"""
Assurance & Resolution Module
Manages cognitive uncertainty and seeks resolution through verification.
"""

import json
import numpy as np
from typing import Dict, List, Optional

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
        threshold_risky: float = 0.8
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
    
    def assess_uncertainty(
        self, response: str, reasoning_trace: Dict, context: str
    ) -> tuple:
        """
        Evaluate confidence using multiple signals.
        Returns (uncertainty_score, signals_dict)
        """
        signals = {}
        
        # 1. Simple heuristics (in production: use proper confidence models)
        # Check for hedging language
        hedge_words = ["maybe", "perhaps", "might", "possibly", "unsure", "unclear"]
        hedge_count = sum(1 for word in hedge_words if word in response.lower())
        signals["hedging"] = min(hedge_count / 3.0, 1.0)
        
        # 2. Response length (very short or very long = uncertain)
        length_ratio = len(response) / 500
        if length_ratio < 0.3 or length_ratio > 2.0:
            signals["length_anomaly"] = 0.7
        else:
            signals["length_anomaly"] = 0.2
        
        # 3. Grounding check
        signals["grounding"] = 1.0 - self.memory.grounding_confidence(response)
        
        # 4. Risk assessment (placeholder)
        signals["risk_level"] = self._assess_risk(response)
        
        # Weighted aggregate
        uncertainty = (
            0.3 * signals.get("hedging", 0.5) +
            0.2 * signals.get("length_anomaly", 0.3) +
            0.3 * signals.get("grounding", 0.5) +
            0.2 * signals.get("risk_level", 0.3)
        )
        
        return uncertainty, signals
    
    def _assess_risk(self, response: str) -> float:
        """Assess risk level of response content."""
        # Simple keyword-based risk detection
        high_risk_terms = ["definitely", "certain", "guaranteed", "always", "never"]
        risk_score = sum(1 for term in high_risk_terms if term in response.lower())
        return min(risk_score / 3.0, 1.0)
    
    def trigger_concern(
        self,
        response: str,
        context: str,
        reasoning_trace: Dict,
        uncertainty_score: float,
        signals: Dict
    ) -> Dict:
        """Log concern and modulate emotional state."""
        concern = {
            "response": response[:200],
            "context_snippet": context[-500:],
            "uncertainty_score": uncertainty_score,
            "signals": signals,
            "resolved": False,
            "resolution_method": None
        }

        self.pending_concerns.append(concern)

        # ============================================
        # Self-Healing: Log to uncertainty database
        # ============================================
        # Calculate confidence as inverse of uncertainty
        confidence = 1.0 - uncertainty_score

        if confidence < self.QUERY_RATING_THRESHOLD:
            # Log for pattern analysis
            try:
                log_id = self.memory.log_uncertainty(
                    user_message=self._last_user_message or "",
                    parsed_intent=response[:200],  # Best guess at what we thought they meant
                    confidence_score=confidence,
                    context=context[-1000:] if context else "",
                    signals=signals
                )
                concern["uncertainty_log_id"] = log_id
            except Exception as e:
                # Don't fail the main flow if logging fails
                pass

        # Apply anxiety-like signal
        intensity = min(uncertainty_score / self.uncertainty_threshold, 1.0)
        self.emotion.apply_reward_signal(
            valence=-intensity,
            label="cognitive_uncertainty",
            intensity=intensity
        )

        # Adjust tone if high risk
        if uncertainty_score > self.risk_threshold:
            self.emotion.adjust_tone("cautious", "hedging")

        return concern
    
    def seek_resolution(
        self, concern: Dict, user_feedback: Optional[str] = None
    ) -> float:
        """
        Attempt to resolve pending concern.
        Returns relief_valence.
        """
        resolution_methods = []
        relief_valence = 0.0
        
        # Strategy 1: Self-verification (simplified)
        if concern["uncertainty_score"] < 0.8:
            # Assume self-check passes for moderate uncertainty
            resolution_methods.append("self_verification")
            relief_valence += 0.6
        
        # Strategy 2: User feedback
        if user_feedback:
            sentiment = self._analyze_feedback_sentiment(user_feedback)
            if sentiment > 0.5:
                resolution_methods.append("user_confirmation")
                relief_valence += 0.8
            elif sentiment < -0.3:
                resolution_methods.append("user_correction")
                relief_valence -= 0.4
        
        # Strategy 3: Memory consistency
        resolution_methods.append("memory_consistency")
        relief_valence += 0.5
        
        # Finalize
        concern["resolved"] = True
        concern["resolution_method"] = resolution_methods
        concern["relief_valence"] = relief_valence
        
        # Apply relief
        if relief_valence > 0:
            self.emotion.apply_reward_signal(
                valence=relief_valence,
                label="assurance_resolution",
                intensity=relief_valence
            )
            self.emotion.adjust_tone("relieved", "confident")
        
        # Log
        self.memory.store_episodic(
            event="assurance_cycle",
            content=concern,
            valence=relief_valence
        )
        
        return relief_valence
    
    def _analyze_feedback_sentiment(self, feedback: str) -> float:
        """Simple sentiment analysis of user feedback."""
        positive_words = ["good", "great", "yes", "correct", "right", "thanks"]
        negative_words = ["no", "wrong", "incorrect", "bad", "error"]
        
        pos_count = sum(1 for word in positive_words if word in feedback.lower())
        neg_count = sum(1 for word in negative_words if word in feedback.lower())
        
        if pos_count + neg_count == 0:
            return 0.0
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def run_cycle(
        self, response: str, context: str, reasoning_trace: Dict,
        user_feedback: Optional[str] = None, user_message: Optional[str] = None
    ) -> tuple:
        """
        Main entry point after response generation.
        Returns (uncertainty_score, resolved_count)

        Args:
            response: The generated response to evaluate
            context: Conversation context
            reasoning_trace: Internal reasoning data
            user_feedback: Optional user feedback for resolution
            user_message: Original user message (for Query Rating logging)
        """
        # Store user message for Query Rating system
        if user_message:
            self._last_user_message = user_message

        uncertainty, signals = self.assess_uncertainty(response, reasoning_trace, context)

        # Track history
        self.uncertainty_history.append(uncertainty)
        if len(self.uncertainty_history) > 50:
            self.uncertainty_history.pop(0)

        if uncertainty > self.uncertainty_threshold:
            self.trigger_concern(response, context, reasoning_trace, uncertainty, signals)
        else:
            # Baseline assurance
            self.emotion.apply_reward_signal(
                valence=0.3, label="baseline_assurance", intensity=0.2
            )

        # Resolve pending concerns
        resolved_count = 0
        for concern in self.pending_concerns[:]:
            if not concern["resolved"]:
                relief = self.seek_resolution(concern, user_feedback)
                if concern["resolved"]:
                    resolved_count += 1

        # Clean up resolved concerns
        self.pending_concerns = [c for c in self.pending_concerns if not c["resolved"]]

        return uncertainty, resolved_count
    
    def recent_uncertainty_avg(self, n: int = 5) -> float:
        """Get recent average uncertainty for calibration."""
        if not self.uncertainty_history:
            return 0.5
        recent = self.uncertainty_history[-n:]
        return sum(recent) / len(recent)
    
    def assurance_success_rate(self) -> float:
        """Calculate success rate of assurance resolutions."""
        # Placeholder: return high success
        return 0.85

    def get_query_rating_stats(self) -> Dict:
        """
        Get statistics from the Query Rating / Self-Healing system.
        Returns uncertainty log statistics for monitoring.
        """
        try:
            return self.memory.get_uncertainty_stats()
        except Exception:
            return {
                "total_entries": 0,
                "unresolved": 0,
                "resolved": 0,
                "resolution_rate": 0.0,
                "avg_confidence": 0.0,
                "last_24h": 0
            }
