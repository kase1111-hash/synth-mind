"""
Federated Learning Layer for Social Companionship
Enables privacy-preserving knowledge sharing between synth-mind instances.

Key principles:
1. Never share user data - only anonymized patterns
2. Differential privacy for all shared gradients
3. Consensus-based validation before applying updates
4. Local learning combined with distributed knowledge
"""

import hashlib
import json
import random
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Optional

import numpy as np

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class SharedPattern:
    """A learnable pattern that can be shared across peers."""
    pattern_type: str  # 'resolution', 'intent', 'calibration'
    pattern_hash: str  # Hash of the pattern (not raw content)
    pattern_embedding: list[float]  # Anonymized embedding
    success_rate: float  # 0-1 effectiveness
    confidence: float  # 0-1 certainty
    sample_count: int  # Number of observations (k-anonymity)
    metadata: dict[str, Any]  # Non-identifying metadata
    timestamp: float


@dataclass
class FederatedUpdate:
    """An update to be shared or received from peers."""
    sender_id: str  # Anonymized sender identifier
    patterns: list[SharedPattern]
    aggregation_round: int
    signature: str  # Simple integrity check


class PrivacyFilter:
    """
    Ensures all shared data meets privacy requirements.
    Implements differential privacy and k-anonymity.
    """

    def __init__(
        self,
        epsilon: float = 1.0,  # Differential privacy parameter
        k_anonymity: int = 5,  # Minimum observations before sharing
        noise_scale: float = 0.1  # Noise added to embeddings
    ):
        self.epsilon = epsilon
        self.k_anonymity = k_anonymity
        self.noise_scale = noise_scale

    def can_share(self, pattern: SharedPattern) -> bool:
        """Check if pattern meets privacy requirements."""
        # K-anonymity: need enough observations
        if pattern.sample_count < self.k_anonymity:
            return False

        # Don't share patterns with low confidence
        if pattern.confidence < 0.5:
            return False

        return True

    def add_differential_noise(self, embedding: list[float]) -> list[float]:
        """Add calibrated noise for differential privacy."""
        noise = np.random.laplace(0, self.noise_scale / self.epsilon, len(embedding))
        noisy = np.array(embedding) + noise
        # Normalize to maintain embedding properties
        norm = np.linalg.norm(noisy)
        if norm > 0:
            noisy = noisy / norm
        return noisy.tolist()

    def anonymize_pattern(self, pattern: SharedPattern) -> SharedPattern:
        """Apply privacy protections to a pattern."""
        # Add noise to embedding
        noisy_embedding = self.add_differential_noise(pattern.pattern_embedding)

        # Quantize success rate (reduce precision)
        quantized_success = round(pattern.success_rate * 10) / 10

        # Remove any potentially identifying metadata
        safe_metadata = {
            k: v for k, v in pattern.metadata.items()
            if k in ('category', 'pattern_class', 'general_domain')
        }

        return SharedPattern(
            pattern_type=pattern.pattern_type,
            pattern_hash=pattern.pattern_hash,
            pattern_embedding=noisy_embedding,
            success_rate=quantized_success,
            confidence=round(pattern.confidence, 2),
            sample_count=pattern.sample_count,
            metadata=safe_metadata,
            timestamp=pattern.timestamp
        )


class PatternAggregator:
    """
    Aggregates patterns from multiple peers using weighted averaging.
    Implements federated averaging for embeddings.
    """

    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.pattern_buffer: dict[str, list[SharedPattern]] = defaultdict(list)

    def add_patterns(self, patterns: list[SharedPattern], source_weight: float = 1.0):
        """Add patterns from a peer to the aggregation buffer."""
        for pattern in patterns:
            # Group by pattern hash
            self.pattern_buffer[pattern.pattern_hash].append(pattern)

    def aggregate(self) -> list[SharedPattern]:
        """
        Aggregate buffered patterns using federated averaging.
        Returns consensus patterns that multiple peers agree on.
        """
        aggregated = []

        for pattern_hash, patterns in self.pattern_buffer.items():
            # Need at least 2 peers to agree
            if len(patterns) < 2:
                continue

            # Weighted average of embeddings
            embeddings = np.array([p.pattern_embedding for p in patterns])
            weights = np.array([p.confidence * p.sample_count for p in patterns])
            weights = weights / weights.sum()

            avg_embedding = np.average(embeddings, axis=0, weights=weights)
            avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)

            # Aggregate success rates and confidence
            avg_success = np.average(
                [p.success_rate for p in patterns],
                weights=weights
            )
            avg_confidence = np.average(
                [p.confidence for p in patterns],
                weights=weights
            )

            # Combine sample counts
            total_samples = sum(p.sample_count for p in patterns)

            # Merge metadata (keep common keys)
            merged_metadata = {}
            if patterns:
                common_keys = set(patterns[0].metadata.keys())
                for p in patterns[1:]:
                    common_keys &= set(p.metadata.keys())
                for key in common_keys:
                    values = [p.metadata[key] for p in patterns]
                    # Keep most common value
                    merged_metadata[key] = max(set(values), key=values.count)

            aggregated.append(SharedPattern(
                pattern_type=patterns[0].pattern_type,
                pattern_hash=pattern_hash,
                pattern_embedding=avg_embedding.tolist(),
                success_rate=float(avg_success),
                confidence=float(avg_confidence),
                sample_count=total_samples,
                metadata=merged_metadata,
                timestamp=time.time()
            ))

        # Clear buffer after aggregation
        self.pattern_buffer.clear()

        return aggregated


