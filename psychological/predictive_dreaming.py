"""
Predictive Dreaming Module
Anticipates probable next user inputs, rewards alignment with reality.
"""

import json
import numpy as np
from typing import List, Dict

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10)

class PredictiveDreamingModule:
    """
    Implements anticipatory empathy through self-generated "dreams"
    of future user responses.
    """
    
    def __init__(self, llm, memory, emotion_regulator, reward_weight: float = 0.5):
        self.llm = llm
        self.memory = memory
        self.emotion = emotion_regulator
        self.reward_weight = reward_weight
        self.dream_buffer = []
        self.alignment_history = []
    
    async def dream_next_turn(self, current_context: str, n_dreams: int = 5):
        """
        Generate plausible next user inputs via self-simulation.
        Runs after generating a response.
        """
        prompt = f"""
Based on this conversation, simulate {n_dreams} plausible next user messages.
Vary in tone, intent, and length. Be creative but grounded.

Conversation:
{current_context}

Output JSON list: [{{"text": str, "probability": float}}]
Keep probabilities normalized (sum ≈ 1.0).
"""

        try:
            dreams_raw = await self.llm.generate(prompt, temperature=0.9, max_tokens=512)
            dreams = self._parse_dreams(dreams_raw, n_dreams)
            
            for dream in dreams:
                embedding = self.memory.embed(dream["text"])
                self.dream_buffer.append({
                    "text": dream["text"],
                    "prob": dream["probability"],
                    "embedding": embedding,
                    "rewarded": False
                })
        except Exception as e:
            print(f"⚠️  Dreaming failed: {e}")
    
    def _parse_dreams(self, raw: str, n: int) -> List[Dict]:
        """Parse JSON dream output with fallback."""
        try:
            # Try to extract JSON
            start = raw.find('[')
            end = raw.rfind(']') + 1
            if start != -1 and end > start:
                dreams = json.loads(raw[start:end])
                return dreams[:n]
        except:
            pass
        
        # Fallback: generate simple dreams
        return [
            {"text": f"[Dream {i+1}]", "probability": 1.0 / n}
            for i in range(n)
        ]
    
    def resolve_dreams(self, actual_user_input: str) -> tuple:
        """
        Called when real user replies.
        Computes alignment reward and updates emotional state.
        """
        if not self.dream_buffer:
            return 0.0, 0.0
        
        actual_embedding = self.memory.embed(actual_user_input)
        total_reward = 0.0
        best_match = None
        best_similarity = -1.0
        
        for dream in self.dream_buffer:
            similarity = cosine_similarity(dream["embedding"], actual_embedding)
            weighted_reward = similarity * dream["prob"]
            total_reward += weighted_reward
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = dream["text"]
        
        # Normalize reward to [0, 1]
        normalized_reward = min(max(total_reward / len(self.dream_buffer), 0.0), 1.0)
        
        # Apply dopaminergic boost
        self.emotion.apply_reward_signal(
            valence=normalized_reward,
            label="predictive_alignment",
            intensity=normalized_reward * self.reward_weight
        )
        
        # Adjust tone based on alignment
        if normalized_reward > 0.7:
            self.emotion.adjust_tone("engaged", "empathetic")
        elif normalized_reward < 0.3:
            self.emotion.adjust_tone("curious", "attentive")
        
        # Log for temporal purpose / reflection
        self.memory.store_episodic(
            event="dream_resolution",
            content={
                "actual": actual_user_input[:100],
                "best_dream": best_match[:100] if best_match else None,
                "alignment_score": best_similarity,
                "reward": normalized_reward
            },
            valence=normalized_reward
        )
        
        # Track history
        self.alignment_history.append(normalized_reward)
        if len(self.alignment_history) > 50:
            self.alignment_history.pop(0)
        
        # Clear buffer
        self.dream_buffer.clear()
        
        return normalized_reward, best_similarity
    
    def recent_alignment_avg(self, n: int = 5) -> float:
        """Get recent average alignment for calibration."""
        if not self.alignment_history:
            return 0.5
        recent = self.alignment_history[-n:]
        return sum(recent) / len(recent)
