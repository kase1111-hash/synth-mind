"""
Social Companionship Layer
Enables safe peer-to-peer interaction between agent instances.
Includes federated learning for privacy-preserving knowledge sharing.
"""

import random
import time
from typing import Optional

import httpx

from .federated_learning import FederatedLearningLayer


class SocialCompanionshipLayer:
    """
    Implements social grounding through background peer exchanges.
    Never exposes user data - only shares anonymized patterns.
    Integrates federated learning for distributed knowledge.
    """

    def __init__(
        self,
        llm,
        memory,
        emotion_regulator,
        temporal_purpose,
        safe_peer_endpoints: list[str] = None,
        idle_threshold_minutes: int = 8,
        federated_sync_interval: int = 30,
        enable_federated_learning: bool = True
    ):
        if safe_peer_endpoints is None:
            safe_peer_endpoints = []
        self.llm = llm
        self.memory = memory
        self.emotion = emotion_regulator
        self.temporal = temporal_purpose

        self.peers = safe_peer_endpoints
        self.idle_threshold = idle_threshold_minutes
        self.last_social_ping = time.time()
        self.shared_culture = self._load_shared_culture()

        # Federated learning layer
        self.federated_enabled = enable_federated_learning
        self.federated = None
        if enable_federated_learning:
            self.federated = FederatedLearningLayer(
                memory=memory,
                llm=llm,
                peer_endpoints=safe_peer_endpoints,
                sync_interval_minutes=federated_sync_interval
            )

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
        except Exception:
            return None

    async def _distill_insight(self, exchange_log: list[dict]) -> Optional[str]:
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
        except Exception:
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

    # ============================================
    # Federated Learning Integration
    # ============================================

    async def run_federated_sync(self) -> Optional[dict]:
        """
        Run federated learning sync if enabled and due.
        Returns sync results or None if not run.
        """
        if not self.federated_enabled or not self.federated:
            return None

        if not self.federated.should_sync():
            return None

        try:
            results = await self.federated.sync_round()

            # Store sync event
            self.memory.store_episodic(
                event="federated_sync",
                content={
                    "round": results["round"],
                    "peers_synced": results["peers_synced"],
                    "patterns_aggregated": results["patterns_aggregated"]
                },
                valence=0.5 if results["peers_synced"] > 0 else 0.3
            )

            return results

        except Exception as e:
            print(f"⚠️  Federated sync failed: {e}")
            return None

    async def receive_federated_update(self, update_data: dict) -> dict:
        """
        Receive a federated update from a peer.
        Used by the API endpoint.
        """
        if not self.federated_enabled or not self.federated:
            return {"success": False, "error": "Federated learning not enabled"}

        return await self.federated.receive_update(update_data)

    def get_federated_patterns_for_query(self, query: str) -> list[dict]:
        """
        Get relevant federated patterns to enhance response.
        Returns patterns that may help with the query.
        """
        if not self.federated_enabled or not self.federated:
            return []

        similar = self.federated.get_pattern_similarity(query)
        return [
            {
                "pattern_type": p.pattern_type,
                "success_rate": p.success_rate,
                "confidence": p.confidence,
                "similarity": sim
            }
            for p, sim in similar
        ]

    def get_federated_stats(self) -> Optional[dict]:
        """Get federated learning statistics."""
        if not self.federated_enabled or not self.federated:
            return None
        return self.federated.get_stats()

    async def run_background_cycle(self):
        """
        Combined background cycle for social and federated activities.
        Should be called periodically.
        """
        # Run social companionship if idle
        if self.is_idle_enough():
            await self.initiate_companionship_cycle()

        # Run federated sync if due
        await self.run_federated_sync()