class FederatedLearningLayer:
    """
    Main federated learning coordinator.
    Manages pattern extraction, sharing, and integration.
    """

    def __init__(
        self,
        memory,
        llm,
        node_id: Optional[str] = None,
        peer_endpoints: list[str] = None,
        privacy_epsilon: float = 1.0,
        k_anonymity: int = 5,
        sync_interval_minutes: int = 30
    ):
        if peer_endpoints is None:
            peer_endpoints = []
        self.memory = memory
        self.llm = llm
        self.node_id = node_id or self._generate_node_id()
        self.peers = peer_endpoints

        self.privacy_filter = PrivacyFilter(
            epsilon=privacy_epsilon,
            k_anonymity=k_anonymity
        )
        self.aggregator = PatternAggregator()

        self.sync_interval = sync_interval_minutes * 60
        self.last_sync = 0
        self.aggregation_round = 0

        # Local pattern storage
        self.local_patterns: dict[str, SharedPattern] = {}
        self.received_patterns: dict[str, SharedPattern] = {}

        # Stats
        self.stats = {
            "patterns_shared": 0,
            "patterns_received": 0,
            "sync_rounds": 0,
            "peers_contacted": 0
        }

    def _generate_node_id(self) -> str:
        """Generate anonymous node identifier."""
        random_bytes = random.randbytes(16)
        return hashlib.sha256(random_bytes).hexdigest()[:16]

    def _hash_pattern_content(self, content: str) -> str:
        """Create privacy-preserving hash of pattern content."""
        # Salt to prevent rainbow table attacks
        salt = "synth_mind_federated_v1"
        return hashlib.sha256(f"{salt}:{content}".encode()).hexdigest()[:32]

    async def extract_shareable_patterns(self) -> list[SharedPattern]:
        """
        Extract patterns from local memory that can be shared.
        Focuses on uncertainty resolution patterns.
        """
        patterns = []

        # Get uncertainty logs that were resolved
        try:
            logs = self.memory.get_uncertainty_logs(limit=200, unresolved_only=False)
        except Exception:
            return []

        # Group by resolution pattern
        resolution_groups: dict[str, list[dict]] = defaultdict(list)
        for log in logs:
            if log.get("resolved") and log.get("resolution_pattern"):
                resolution_groups[log["resolution_pattern"]].append(log)

        # Create patterns from groups that meet k-anonymity
        for resolution, group in resolution_groups.items():
            if len(group) < self.privacy_filter.k_anonymity:
                continue

            # Calculate success metrics
            avg_confidence = sum(entry["confidence_score"] for entry in group) / len(group)

            # Create embedding from resolution pattern (anonymized)
            if hasattr(self.memory, 'embed'):
                embedding = self.memory.embed(resolution).tolist()
            else:
                # Fallback: hash-based pseudo-embedding
                embedding = self._hash_to_embedding(resolution)

            pattern = SharedPattern(
                pattern_type="resolution",
                pattern_hash=self._hash_pattern_content(resolution),
                pattern_embedding=embedding,
                success_rate=1.0 - avg_confidence,  # Lower uncertainty = success
                confidence=min(1.0, len(group) / 20),  # More samples = confidence
                sample_count=len(group),
                metadata={
                    "category": "uncertainty_resolution",
                    "general_domain": "intent_parsing"
                },
                timestamp=time.time()
            )

            if self.privacy_filter.can_share(pattern):
                patterns.append(self.privacy_filter.anonymize_pattern(pattern))

        return patterns

    def _hash_to_embedding(self, text: str, dim: int = 384) -> list[float]:
        """Fallback: create pseudo-embedding from hash."""
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        emb = np.random.randn(dim)
        return (emb / np.linalg.norm(emb)).tolist()

    async def share_with_peer(self, peer_endpoint: str) -> bool:
        """Share local patterns with a specific peer."""
        if not HTTPX_AVAILABLE:
            return False

        patterns = await self.extract_shareable_patterns()
        if not patterns:
            return True  # Nothing to share is okay

        update = FederatedUpdate(
            sender_id=self.node_id,
            patterns=patterns,
            aggregation_round=self.aggregation_round,
            signature=self._sign_update(patterns)
        )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{peer_endpoint}/api/federated/receive",
                    json={
                        "sender_id": update.sender_id,
                        "patterns": [asdict(p) for p in update.patterns],
                        "aggregation_round": update.aggregation_round,
                        "signature": update.signature
                    }
                )
                if resp.status_code == 200:
                    self.stats["patterns_shared"] += len(patterns)
                    self.stats["peers_contacted"] += 1
                    return True
        except Exception as e:
            print(f"⚠️  Federated share failed: {e}")

        return False

    async def receive_update(self, update_data: dict) -> dict:
        """
        Receive and process an update from a peer.
        Returns acknowledgment with local patterns.
        """
        try:
            patterns = [
                SharedPattern(**p) for p in update_data.get("patterns", [])
            ]

            # Validate patterns
            valid_patterns = []
            for p in patterns:
                if self._validate_received_pattern(p):
                    valid_patterns.append(p)

            # Add to aggregator
            self.aggregator.add_patterns(valid_patterns)
            self.stats["patterns_received"] += len(valid_patterns)

            # Store received patterns
            for p in valid_patterns:
                self.received_patterns[p.pattern_hash] = p

            # Return our patterns in response
            our_patterns = await self.extract_shareable_patterns()

            return {
                "success": True,
                "received_count": len(valid_patterns),
                "patterns": [asdict(p) for p in our_patterns[:10]]  # Limit response
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _validate_received_pattern(self, pattern: SharedPattern) -> bool:
        """Validate a received pattern before accepting."""
        # Check reasonable bounds
        if not (0 <= pattern.success_rate <= 1):
            return False
        if not (0 <= pattern.confidence <= 1):
            return False
        if pattern.sample_count < 1:
            return False

        # Check embedding is normalized
        emb = np.array(pattern.pattern_embedding)
        if abs(np.linalg.norm(emb) - 1.0) > 0.1:
            return False

        return True

    def _sign_update(self, patterns: list[SharedPattern]) -> str:
        """Create simple integrity signature."""
        content = json.dumps([asdict(p) for p in patterns], sort_keys=True)
        return hashlib.sha256(f"{self.node_id}:{content}".encode()).hexdigest()[:16]

    async def sync_round(self) -> dict:
        """
        Perform a full synchronization round with all peers.
        """
        self.aggregation_round += 1

        results = {
            "round": self.aggregation_round,
            "peers_synced": 0,
            "patterns_shared": 0,
            "patterns_aggregated": 0
        }

        # Share with each peer
        for peer in self.peers:
            if await self.share_with_peer(peer):
                results["peers_synced"] += 1

        # Aggregate received patterns
        aggregated = self.aggregator.aggregate()
        results["patterns_aggregated"] = len(aggregated)

        # Apply aggregated patterns to local knowledge
        await self._apply_aggregated_patterns(aggregated)

        self.last_sync = time.time()
        self.stats["sync_rounds"] += 1

        return results

    async def _apply_aggregated_patterns(self, patterns: list[SharedPattern]):
        """
        Apply aggregated patterns to improve local knowledge.
        Uses consensus patterns to enhance uncertainty resolution.
        """
        for pattern in patterns:
            # Store in local received patterns
            self.received_patterns[pattern.pattern_hash] = pattern

            # If we have semantic memory, store the pattern embedding
            if hasattr(self.memory, 'store_semantic'):
                try:
                    self.memory.store_semantic(
                        content=f"federated_pattern:{pattern.pattern_hash}",
                        category="federated_learning",
                        importance=pattern.confidence,
                        metadata={
                            "pattern_type": pattern.pattern_type,
                            "success_rate": pattern.success_rate,
                            "sample_count": pattern.sample_count,
                            "source": "peer_aggregation"
                        }
                    )
                except Exception:
                    pass

    def should_sync(self) -> bool:
        """Check if it's time for a sync round."""
        return (time.time() - self.last_sync) > self.sync_interval

    async def run_background_sync(self):
        """Background task to periodically sync with peers."""
        if self.should_sync() and self.peers:
            await self.sync_round()

    def get_pattern_similarity(self, text: str) -> list[tuple[SharedPattern, float]]:
        """
        Find patterns similar to given text.
        Used to enhance local decision making.
        """
        if not self.received_patterns:
            return []

        if hasattr(self.memory, 'embed'):
            text_embedding = self.memory.embed(text)
        else:
            text_embedding = np.array(self._hash_to_embedding(text))

        results = []
        for pattern in self.received_patterns.values():
            pattern_emb = np.array(pattern.pattern_embedding)
            similarity = float(np.dot(text_embedding, pattern_emb))
            if similarity > 0.5:  # Threshold
                results.append((pattern, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:5]

    def get_stats(self) -> dict:
        """Get federated learning statistics."""
        return {
            **self.stats,
            "node_id": self.node_id[:8] + "...",
            "local_patterns": len(self.local_patterns),
            "received_patterns": len(self.received_patterns),
            "aggregation_round": self.aggregation_round,
            "peers_configured": len(self.peers),
            "last_sync_ago_minutes": (time.time() - self.last_sync) / 60 if self.last_sync else None,
            "privacy_epsilon": self.privacy_filter.epsilon,
            "k_anonymity": self.privacy_filter.k_anonymity
        }
