"""
Memory System - Hybrid vector + relational storage.
Manages episodic memory, semantic embeddings, and persistent state.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not available, using fallback memory")

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
        self.dimension = 384  # Standard embedding dimension
        
        self.last_activity_time = time.time()
        self.current_turn = 0
        self.max_context_length = 8192
    
    async def initialize(self):
        """Initialize database and vector store."""
        self._init_database()
        self._init_vector_store()
        self._load_persistent_state()
    
    def _init_database(self):
        """Initialize SQLite database for structured memory."""
        self.db = sqlite3.connect(self.db_path)
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

        self.db.commit()
    
    def _init_vector_store(self):
        """Initialize FAISS vector store for semantic search."""
        if FAISS_AVAILABLE:
            index_path = self.embeddings_path / "index.faiss"
            if index_path.exists():
                self.vector_store = faiss.read_index(str(index_path))
            else:
                self.vector_store = faiss.IndexFlatL2(self.dimension)
        else:
            # Fallback: in-memory list
            self.vector_store = []
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for text (simplified)."""
        # In production, use proper embedding model
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        return np.random.randn(self.dimension)
    
    def store_episodic(
        self, event: str, content: Dict[str, Any], valence: float = 0.0
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
    
    def retrieve_recent_episodic(self, n: int = 100) -> List[Dict]:
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
    
    def grounding_confidence(self, text: str) -> float:
        """Assess grounding of text in known memory (simplified)."""
        # In production: semantic similarity to known facts
        return 0.8  # Placeholder
    
    def detect_coherence_drift(self, threshold: float = 0.7) -> bool:
        """Detect if context coherence has drifted."""
        # In production: embedding similarity analysis
        return False  # Placeholder

    # ============================================
    # Self-Healing Query Rating System
    # ============================================

    def log_uncertainty(
        self,
        user_message: str,
        parsed_intent: str,
        confidence_score: float,
        context: str,
        signals: Dict[str, float]
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
    ) -> List[Dict]:
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

    def get_uncertainty_stats(self) -> Dict:
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
