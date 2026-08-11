"""
UGOS_700: Developer CLI Interface
---------------------------------
Command-line entry point to trigger workflows, monitor execution tasks, and inspect state.
"""

import sys
import argparse
import logging
from pathlib import Path

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ugos.engines.execution import ExecutionEngine
from ugos.engines.orchestrator import OrchestratorEngine

def main():
    parser = argparse.ArgumentParser(
        prog="ugos",
        description="UGOS Autonomous Agent OS Developer CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: status
    parser_status = subparsers.add_parser("status", help="Show UGOS kernel status and active sandbox level")

    # Command: run
    parser_run = subparsers.add_parser("run", help="Execute a workflow or task")
    parser_run.add_argument("--workflow-id", type=str, default="wf_demo_001", help="ID of the workflow to run")

    args = parser.parse_args()

    if args.command == "status":
        engine = ExecutionEngine()
        print("\n=================================================")
        print("🤖 UGOS AGENT OPERATING SYSTEM - STATUS REPORT")
        print("=================================================")
        print(f"  • Kernel Version   : v1.0.0-alpha")
        print(f"  • Sandbox Profile  : {engine.sandbox_level}")
        print(f"  • Engine Core      : UGOS_100 Execution Engine (ACTIVE)")
        print(f"  • Orchestrator     : UGOS_105 DAG Coordinator (ACTIVE)")
        print("=================================================\n")

    elif args.command == "run":
        orchestrator = OrchestratorEngine()
        
        # Sample DAG pipeline
        pipeline = [
            {"id": "step_1_inspect", "payload": {"action": "scan_vulnerabilities", "target": "auth.py"}},
            {"id": "step_2_patch", "depends_on": ["step_1_inspect"], "payload": {"action": "apply_patch"}},
            {"id": "step_3_verify", "depends_on": ["step_2_patch"], "payload": {"action": "run_pytest"}}
        ]
        
        result = orchestrator.run_workflow(args.workflow_id, pipeline)
        print("\n=================================================")
        print(f"🚀 WORKFLOW EXECUTION COMPLETE: {result['workflow_id']}")
        print(f"  • Status          : {result['status']}")
        print(f"  • Tasks Completed : {len(result['completed'])}")
        print(f"  • Tasks Failed    : {len(result['failed'])}")
        print("=================================================\n")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()