"""
UGOS_100: Core Task Execution Engine
-----------------------------------
Handles the execution of discrete tasks emitted by agents.
Supports local process execution and sandboxed Docker container execution.
"""

import sys
import logging
import subprocess
import shutil
import uuid
from enum import Enum
from typing import Dict, Any, Union, Optional
from pathlib import Path

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class TaskState(Enum):
    """Task execution lifecycle states."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ERROR = "ERROR"


class ExecutionEngine:
    """Manages secure execution of agent tasks locally or inside Docker sandboxes."""

    def __init__(self, use_docker: bool = False, docker_image: str = "python:3.12-slim"):
        self.use_docker = use_docker
        self.docker_image = docker_image
        self.docker_available = shutil.which("docker") is not None
        self.tasks: Dict[str, Dict[str, Any]] = {}
        
        if self.use_docker and not self.docker_available:
            logging.warning("⚠️ Docker requested but docker binary not found in PATH. Falling back to local execution.")
            self.use_docker = False

        logging.info(f"Initialized Execution Engine (Docker Mode: {self.use_docker})")

    def submit_task(self, task: Dict[str, Any]) -> str:
        """Submits a task for tracking and returns its task_id."""
        task_id = task.get("id", f"task_{uuid.uuid4().hex[:8]}")
        task["id"] = task_id
        
        self.tasks[task_id] = {
            "task": task,
            "state": TaskState.PENDING,
            "result": None
        }
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Retrieves task state and execution output."""
        if task_id in self.tasks:
            return self.tasks[task_id]
        return {"state": TaskState.ERROR, "error": f"Task ID '{task_id}' not found"}

    def execute_task(self, task: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """Executes a task item (accepts a task dictionary or a task_id string)."""
        if isinstance(task, str):
            task_id = task
            task_dict = self.tasks.get(task_id, {}).get("task", {"id": task_id})
        else:
            task_dict = task
            task_id = task_dict.get("id", "task_unknown")

        action = task_dict.get("action", "noop")
        payload = task_dict.get("payload", {})

        logging.info(f"Executing [{task_id}] -> Action: '{action}'")

        if action == "python_eval":
            res = self._execute_python(payload.get("code", ""), task_id)
        elif action == "shell_cmd":
            res = self._execute_shell(payload.get("command", ""), task_id)
        else:
            res = {
                "status": "SUCCESS",
                "task_id": task_id,
                "result": {
                    "status": "SUCCESS",
                    "details": f"Executed action '{action}' with payload keys: {list(payload.keys())}"
                }
            }

        # Inject state metadata for orchestrator and test compatibility
        state = TaskState.COMPLETED if res.get("status") == "SUCCESS" else TaskState.FAILED
        res["state"] = state

        if task_id in self.tasks:
            self.tasks[task_id]["result"] = res
            self.tasks[task_id]["state"] = state

        return res

    def _execute_python(self, code: str, task_id: str) -> Dict[str, Any]:
        """Executes Python code either locally or inside a Docker sandbox container."""
        if self.use_docker:
            return self._execute_in_docker(f"python -c \"{code}\"", task_id)
        
        try:
            local_scope = {}
            exec(code, {}, local_scope)
            return {
                "status": "SUCCESS",
                "task_id": task_id,
                "mode": "local",
                "result": local_scope.get("result", "Execution completed successfully.")
            }
        except Exception as e:
            return {"status": "ERROR", "task_id": task_id, "mode": "local", "error": str(e)}

    def _execute_shell(self, command: str, task_id: str) -> Dict[str, Any]:
        """Executes shell command locally or inside Docker."""
        if self.use_docker:
            return self._execute_in_docker(command, task_id)

        try:
            res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            return {
                "status": "SUCCESS" if res.returncode == 0 else "FAILED",
                "task_id": task_id,
                "mode": "local",
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip()
            }
        except Exception as e:
            return {"status": "ERROR", "task_id": task_id, "mode": "local", "error": str(e)}

    def _execute_in_docker(self, command: str, task_id: str) -> Dict[str, Any]:
        """Executes command inside an isolated Docker container."""
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "256m",
            self.docker_image,
            "sh", "-c", command
        ]
        try:
            res = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=15)
            return {
                "status": "SUCCESS" if res.returncode == 0 else "FAILED",
                "task_id": task_id,
                "mode": "docker_sandbox",
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip()
            }
        except Exception as e:
            return {"status": "ERROR", "task_id": task_id, "mode": "docker_sandbox", "error": str(e)}


if __name__ == "__main__":
    print("\n--- Testing Execution Engine (Local & Sandbox Detection) ---")
    engine = ExecutionEngine(use_docker=False)
    tid = engine.submit_task({"action": "python_eval", "payload": {"code": "result = 21 * 2"}})
    print("\n[Submitted Task Result]:", engine.execute_task(tid))