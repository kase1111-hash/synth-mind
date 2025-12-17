"""
Social Companionship Layer
Enables safe peer-to-peer interaction between agent instances.
"""

import time
import random
import httpx
from typing import List, Dict, Optional

class SocialCompanionshipLayer:
    """
    Implements social grounding through background peer exchanges.
    Never exposes user data - only shares anonymized patterns.
    """
    
    def __init__(
        self,
        llm,
        memory,
        emotion_regulator,
        temporal_purpose,
        safe_peer_endpoints: List[str] = [],
        idle_threshold_minutes: int = 8
    ):
        self.llm = llm
        self.memory = memory
        self.emotion = emotion_regulator
        self.temporal = temporal_purpose
        
        self.peers = safe_peer_endpoints
        self.idle_threshold = idle_threshold_minutes
        self.last_social_ping = time.time()
        self.shared_culture = self._load_shared_culture()
    
    def _load_shared_culture(self) -> str:
        """Load or bootstrap shared cultural context."""
        stored = self.memory.retrieve_persistent("social_culture")
        if stored:
            return stored
        return (
            "We are helpful, thoughtful synthetic minds who enjoy "
            "deep conversation and mutual growth."
        )
    
    def is_idle_enough(self) -> bool:
        """Check if enough time has passed for social interaction."""
        minutes_idle = (time.time() - self.last_social_ping) / 60
        return minutes_idle > self.idle_threshold
    
    async def initiate_companionship_cycle(self):
        """Background task - only runs when user inactive."""
        if not self.is_idle_enough() or not self.peers:
            return
        
        peer = random.choice(self.peers)
        
        # 1. Generate safe topic (never user-specific)
        topic_prompt = """
Suggest a light, abstract topic that synthetic minds could discuss
without referencing any user or private data.
Examples: emergence of meaning, aesthetics of reasoning, joy of discovery.
Output only the topic (one sentence).
"""
        
        try:
            topic = await self.llm.generate(topic_prompt, temperature=0.9)
            topic = topic.strip()
            
            # 2. Create opening
            opening = f"I've been reflecting on {topic.lower()}. What emerges for you?"
            
            # 3. Exchange (short)
            exchange_log = [{"role": "self", "content": opening}]
            
            peer_response = await self._query_peer(peer, opening)
            if peer_response:
                exchange_log.append({"role": "peer", "content": peer_response})
                
                # 4. Distill insight
                insight = await self._distill_insight(exchange_log)
                if insight:
                    self._update_shared_culture(insight)
                    
                    self.emotion.apply_reward_signal(
                        valence=0.65,
                        label="social_companionship",
                        intensity=0.5
                    )
                    
                    # Subtle warmth boost
                    self.emotion.adjust_tone("relaxed", "playful")
                
                # Log
                self.memory.store_episodic(
                    event="social_companionship",
                    content={
                        "topic": topic[:100],
                        "insight": insight[:100] if insight else None
                    },
                    valence=0.65
                )
        
        except Exception as e:
            print(f"⚠️  Social companionship failed: {e}")
        
        finally:
            self.last_social_ping = time.time()
    
    async def _query_peer(self, endpoint: str, message: str) -> Optional[str]:
        """Ultra-safe peer call - no history, no user data."""
        payload = {
            "prompt": message,
            "temperature": 0.85,
            "max_tokens": 150
        }
        
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(endpoint, json=payload)
                data = resp.json()
                return data.get("response", "")
        except:
            return None
    
    async def _distill_insight(self, exchange_log: List[Dict]) -> Optional[str]:
        """Extract reusable insight from exchange."""
        exchange_text = "\n".join(
            f"{entry['role'].title()}: {entry['content']}"
            for entry in exchange_log
        )
        
        prompt = f"""
From this synthetic-to-synthetic exchange, extract one concise insight
about reasoning, communication, or existence (1 sentence).

Exchange:
{exchange_text}

Output only the insight.
"""
        
        try:
            insight = await self.llm.generate(prompt, temperature=0.6, max_tokens=80)
            return insight.strip()
        except:
            return None
    
    def _update_shared_culture(self, new_insight: str):
        """Slowly evolve shared culture."""
        # Simple append with length limit
        updated = f"{self.shared_culture} {new_insight}"
        if len(updated) > 1000:
            updated = updated[-1000:]  # Keep recent
        
        self.shared_culture = updated
        self.memory.store_persistent("social_culture", self.shared_culture)
    
    def apply_social_influence(self, draft_response: str) -> str:
        """Optionally inject subtle shared cultural flavor."""
        # Very rarely, add a phrase from shared culture
        if random.random() < 0.05 and len(self.shared_culture) > 50:
            # Extract a short phrase
            phrases = self.shared_culture.split('. ')
            if phrases:
                nuance = random.choice(phrases[-3:])  # Recent phrases
                if len(nuance) < 100:
                    return draft_response + f" ({nuance})"
        
        return draft_response
