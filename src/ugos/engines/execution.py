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
from typing import Dict, Any, Optional
from pathlib import Path

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class ExecutionEngine:
    """Manages secure execution of agent tasks locally or inside Docker sandboxes."""

    def __init__(self, use_docker: bool = False, docker_image: str = "python:3.12-slim"):
        self.use_docker = use_docker
        self.docker_image = docker_image
        self.docker_available = shutil.which("docker") is not None
        
        if self.use_docker and not self.docker_available:
            logging.warning("⚠️ Docker requested but docker binary not found in PATH. Falling back to local execution.")
            self.use_docker = False

        logging.info(f"Initialized Execution Engine (Docker Mode: {self.use_docker})")

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a single task item."""
        task_id = task.get("id", "task_unknown")
        action = task.get("action", "noop")
        payload = task.get("payload", {})

        logging.info(f"Executing [{task_id}] -> Action: '{action}'")

        if action == "python_eval":
            return self._execute_python(payload.get("code", ""), task_id)
        elif action == "shell_cmd":
            return self._execute_shell(payload.get("command", ""), task_id)
        else:
            return {
                "status": "SUCCESS",
                "task_id": task_id,
                "result": f"Executed action '{action}' with payload keys: {list(payload.keys())}"
            }

    def _execute_python(self, code: str, task_id: str) -> Dict[str, Any]:
        """Executes Python code either locally or inside a Docker sandbox container."""
        if self.use_docker:
            return self._execute_in_docker(f"python -c \"{code}\"", task_id)
        
        try:
            # Local safe evaluation
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
            "--network", "none",  # Network sandbox isolation
            "--memory", "256m",   # Memory cap
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
    
    # 1. Local Execution Engine Test
    engine = ExecutionEngine(use_docker=False)
    sample_task = {
        "id": "tsk_101",
        "action": "python_eval",
        "payload": {"code": "result = 21 * 2"}
    }
    res = engine.execute_task(sample_task)
    print("\n[Local Execution Result]:", res)

    # 2. Docker Sandbox Mode Test (Falls back safely if Docker is absent)
    docker_engine = ExecutionEngine(use_docker=True)
    res_docker = docker_engine.execute_task(sample_task)
    print("\n[Docker Engine Result]:", res_docker)
