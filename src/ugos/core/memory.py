"""
UGOS_300: Persistent Memory Engine & Context Architecture
---------------------------------------------------------
Provides short-term episodic session logging and long-term tagged semantic fact storage
backed by a persistent SQLite database (`ugos_memory.db`).
"""

import sys
import logging
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DB_PATH = Path("ugos_memory.db")


class SQLiteMemoryStore:
    """Persistent SQLite database manager for semantic facts and episodic logs."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes database schema for episodic logs and semantic facts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table 1: Episodic Session Events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            # Table 2: Semantic Tagged Facts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS semantic_facts (
                    fact_key TEXT PRIMARY KEY,
                    fact_value TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def store_event(self, session_id: str, agent_id: str, action: str, details: Dict[str, Any]):
        """Persists an episodic event row to SQLite."""
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute(
                "INSERT INTO episodic_events (session_id, agent_id, action, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                (session_id, agent_id, action, json.dumps(details), timestamp)
            )
            conn.commit()

    def fetch_recent_events(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent session events from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT agent_id, action, details, timestamp FROM episodic_events WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [
                {
                    "agent_id": row["agent_id"],
                    "action": row["action"],
                    "details": json.loads(row["details"]),
                    "timestamp": row["timestamp"]
                }
                for row in reversed(rows)
            ]

    def set_fact(self, key: str, value: Any, tags: List[str]):
        """Upserts a tagged fact into semantic SQLite storage."""
        updated_at = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute(
                "INSERT INTO semantic_facts (fact_key, fact_value, tags, updated_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(fact_key) DO UPDATE SET fact_value=excluded.fact_value, tags=excluded.tags, updated_at=excluded.updated_at",
                (key, json.dumps(value), json.dumps(tags), updated_at)
            )
            conn.commit()

    def get_facts_by_tag(self, tag: str) -> Dict[str, Any]:
        """Queries semantic facts by matching tag in JSON array."""
        results = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fact_key, fact_value, tags FROM semantic_facts")
            for row in cursor.fetchall():
                tags = json.loads(row["tags"])
                if tag in tags:
                    results[row["fact_key"]] = json.loads(row["fact_value"])
        return results


class MemorySession:
    """Episodic Session Memory wrapper tied to SQLite database persistence."""

    def __init__(self, session_id: str, store: SQLiteMemoryStore):
        self.session_id = session_id
        self.store = store

    def log_event(self, agent_id: str, action: str, details: Dict[str, Any]):
        self.store.store_event(self.session_id, agent_id, action, details)

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.store.fetch_recent_events(self.session_id, limit)


class MemoryEngine:
    """UGOS Memory Architecture coordinating SQLite episodic and semantic storage."""

    def __init__(self, db_path: Path = DB_PATH):
        self.store = SQLiteMemoryStore(db_path)
        self.sessions: Dict[str, MemorySession] = {}
        logging.info(f"Initialized UGOS Memory Engine (SQLite DB: {db_path})")

    def get_or_create_session(self, session_id: str) -> MemorySession:
        if session_id not in self.sessions:
            self.sessions[session_id] = MemorySession(session_id, self.store)
        return self.sessions[session_id]

    def set_global_fact(self, key: str, value: Any, tags: List[str]):
        self.store.set_fact(key, value, tags)

    def get_facts_by_tag(self, tag: str) -> Dict[str, Any]:
        return self.store.get_facts_by_tag(tag)


if __name__ == "__main__":
    print("\n--- Testing Persistent SQLite Memory Engine ---")
    memory = MemoryEngine()

    # 1. Store persistent facts in SQLite
    memory.set_global_fact("system_version", "v1.0-release", tags=["core", "build"])
    memory.set_global_fact("db_engine", "SQLite3", tags=["core", "storage"])

    # Query facts
    core_facts = memory.get_facts_by_tag("core")
    print("\n[Retrieved Core Facts from SQLite]:", core_facts)

    # 2. Log episodic session event to SQLite
    session = memory.get_or_create_session("sess_persistent_01")
    session.log_event("ag_dev_01", "deploy_check", {"status": "SUCCESS", "db": "ugos_memory.db"})

    history = session.get_recent_history(limit=5)
    print("\n[Retrieved Episodic History from SQLite]:")
    for event in history:
        print(" ", event)