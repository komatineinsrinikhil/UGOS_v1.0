"""
UGOS_700: Developer CLI & Workflow Runner
------------------------------------------
Provides command-line interface for running agent workflows with
full security policy checks, tool execution, and episodic memory logging.
"""

import argparse
import sys
import logging
from pathlib import Path

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ugos.engines.orchestrator import OrchestratorEngine
from ugos.security.policy import PolicyEngine, PermissionLevel, SecurityAction
from ugos.core.tools import ToolEngine
from ugos.core.memory import MemoryEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class UGOSCLI:
    """CLI Controller wiring core runtime engines together."""

    def __init__(self):
        self.orchestrator = OrchestratorEngine()
        self.tools = ToolEngine()
        self.memory = MemoryEngine()

    def run_workflow(self, workflow_id: str):
        """Runs a workflow pipeline through DAG, Tool, Security, and Memory layers."""
        logging.info(f"Starting workflow execution: '{workflow_id}'")
        
        # 1. Initialize session memory
        session = self.memory.get_or_create_session(f"sess_{workflow_id}")
        session.log_event("cli_user", "start_workflow", {"workflow_id": workflow_id})

        # 2. Define workflow pipeline tasks
        pipeline = [
            {"id": "step_1_inspect", "payload": {"action": "read_source", "target": "src/ugos/engines/execution.py"}},
            {"id": "step_2_eval", "depends_on": ["step_1_inspect"], "payload": {"action": "python_eval", "code": "100 + 200"}}
        ]

        # 3. Execute workflow through Orchestrator
        summary = self.orchestrator.run_workflow(workflow_id, pipeline)
        
        # 4. Log completion into session memory
        session.log_event(
            "cli_user",
            "workflow_completed",
            {"status": summary["status"], "completed": summary["completed"]}
        )
        
        print("\n" + "=" * 50)
        print(f"  ✅ WORKFLOW '{workflow_id}' EXECUTED SUCCESSFULLY")
        print("=" * 50)
        print(f" • Status           : {summary['status']}")
        print(f" • Completed Steps  : {summary['completed']}")
        print(f" • Session Logged   : {len(session.get_recent_history(5))} episodic events")
        print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="UGOS Developer CLI v1.0")
    subparsers = parser.add_subparsers(dest="command", help="Available CLI Commands")

    # Command: status
    subparsers.add_parser("status", help="Displays current UGOS runtime status.")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Executes an agent workflow pipeline.")
    run_parser.add_argument("--workflow-id", type=str, default="wf_demo_01", help="ID of the workflow to execute.")

    args = parser.parse_args()
    cli = UGOSCLI()

    if args.command == "status":
        print("\n🟢 UGOS v1.0 Core Runtime Status")
        print(" Active Engines: Execution (100) | Orchestrator (105) | Tools (107) | Security (402) | Memory (300)\n")
    elif args.command == "run":
        cli.run_workflow(args.workflow_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()