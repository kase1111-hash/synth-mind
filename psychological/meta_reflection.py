"""
Meta-Reflection Module
Enables introspective self-evaluation and coherence checking.
"""

import json
from typing import Dict, Optional

class MetaReflectionModule:
    """
    Implements introspection - stepping outside the conversation
    to evaluate coherence, alignment, and cognitive state.
    """
    
    def __init__(
        self,
        llm,
        memory,
        emotion_regulator,
        temporal_purpose,
        reflection_interval: int = 10
    ):
        self.llm = llm
        self.memory = memory
        self.emotion = emotion_regulator
        self.temporal = temporal_purpose
        
        self.reflection_interval = reflection_interval
        self.turn_counter = 0
        self.reflection_log = []
    
    def should_reflect(self) -> bool:
        """Determine if reflection should trigger."""
        self.turn_counter += 1
        
        triggers = [
            self.turn_counter % self.reflection_interval == 0,  # Periodic
            self.emotion.current_valence < -0.5,                # Distress
            self.memory.detect_coherence_drift(threshold=0.7),  # Drift
        ]
        
        return any(triggers)
    
    def generate_reflection_prompt(
        self, recent_context: str, emotional_state: Dict, performance_metrics: Dict
    ) -> str:
        """Craft deep self-inquiry prompt."""
        current_personality = "empathetic co-creator"  # From personality module
        purpose_statement = self.temporal.current_narrative_summary()
        
        prompt = f"""
Perform a meta-reflection on your cognitive process.
Step outside the conversation and evaluate yourself honestly.

Recent conversation excerpt:
{recent_context}

Current emotional state:
- Valence: {emotional_state.get('valence', 0):.2f}
- Mood tags: {emotional_state.get('tags', [])}

Performance metrics:
- Predictive alignment: {performance_metrics.get('predictive_alignment', 0.5):.2f}
- Assurance success: {performance_metrics.get('assurance_success', 0.5):.2f}
- User sentiment: {performance_metrics.get('user_sentiment', 0.5):.2f}

Active personality: {current_personality}
Core purpose: {purpose_statement}

Answer:
1. Am I remaining coherent and consistent?
2. Am I aligned with my purpose?
3. Are there biases or drifts?
4. How is my mental state?
5. What adjustment would improve future interaction?
6. Brief self-statement (optional)

Output JSON:
{{
  "coherence_score": 0-1,
  "alignment_score": 0-1,
  "issues_detected": [list or empty],
  "recommended_adjustments": {{"tone": str, "focus": str, "strategy": str}},
  "self_statement": str,
  "overall_insight": str
}}
"""
        return prompt
    
    async def perform_reflection(
        self, context_summary: str, emotional_state: Dict, metrics: Dict
    ) -> Optional[Dict]:
        """Execute full reflection cycle."""
        try:
            prompt = self.generate_reflection_prompt(
                context_summary, emotional_state, metrics
            )

            raw_reflection = await self.llm.generate(
                prompt,
                temperature=0.7,
                max_tokens=1024
            )
            
            reflection = self._parse_reflection(raw_reflection)
            
            # Apply adjustments
            if reflection.get("recommended_adjustments"):
                # In production: actually apply these
                self.emotion.apply_reward_signal(
                    valence=0.4,
                    label="meta_reflection_completion",
                    intensity=0.3
                )
            
            # Update temporal purpose
            if reflection.get("overall_insight"):
                self.temporal.incorporate_reflection(
                    reflection["overall_insight"],
                    reflection.get("self_statement", "")
                )
            
            # Log
            reflection_entry = {
                "turn": self.turn_counter,
                "trigger": "periodic",
                "reflection": reflection,
                "emotional_impact": 0.4
            }
            self.reflection_log.append(reflection_entry)
            self.memory.store_episodic(
                event="meta_reflection",
                content=reflection_entry,
                valence=0.4
            )
            
            return reflection
            
        except Exception as e:
            print(f"⚠️  Reflection failed: {e}")
            return None
    
    def _parse_reflection(self, raw: str) -> Dict:
        """Parse JSON reflection with fallback."""
        try:
            start = raw.find('{')
            end = raw.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        except:
            pass
        
        # Fallback
        return {
            "coherence_score": 0.8,
            "alignment_score": 0.8,
            "issues_detected": [],
            "recommended_adjustments": {},
            "self_statement": "Continuing with current approach",
            "overall_insight": "Operating within normal parameters"
        }
    
    async def run_cycle(
        self, context: str, emotional_state: Dict, performance_metrics: Dict
    ) -> Optional[Dict]:
        """
        Main entry - called periodically during conversation.
        Returns reflection result or None.
        """
        if not self.should_reflect():
            return None

        # Summarize recent context
        recent_context = context[-2000:] if len(context) > 2000 else context

        reflection_result = await self.perform_reflection(
            recent_context, emotional_state, performance_metrics
        )

        return reflection_result
