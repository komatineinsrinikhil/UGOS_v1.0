"""
UGOS_300 / UGOS_301 / UGOS_302: Memory Architecture & Context Store
-------------------------------------------------------------------
Manages short-term episodic session buffers and long-term semantic
knowledge stores for UGOS agents.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class EpisodicMemory:
    """UGOS_301: Short-term session memory for tracking task turn events."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: List[Dict[str, Any]] = []

    def log_event(self, agent_id: str, action: str, details: Dict[str, Any]):
        """Logs a single action/turn event into episodic memory."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "action": action,
            "details": details
        }
        self.events.append(entry)

    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves the last N events from the session buffer."""
        return self.events[-limit:]


class SemanticMemory:
    """UGOS_302: Long-term knowledge store for persistent key-value context."""

    def __init__(self):
        self.store: Dict[str, Any] = {}

    def set_fact(self, key: str, value: Any, tags: Optional[List[str]] = None):
        """Stores a persistent fact with metadata and search tags."""
        self.store[key] = {
            "value": value,
            "tags": tags or [],
            "updated_at": datetime.now().isoformat()
        }

    def get_fact(self, key: str) -> Optional[Any]:
        """Retrieves a specific fact by key."""
        fact = self.store.get(key)
        return fact["value"] if fact else None

    def search_by_tag(self, tag: str) -> Dict[str, Any]:
        """Searches long-term memory for all facts matching a given tag."""
        return {k: v["value"] for k, v in self.store.items() if tag in v["tags"]}


class MemoryEngine:
    """UGOS_300: Unified Memory Engine coordinating Episodic & Semantic context."""

    def __init__(self):
        self.sessions: Dict[str, EpisodicMemory] = {}
        self.global_semantic = SemanticMemory()
        logging.info("Initialized UGOS Memory Engine")

    def get_or_create_session(self, session_id: str) -> EpisodicMemory:
        """Gets or initializes an episodic memory session buffer."""
        if session_id not in self.sessions:
            self.sessions[session_id] = EpisodicMemory(session_id)
        return self.sessions[session_id]


if __name__ == "__main__":
    memory = MemoryEngine()
    
    print("\n--- Testing Memory Architecture ---")
    
    # Test 1: Short-Term Episodic Memory
    session = memory.get_or_create_session("sess_001")
    session.log_event("agent_dev", "read_file", {"target": "execution.py"})
    session.log_event("agent_dev", "run_test", {"status": "PASSED"})
    
    history = session.get_recent_history(limit=2)
    print("\nEpisodic History Count:", len(history))
    print("Last Logged Action:", history[-1]["action"])
    
    # Test 2: Long-Term Semantic Memory
    memory.global_semantic.set_fact("env_target", "PRODUCTION", tags=["config", "deployment"])
    memory.global_semantic.set_fact("sandbox_profile", "L2_CONTAINER", tags=["config", "security"])
    
    config_facts = memory.global_semantic.search_by_tag("config")
    print("\nSemantic Search (tag='config'):", config_facts)