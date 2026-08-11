"""
UGOS_105: Orchestration Engine (DAG Workflow Coordinator)
---------------------------------------------------------
Executes multi-step task workflows respecting task dependencies (DAGs).
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ugos.engines.execution import ExecutionEngine, TaskState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class OrchestratorEngine:
    """DAG Workflow Orchestrator built on top of UGOS_100 Execution Engine."""

    def __init__(self):
        self.execution_engine = ExecutionEngine()
        logging.info("Initialized UGOS Orchestration Engine (DAG Coordinator)")

    def run_workflow(self, workflow_id: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Executes a list of DAG tasks respecting dependency ordering."""
        logging.info(f"Starting workflow '{workflow_id}' with {len(tasks)} tasks...")
        
        completed_tasks = set()
        failed_tasks = set()
        task_map = {t["id"]: t for t in tasks}
        results = {}

        # DAG evaluation loop
        while len(completed_tasks) + len(failed_tasks) < len(tasks):
            progress_made = False

            for task_id, task in task_map.items():
                if task_id in completed_tasks or task_id in failed_tasks:
                    continue

                deps = task.get("depends_on", [])
                # Check if all dependencies are satisfied
                if all(dep in completed_tasks for dep in deps):
                    logging.info(f"[DAG] Dependencies met for '{task_id}'. Executing...")
                    
                    engine_task_id = self.execution_engine.submit_task(task["payload"])
                    res = self.execution_engine.execute_task(engine_task_id)
                    
                    if res["state"] == TaskState.COMPLETED:
                        completed_tasks.add(task_id)
                        results[task_id] = res["result"]
                    else:
                        failed_tasks.add(task_id)
                        results[task_id] = {"status": "FAILED", "error": res["error"]}
                        
                    progress_made = True

            if not progress_made and len(completed_tasks) + len(failed_tasks) < len(tasks):
                raise RuntimeError("Circular dependency detected or unresolvable task dependencies in DAG!")

        status = "SUCCESS" if not failed_tasks else "PARTIAL_FAILURE"
        return {
            "workflow_id": workflow_id,
            "status": status,
            "completed": list(completed_tasks),
            "failed": list(failed_tasks),
            "results": results
        }

if __name__ == "__main__":
    orchestrator = OrchestratorEngine()
    
    # Define a 3-stage DAG workflow pipeline
    sample_dag = [
        {"id": "step_1_fetch", "payload": {"action": "fetch_spec", "target": "auth.md"}},
        {"id": "step_2_parse", "depends_on": ["step_1_fetch"], "payload": {"action": "parse_schema"}},
        {"id": "step_3_build", "depends_on": ["step_2_parse"], "payload": {"action": "compile_module"}}
    ]
    
    out = orchestrator.run_workflow("wf_pipeline_001", sample_dag)
    print("\n--- DAG Workflow Execution Summary ---")
    print(out)