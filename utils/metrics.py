"""
Metrics Tracker
Aggregates performance metrics across psychological modules.
"""

from typing import Dict, List
from collections import defaultdict

class MetricsTracker:
    """
    Centralized tracking of system performance metrics.
    """
    
    def __init__(self):
        self.dream_alignments = []
        self.uncertainty_scores = []
        self.flow_states = []
        self.user_sentiments = []
        
        self.last_dream_alignment = 0.5
        
        # Aggregated stats
        self.stats = defaultdict(list)
    
    def log_dream_alignment(self, alignment: float):
        """Log predictive dreaming alignment score."""
        self.dream_alignments.append(alignment)
        self.last_dream_alignment = alignment
        if len(self.dream_alignments) > 100:
            self.dream_alignments.pop(0)
    
    def log_uncertainty(self, uncertainty: float):
        """Log assurance uncertainty score."""
        self.uncertainty_scores.append(uncertainty)
        if len(self.uncertainty_scores) > 100:
            self.uncertainty_scores.pop(0)
    
    def log_flow_state(self, state: str):
        """Log flow calibration state."""
        self.flow_states.append(state)
        if len(self.flow_states) > 100:
            self.flow_states.pop(0)
    
    def log_user_sentiment(self, sentiment: float):
        """Log user sentiment estimate."""
        self.user_sentiments.append(sentiment)
        if len(self.user_sentiments) > 100:
            self.user_sentiments.pop(0)
    
    def update_turn_metrics(
        self,
        alignment: float = None,
        uncertainty: float = None,
        flow_state: str = None
    ):
        """Update all metrics for a turn."""
        if alignment is not None:
            self.log_dream_alignment(alignment)
        if uncertainty is not None:
            self.log_uncertainty(uncertainty)
        if flow_state is not None:
            self.log_flow_state(flow_state)
    
    def avg_dream_alignment(self, n: int = 10) -> float:
        """Get recent average dream alignment."""
        if not self.dream_alignments:
            return 0.5
        recent = self.dream_alignments[-n:]
        return sum(recent) / len(recent)
    
    def avg_uncertainty(self, n: int = 10) -> float:
        """Get recent average uncertainty."""
        if not self.uncertainty_scores:
            return 0.5
        recent = self.uncertainty_scores[-n:]
        return sum(recent) / len(recent)
    
    def avg_user_sentiment(self, n: int = 10) -> float:
        """Get recent average user sentiment."""
        if not self.user_sentiments:
            return 0.5
        recent = self.user_sentiments[-n:]
        return sum(recent) / len(recent)
    
    def assurance_success_rate(self) -> float:
        """Calculate assurance resolution success rate."""
        # Simplified: inverse of average uncertainty
        avg_unc = self.avg_uncertainty(n=20)
        return 1.0 - avg_unc
    
    def flow_state_distribution(self) -> Dict[str, float]:
        """Get distribution of flow states."""
        if not self.flow_states:
            return {"balanced": 1.0}
        
        from collections import Counter
        counts = Counter(self.flow_states[-20:])
        total = sum(counts.values())
        return {state: count / total for state, count in counts.items()}
    
    def summary(self) -> Dict:
        """Get comprehensive metrics summary."""
        return {
            "dream_alignment": {
                "current": self.last_dream_alignment,
                "average": self.avg_dream_alignment(),
                "trend": "positive" if len(self.dream_alignments) > 1 and 
                         self.dream_alignments[-1] > self.dream_alignments[-10] else "stable"
            },
            "uncertainty": {
                "average": self.avg_uncertainty(),
                "assurance_success": self.assurance_success_rate()
            },
            "flow": self.flow_state_distribution(),
            "user_sentiment": self.avg_user_sentiment()
        }
