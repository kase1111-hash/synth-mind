"""
Memory System - Hybrid vector + relational storage.
Manages episodic memory, semantic embeddings, and persistent state.
"""

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np

# Optional: FAISS for vector search
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not available, using fallback vector search")

# Optional: sentence-transformers for local embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Optional: OpenAI for cloud embeddings
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EmbeddingProvider:
    """
    Multi-backend embedding provider with automatic fallback.
    Priority: sentence-transformers > OpenAI > hash-based placeholder
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.provider_name = "none"
        self.model = None
        self._init_provider()

    def _init_provider(self):
        """Initialize the best available embedding provider."""
        # Try sentence-transformers first (local, free, good quality)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # all-MiniLM-L6-v2 is fast and produces 384-dim embeddings
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.dimension = 384
                self.provider_name = "sentence-transformers"
                print("✓ Using sentence-transformers for embeddings")
                return
            except Exception as e:
                print(f"⚠️  sentence-transformers init failed: {e}")

        # Try OpenAI embeddings (cloud, requires API key)
        if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
            try:
                self.model = openai.OpenAI()
                self.dimension = 1536  # text-embedding-3-small dimension
                self.provider_name = "openai"
                print("✓ Using OpenAI for embeddings")
                return
            except Exception as e:
                print(f"⚠️  OpenAI embeddings init failed: {e}")

        # Fallback to hash-based (deterministic but not semantic)
        self.provider_name = "hash-fallback"
        self.dimension = 384
        print("⚠️  Using hash-based fallback embeddings (install sentence-transformers for better quality)")

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for text using the best available provider."""
        if self.provider_name == "sentence-transformers":
            return self._embed_sentence_transformers(text)
        elif self.provider_name == "openai":
            return self._embed_openai(text)
        else:
            return self._embed_hash_fallback(text)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for multiple texts (more efficient)."""
        if self.provider_name == "sentence-transformers":
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.astype(np.float32)
        elif self.provider_name == "openai":
            return np.array([self._embed_openai(t) for t in texts], dtype=np.float32)
        else:
            return np.array([self._embed_hash_fallback(t) for t in texts], dtype=np.float32)

    def _embed_sentence_transformers(self, text: str) -> np.ndarray:
        """Embed using sentence-transformers."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)

    def _embed_openai(self, text: str) -> np.ndarray:
        """Embed using OpenAI API (synchronous - use embed_async for async contexts)."""
        try:
            response = self.model.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            print(f"⚠️  OpenAI embedding failed: {e}, using fallback")
            return self._embed_hash_fallback(text)

    async def embed_async(self, text: str) -> np.ndarray:
        """Generate embedding asynchronously (safe for async contexts)."""
        import asyncio
        return await asyncio.to_thread(self.embed, text)

    async def embed_batch_async(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for multiple texts asynchronously."""
        import asyncio
        return await asyncio.to_thread(self.embed_batch, texts)

    def _embed_hash_fallback(self, text: str) -> np.ndarray:
        """Deterministic hash-based fallback (not semantic, but consistent)."""
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        return np.random.randn(self.dimension).astype(np.float32)

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

class MemorySystem:
    """Hybrid memory system with episodic and semantic storage."""

    def __init__(self, state_dir: str = "state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)

        self.db_path = self.state_dir / "memory.db"
        self.embeddings_path = self.state_dir / "embeddings"
        self.embeddings_path.mkdir(exist_ok=True)

        self.db = None
        self.vector_store = None
        self.embedding_provider: Optional[EmbeddingProvider] = None
        self.dimension = 384  # Updated after embedding provider init

        # Semantic memory index mapping (FAISS index -> DB id)
        self.semantic_id_map: list[int] = []

        self.last_activity_time = time.time()
        self.current_turn = 0
        self.max_context_length = 8192

        # Recent context embeddings for coherence tracking
        self._context_embeddings: list[np.ndarray] = []
        self._max_context_embeddings = 20

    async def initialize(self):
        """Initialize database, embedding provider, and vector store."""
        # Initialize embedding provider first (determines dimension)
        self.embedding_provider = EmbeddingProvider()
        self.dimension = self.embedding_provider.dimension

        self._init_database()
        self._init_vector_store()
        self._load_persistent_state()
        self._rebuild_semantic_index()

    def _init_database(self):
        """Initialize SQLite database for structured memory."""
        # Use check_same_thread=False for async contexts where DB may be accessed
        # from different threads. We rely on SQLite's internal serialization.
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.db.cursor()

        # Episodic memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                event_type TEXT,
                content TEXT,
                valence REAL,
                metadata TEXT
            )
        """)

        # Long-term semantic storage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS long_term (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at REAL
            )
        """)

        # Conversation turns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                user_input TEXT,
                assistant_response TEXT,
                metadata TEXT
            )
        """)

        # Uncertainty log for self-healing (Query Rating system)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uncertainty_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                user_message TEXT,
                parsed_intent TEXT,
                confidence_score REAL,
                context TEXT,
                signals TEXT,
                resolved INTEGER DEFAULT 0,
                resolution_pattern TEXT
            )
        """)

        # Semantic memories for vector search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                content TEXT,
                category TEXT,
                importance REAL DEFAULT 0.5,
                metadata TEXT
            )
        """)

        self.db.commit()

    def _init_vector_store(self):
        """Initialize FAISS vector store for semantic search."""
        if FAISS_AVAILABLE:
            index_path = self.embeddings_path / "index.faiss"
            id_map_path = self.embeddings_path / "id_map.json"

            if index_path.exists():
                self.vector_store = faiss.read_index(str(index_path))
                # Load ID mapping
                if id_map_path.exists():
                    with open(id_map_path) as f:
                        self.semantic_id_map = json.load(f)
            else:
                # Use IndexFlatIP for cosine similarity (after L2 normalization)
                self.vector_store = faiss.IndexFlatIP(self.dimension)
        else:
            # Fallback: in-memory list of (embedding, db_id) tuples
            self.vector_store = []

    def _rebuild_semantic_index(self):
        """Rebuild vector index from database (on startup if needed)."""
        if not self.db:
            return

        cursor = self.db.cursor()
        cursor.execute("SELECT id, content FROM semantic_memories ORDER BY id")
        rows = cursor.fetchall()

        if not rows:
            return

        # Check if index needs rebuilding
        current_count = len(self.semantic_id_map) if self.semantic_id_map else 0
        if current_count == len(rows):
            return  # Already in sync

        print(f"Rebuilding semantic index for {len(rows)} memories...")

        # Reset index
        if FAISS_AVAILABLE:
            self.vector_store = faiss.IndexFlatIP(self.dimension)
        else:
            self.vector_store = []

        self.semantic_id_map = []

        # Batch embed all content
        ids = [row[0] for row in rows]
        texts = [row[1] for row in rows]
        embeddings = self.embedding_provider.embed_batch(texts)

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings) if FAISS_AVAILABLE else None

        # Add to index
        if FAISS_AVAILABLE:
            self.vector_store.add(embeddings)
        else:
            for i, emb in enumerate(embeddings):
                self.vector_store.append((emb, ids[i]))

        self.semantic_id_map = ids
        print(f"✓ Semantic index rebuilt with {len(ids)} memories")

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for text using the configured provider."""
        if self.embedding_provider:
            return self.embedding_provider.embed(text)
        # Fallback if provider not initialized
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        return np.random.randn(self.dimension).astype(np.float32)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for multiple texts (more efficient)."""
        if self.embedding_provider:
            return self.embedding_provider.embed_batch(texts)
        return np.array([self.embed(t) for t in texts], dtype=np.float32)

    def store_episodic(
        self, event: str, content: dict[str, Any], valence: float = 0.0
    ):
        """Store episodic memory."""
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO episodes (timestamp, event_type, content, valence, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                time.time(),
                event,
                json.dumps(content),
                valence,
                json.dumps({})
            )
        )
        self.db.commit()

    def retrieve_recent_episodic(self, n: int = 100) -> list[dict]:
        """Retrieve recent episodic memories."""
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT event_type, content, valence, timestamp
            FROM episodes
            ORDER BY id DESC
            LIMIT ?
            """,
            (n,)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                "event": row[0],
                "content": json.loads(row[1]),
                "valence": row[2],
                "timestamp": row[3]
            })

        return results

    def store_turn(self, user_input: str, assistant_response: str):
        """Store conversation turn."""
        self.current_turn += 1
        self.last_activity_time = time.time()

        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO turns (timestamp, user_input, assistant_response, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (time.time(), user_input, assistant_response, json.dumps({}))
        )
        self.db.commit()

    def store_persistent(self, key: str, value: Any):
        """Store persistent key-value data."""
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO long_term (key, value, updated_at)
            VALUES (?, ?, ?)
            """,
            (key, json.dumps(value), time.time())
        )
        self.db.commit()

    def retrieve_persistent(self, key: str) -> Optional[Any]:
        """Retrieve persistent data."""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT value FROM long_term WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def _load_persistent_state(self):
        """Load any persistent state on startup."""
        pass  # Loaded by individual modules

    def update_last_activity_time(self):
        """Update activity timestamp."""
        self.last_activity_time = time.time()

    # ============================================
    # Semantic Memory System
    # ============================================

    def store_semantic(
        self,
        content: str,
        category: str = "general",
        importance: float = 0.5,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Store a semantic memory with vector embedding.
        Returns the memory ID.
        """
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO semantic_memories (timestamp, content, category, importance, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                time.time(),
                content,
                category,
                importance,
                json.dumps(metadata or {})
            )
        )
        self.db.commit()
        memory_id = cursor.lastrowid

        # Generate and store embedding
        embedding = self.embed(content)

        # Normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # Add to vector store
        if FAISS_AVAILABLE:
            self.vector_store.add(embedding.reshape(1, -1))
        else:
            self.vector_store.append((embedding, memory_id))

        self.semantic_id_map.append(memory_id)

        return memory_id

    def search_semantic(
        self,
        query: str,
        k: int = 5,
        category: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> list[dict]:
        """
        Search semantic memories by similarity to query.
        Returns list of memories with similarity scores.
        """
        if not self.semantic_id_map:
            return []

        # Generate query embedding
        query_embedding = self.embed(query)

        # Normalize for cosine similarity
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm

        # Search vector store
        if FAISS_AVAILABLE:
            query_embedding = query_embedding.reshape(1, -1)
            similarities, indices = self.vector_store.search(query_embedding, min(k * 2, len(self.semantic_id_map)))
            results = []
            for sim, idx in zip(similarities[0], indices[0]):
                if idx < 0 or idx >= len(self.semantic_id_map):
                    continue
                if sim < min_similarity:
                    continue
                db_id = self.semantic_id_map[idx]
                results.append((db_id, float(sim)))
        else:
            # Fallback: linear search
            similarities = []
            for emb, db_id in self.vector_store:
                sim = EmbeddingProvider.cosine_similarity(query_embedding, emb)
                if sim >= min_similarity:
                    similarities.append((db_id, sim))
            similarities.sort(key=lambda x: x[1], reverse=True)
            results = similarities[:k * 2]

        # Fetch from database
        memories = []
        cursor = self.db.cursor()
        for db_id, similarity in results[:k]:
            cursor.execute(
                """
                SELECT id, timestamp, content, category, importance, metadata
                FROM semantic_memories WHERE id = ?
                """,
                (db_id,)
            )
            row = cursor.fetchone()
            if row:
                # Filter by category if specified
                if category and row[3] != category:
                    continue
                memories.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "content": row[2],
                    "category": row[3],
                    "importance": row[4],
                    "metadata": json.loads(row[5]) if row[5] else {},
                    "similarity": similarity
                })

        return memories

    def get_related_memories(
        self,
        text: str,
        k: int = 3,
        include_episodic: bool = True
    ) -> dict[str, list[dict]]:
        """
        Get memories related to text from multiple sources.
        Combines semantic search with recent episodic memories.
        """
        result = {
            "semantic": self.search_semantic(text, k=k),
            "episodic": []
        }

        if include_episodic:
            # Get recent episodic and score by text similarity
            recent = self.retrieve_recent_episodic(n=20)
            if recent and self.embedding_provider:
                text_emb = self.embed(text)
                scored = []
                for ep in recent:
                    content_str = json.dumps(ep["content"])
                    ep_emb = self.embed(content_str)
                    sim = EmbeddingProvider.cosine_similarity(text_emb, ep_emb)
                    scored.append((ep, sim))
                scored.sort(key=lambda x: x[1], reverse=True)
                result["episodic"] = [
                    {**ep, "similarity": sim}
                    for ep, sim in scored[:k]
                ]

        return result

    def track_context_embedding(self, text: str):
        """Track embedding for coherence drift detection."""
        emb = self.embed(text)
        self._context_embeddings.append(emb)
        if len(self._context_embeddings) > self._max_context_embeddings:
            self._context_embeddings.pop(0)

    def grounding_confidence(self, text: str) -> float:
        """
        Assess grounding of text in known memory using semantic similarity.
        Returns confidence score 0-1 based on how well text matches stored knowledge.
        """
        if not self.semantic_id_map:
            return 0.5  # Neutral if no memories stored

        # Search for similar memories
        similar = self.search_semantic(text, k=3, min_similarity=0.3)

        if not similar:
            return 0.3  # Low confidence - no similar memories

        # Weight by similarity and importance
        weighted_sum = 0.0
        weight_total = 0.0
        for mem in similar:
            weight = mem["importance"]
            weighted_sum += mem["similarity"] * weight
            weight_total += weight

        if weight_total == 0:
            return 0.5

        # Scale to 0-1 range (similarity is already 0-1)
        confidence = weighted_sum / weight_total

        # Boost slightly if multiple strong matches
        if len(similar) >= 2 and similar[1]["similarity"] > 0.6:
            confidence = min(1.0, confidence * 1.1)

        return confidence

    def detect_coherence_drift(self, threshold: float = 0.7) -> bool:
        """
        Detect if context coherence has drifted using embedding similarity.
        Returns True if recent context is incoherent (drifted).
        """
        if len(self._context_embeddings) < 3:
            return False  # Not enough context to judge

        # Compare recent embeddings to earlier ones
        recent = self._context_embeddings[-3:]
        earlier = self._context_embeddings[:-3] if len(self._context_embeddings) > 3 else []

        if not earlier:
            # Compare within recent only
            similarities = []
            for i in range(len(recent)):
                for j in range(i + 1, len(recent)):
                    sim = EmbeddingProvider.cosine_similarity(recent[i], recent[j])
                    similarities.append(sim)
            if similarities:
                avg_sim = sum(similarities) / len(similarities)
                return avg_sim < threshold
            return False

        # Compare recent to earlier
        cross_similarities = []
        for r in recent:
            for e in earlier:
                sim = EmbeddingProvider.cosine_similarity(r, e)
                cross_similarities.append(sim)

        if cross_similarities:
            avg_cross = sum(cross_similarities) / len(cross_similarities)
            return avg_cross < threshold

        return False

    def get_embedding_stats(self) -> dict:
        """Get statistics about the embedding system."""
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM semantic_memories")
        total_memories = cursor.fetchone()[0]

        return {
            "provider": self.embedding_provider.provider_name if self.embedding_provider else "none",
            "dimension": self.dimension,
            "total_semantic_memories": total_memories,
            "index_size": len(self.semantic_id_map),
            "context_embeddings_tracked": len(self._context_embeddings),
            "faiss_available": FAISS_AVAILABLE
        }

    # ============================================
    # Self-Healing Query Rating System
    # ============================================

    def log_uncertainty(
        self,
        user_message: str,
        parsed_intent: str,
        confidence_score: float,
        context: str,
        signals: dict[str, float]
    ) -> int:
        """
        Log an uncertainty event for later pattern analysis.
        Called when confidence is below threshold or intent is ambiguous.
        Returns the log entry ID.
        """
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO uncertainty_log
            (timestamp, user_message, parsed_intent, confidence_score, context, signals)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                time.time(),
                user_message,
                parsed_intent,
                confidence_score,
                context[:2000] if context else "",  # Limit context size
                json.dumps(signals)
            )
        )
        self.db.commit()
        return cursor.lastrowid

    def get_uncertainty_logs(
        self,
        limit: int = 500,
        unresolved_only: bool = False,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0
    ) -> list[dict]:
        """
        Retrieve uncertainty logs for pattern analysis.
        Used by the harvest cycle to identify linguistic patterns.
        """
        cursor = self.db.cursor()

        query = """
            SELECT id, timestamp, user_message, parsed_intent,
                   confidence_score, context, signals, resolved, resolution_pattern
            FROM uncertainty_log
            WHERE confidence_score >= ? AND confidence_score <= ?
        """
        params = [min_confidence, max_confidence]

        if unresolved_only:
            query += " AND resolved = 0"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "user_message": row[2],
                "parsed_intent": row[3],
                "confidence_score": row[4],
                "context": row[5],
                "signals": json.loads(row[6]) if row[6] else {},
                "resolved": bool(row[7]),
                "resolution_pattern": row[8]
            })

        return results

    def mark_uncertainty_resolved(
        self,
        log_id: int,
        resolution_pattern: str
    ):
        """
        Mark an uncertainty log entry as resolved with the pattern that fixed it.
        Called after pattern harvest identifies a fix.
        """
        cursor = self.db.cursor()
        cursor.execute(
            """
            UPDATE uncertainty_log
            SET resolved = 1, resolution_pattern = ?
            WHERE id = ?
            """,
            (resolution_pattern, log_id)
        )
        self.db.commit()

    def get_uncertainty_stats(self) -> dict:
        """Get statistics about uncertainty logs for monitoring."""
        cursor = self.db.cursor()

        # Total count
        cursor.execute("SELECT COUNT(*) FROM uncertainty_log")
        total = cursor.fetchone()[0]

        # Unresolved count
        cursor.execute("SELECT COUNT(*) FROM uncertainty_log WHERE resolved = 0")
        unresolved = cursor.fetchone()[0]

        # Average confidence
        cursor.execute("SELECT AVG(confidence_score) FROM uncertainty_log")
        avg_confidence = cursor.fetchone()[0] or 0.0

        # Recent count (last 24 hours)
        day_ago = time.time() - 86400
        cursor.execute(
            "SELECT COUNT(*) FROM uncertainty_log WHERE timestamp > ?",
            (day_ago,)
        )
        recent = cursor.fetchone()[0]

        return {
            "total_entries": total,
            "unresolved": unresolved,
            "resolved": total - unresolved,
            "resolution_rate": (total - unresolved) / total if total > 0 else 0.0,
            "avg_confidence": avg_confidence,
            "last_24h": recent
        }

    async def save_state(self):
        """Save all state to disk."""
        if self.db:
            self.db.commit()

        if FAISS_AVAILABLE and self.vector_store:
            faiss.write_index(
                self.vector_store,
                str(self.embeddings_path / "index.faiss")
            )

        # Save semantic ID mapping
        if self.semantic_id_map:
            id_map_path = self.embeddings_path / "id_map.json"
            with open(id_map_path, 'w') as f:
                json.dump(self.semantic_id_map, f)
