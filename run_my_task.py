"""
UGOS Application Script: Custom Automation Workflow
--------------------------------------------------
Demonstrates applying UGOS for zero-trust security checks,
sandboxed execution, DAG pipeline scheduling, and persistent SQLite memory.
"""

import sys
import logging
from pathlib import Path

# Fix ModuleNotFoundError: Add src directory to Python path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import Core UGOS Engines
from ugos.core.memory import MemoryEngine
from ugos.security.policy import PolicyEngine
from ugos.engines.execution import ExecutionEngine
from ugos.engines.orchestrator import OrchestratorEngine
from ugos.agents.specialized import SoftwareEngineerAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    print("\n" + "=" * 60)
    print("🛠️  Applying UGOS: Custom Automation Workflow")
    print("=" * 60)

    # 1. Initialize Local Persistent Memory
    memory = MemoryEngine(db_path=Path("ugos_memory.db"))
    memory.set_global_fact("project_name", "UGOS Custom Pipeline", tags=["metadata"])
    logging.info(f"Memory active. Facts stored: {len(memory.get_facts_by_tag('metadata'))}")

    # 2. Setup Zero-Trust Security & Execution Sandbox
    security = PolicyEngine()
    execution = ExecutionEngine(use_docker=False)
    orchestrator = OrchestratorEngine()
    orchestrator.execution_engine = execution

    # 3. Assign a Specialized Agent
    agent = SoftwareEngineerAgent(agent_id="dev_01", name="DevBot")
    logging.info(f"Agent assigned: {agent.name} ({agent.agent_id})")

    # 4. Define a Dependency-Driven DAG Pipeline
    pipeline = [
        {
            "id": "task_data_prep",
            "payload": {
                "action": "python_eval",
                "payload": {"code": "result = [10, 20, 30, 40, 50]"}
            }
        },
        {
            "id": "task_compute_avg",
            "depends_on": ["task_data_prep"],
            "payload": {
                "action": "python_eval",
                "payload": {"code": "result = sum([10, 20, 30, 40, 50]) / 5"}
            }
        }
    ]

    # 5. Execute Workflow via DAG Orchestrator
    summary = orchestrator.run_workflow(workflow_id="custom_analytics_job", tasks=pipeline)

    print("\n" + "=" * 60)
    print("📊 Execution Summary:")
    print(f"   - Workflow: {summary.get('workflow_id')}")
    print(f"   - Completed Tasks: {len(summary.get('completed', []))}")
    print(f"   - Failed Tasks:    {len(summary.get('failed', []))}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()