"""
UGOS_000: Unified System Entry Point & CLI Driver
--------------------------------------------------
Integrates all UGOS core engines: Orchestration, Zero-Trust Security,
Specialized Agents, Sandboxed Tools, SQLite Memory, and LLM Router.
"""

import sys
import logging
import argparse
from pathlib import Path

# Ensure project root is in Python path
current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent
project_root = src_dir.parent

for p in [str(src_dir), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Core Engines & Security Imports
from ugos.engines.orchestrator import OrchestratorEngine
from ugos.engines.execution import ExecutionEngine
from ugos.core.memory import MemoryEngine
from ugos.llm.router import LLMRouter, SimulatedAPIProvider, MockLLMProvider
from ugos.security.policy import PolicyEngine as SecurityPolicyEngine
from ugos.agents.specialized import SoftwareEngineerAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="UGOS v1.0 Unified Agent Operating System")
    parser.add_argument("--workflow", type=str, default="demo_workflow_01", help="Workflow ID to execute")
    parser.add_argument("--use-docker", action="store_true", help="Enable Docker sandbox execution")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("🚀 Launching UGOS v1.0 Unified Agent Operating System")
    print("=" * 65)

    # 1. Initialize Memory Engine
    memory = MemoryEngine(db_path=Path("ugos_memory.db"))
    memory.set_global_fact("system_version", "v1.0.0", tags=["config"])
    logging.info(f"Memory Engine loaded. Global facts count: {len(memory.get_facts_by_tag('config'))}")

    # 2. Initialize LLM Provider Router
    llm_router = LLMRouter(
        primary_provider=SimulatedAPIProvider(model_id="gpt-4o", should_fail=False),
        fallback_providers=[MockLLMProvider()]
    )
    llm_response = llm_router.generate("Analyze system security policies")
    logging.info(f"LLM Router active | Provider: {llm_response['provider']}")

    # 3. Initialize Security & Execution Engines
    security = SecurityPolicyEngine()
    execution = ExecutionEngine(use_docker=args.use_docker)
    orchestrator = OrchestratorEngine()
    orchestrator.execution_engine = execution

    # 4. Instantiate Specialized Agent
    agent = SoftwareEngineerAgent(agent_id="swe_agent_01", name="DevEngine")
    if hasattr(agent, "security_engine"):
        agent.security_engine = security
    elif hasattr(agent, "security_policy"):
        agent.security_policy = security

    logging.info(f"Agent '{agent.agent_id}' ({agent.name}) initialized successfully.")

    # 5. Build Sample DAG Pipeline
    dag_pipeline = [
        {"id": "task_mem_check", "payload": {"action": "python_eval", "payload": {"code": "result = 'UGOS SQLite Memory Active'"}}},
        {"id": "task_compute", "depends_on": ["task_mem_check"], "payload": {"action": "python_eval", "payload": {"code": "result = 21 * 2"}}}
    ]

    # 6. Run Workflow via Orchestrator
    summary = orchestrator.run_workflow(workflow_id=args.workflow, tasks=dag_pipeline)

    print("\n" + "=" * 65)
    print("📊 UGOS Workflow Execution Summary:")
    print(f"   - Workflow ID: {summary.get('workflow_id')}")
    print(f"   - Total Tasks: {summary.get('total_tasks')}")
    print(f"   - Completed:   {len(summary.get('completed', []))}")
    print(f"   - Failed:      {len(summary.get('failed', []))}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()