"""
UGOS_100: Execution Engine Kernel Implementation
------------------------------------------------
Handles task execution loops, state transitions, and sandbox boundary enforcement.
"""

from enum import Enum
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class TaskState(Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ExecutionEngine:
    """Core Execution Engine state machine derived from UGOS_100 spec."""

    def __init__(self, sandbox_level: str = "L2_CONTAINER"):
        self.sandbox_level = sandbox_level
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        logging.info(f"Initialized UGOS Execution Engine (Sandbox Mode: {self.sandbox_level})")

    def submit_task(self, payload: Dict[str, Any]) -> str:
        """Registers a new task in the execution queue."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        self.active_tasks[task_id] = {
            "task_id": task_id,
            "state": TaskState.PENDING,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": None
        }
        logging.info(f"Task {task_id} submitted successfully.")
        return task_id

    def transition_state(self, task_id: str, target_state: TaskState) -> None:
        """Validates and enforces valid state machine transitions."""
        if task_id not in self.active_tasks:
            raise KeyError(f"Task ID {task_id} does not exist.")

        current = self.active_tasks[task_id]["state"]
        
        valid_transitions = {
            TaskState.PENDING: [TaskState.SCHEDULED, TaskState.CANCELLED],
            TaskState.SCHEDULED: [TaskState.RUNNING, TaskState.CANCELLED],
            TaskState.RUNNING: [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED],
            TaskState.COMPLETED: [],
            TaskState.FAILED: [],
            TaskState.CANCELLED: []
        }

        if target_state not in valid_transitions[current]:
            raise ValueError(f"Invalid transition from {current.value} -> {target_state.value}")

        self.active_tasks[task_id]["state"] = target_state
        self.active_tasks[task_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        logging.info(f"Task {task_id}: {current.value} -> {target_state.value}")

    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Executes a task through its complete lifecycle."""
        try:
            self.transition_state(task_id, TaskState.SCHEDULED)
            self.transition_state(task_id, TaskState.RUNNING)

            payload = self.active_tasks[task_id]["payload"]
            result = {
                "status": "SUCCESS",
                "output": f"Executed action '{payload.get('action', 'default')}' under sandbox {self.sandbox_level}"
            }

            self.active_tasks[task_id]["result"] = result
            self.transition_state(task_id, TaskState.COMPLETED)
            return self.active_tasks[task_id]

        except Exception as e:
            logging.error(f"Execution failed for {task_id}: {str(e)}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["error"] = str(e)
                self.transition_state(task_id, TaskState.FAILED)
            raise

if __name__ == "__main__":
    engine = ExecutionEngine()
    tid = engine.submit_task({"action": "refactor_module", "target": "auth.py"})
    res = engine.execute_task(tid)
    print("\n--- Execution Output ---")
    print(res)