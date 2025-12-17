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
    
    async def save_state(self):
        """Save all state to disk."""
        if self.db:
            self.db.commit()
        
        if FAISS_AVAILABLE and self.vector_store:
            faiss.write_index(
                self.vector_store,
                str(self.embeddings_path / "index.faiss")
            )
