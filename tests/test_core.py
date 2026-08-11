"""
UGOS System-Wide Automated Test Suite
--------------------------------------
Verifies core execution, DAG orchestration, security policy enforcement,
agent behavior, and tool capabilities.
"""

import sys
import pytest
from pathlib import Path

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ugos.engines.execution import ExecutionEngine, TaskState
from ugos.engines.orchestrator import OrchestratorEngine
from ugos.security.policy import PolicyEngine, PermissionLevel, SecurityAction
from ugos.agents.base import BaseAgent
from ugos.core.tools import ToolEngine


# --- 1. Execution Engine Tests ---
def test_execution_engine_single_task():
    engine = ExecutionEngine()
    task_id = engine.submit_task({"action": "test_ping"})
    res = engine.execute_task(task_id)
    assert res["state"] == TaskState.COMPLETED
    assert res["result"]["status"] == "SUCCESS"


# --- 2. DAG Orchestrator Tests ---
def test_orchestrator_dag_pipeline():
    orchestrator = OrchestratorEngine()
    pipeline = [
        {"id": "step_a", "payload": {"action": "fetch"}},
        {"id": "step_b", "depends_on": ["step_a"], "payload": {"action": "process"}}
    ]
    summary = orchestrator.run_workflow("test_wf", pipeline)
    assert summary["status"] == "SUCCESS"
    assert len(summary["completed"]) == 2
    assert "step_b" in summary["completed"]


# --- 3. Security Policy Engine Tests ---
def test_security_policy_enforcement():
    policy = PolicyEngine(default_profile="STRICT")

    # Read action allowed for READ_ONLY
    assert policy.authorize_action("agent_01", PermissionLevel.READ_ONLY, SecurityAction.READ_FILE, "src/ugos/engines/execution.py") is True

    # Shell execution denied for READ_ONLY
    assert policy.authorize_action("agent_01", PermissionLevel.READ_ONLY, SecurityAction.EXECUTE_SHELL) is False

    # Forbidden path pattern (.env) blocked
    assert policy.authorize_action("agent_01", PermissionLevel.ELEVATED, SecurityAction.READ_FILE, ".env") is False


# --- 4. Base Agent Architecture Tests ---
def test_base_agent_security_integration():
    dev_agent = BaseAgent(
        agent_id="ag_test_01",
        name="TestDev",
        role="Developer",
        permission_level=PermissionLevel.STANDARD_EXEC
    )

    # File write should succeed under STANDARD_EXEC
    res1 = dev_agent.evaluate_and_act(SecurityAction.WRITE_FILE, target="src/ugos/engines/execution.py")
    assert res1["status"] == "SUCCESS"

    # Shell execution should be blocked under STANDARD_EXEC
    res2 = dev_agent.evaluate_and_act(SecurityAction.EXECUTE_SHELL, target="bash")
    assert res2["status"] == "BLOCKED_BY_SECURITY"


# --- 5. Tool Engine Tests ---
def test_tool_engine_execution():
    tools = ToolEngine()

    # File reader tool with standard permissions
    res1 = tools.execute_tool(
        tool_name="file_reader",
        agent_id="ag_test_02",
        permission_level=PermissionLevel.STANDARD_EXEC,
        target="src/ugos/engines/execution.py"
    )
    assert res1["status"] == "SUCCESS"

    # Python eval tool blocked under STANDARD_EXEC
    res2 = tools.execute_tool(
        tool_name="python_eval",
        agent_id="ag_test_02",
        permission_level=PermissionLevel.STANDARD_EXEC,
        code="1 + 1"
    )
    assert res2["status"] == "DENIED"

    # Python eval tool allowed under ELEVATED
    res3 = tools.execute_tool(
        tool_name="python_eval",
        agent_id="ag_admin_02",
        permission_level=PermissionLevel.ELEVATED,
        code="2 * 3"
    )
    assert res3["status"] == "SUCCESS"
    assert "Evaluated result: 6" in res3["output"]




from ugos.core.memory import MemoryEngine

# --- 6. Memory Architecture Tests ---
def test_memory_engine_episodic_and_semantic():
    memory = MemoryEngine()
    
    # Test Episodic Session Logging
    session = memory.get_or_create_session("test_sess_01")
    session.log_event("agent_test", "action_1", {"status": "ok"})
    history = session.get_recent_history(limit=1)
    assert len(history) == 1
    assert history[0]["action"] == "action_1"

    # Test Semantic Tagged Context Retrieval
    memory.global_semantic.set_fact("db_port", 5432, tags=["database", "config"])
    facts = memory.global_semantic.search_by_tag("database")
    assert facts.get("db_port") == 5432



from ugos.agents.specialized import SoftwareEngineerAgent, SecurityAuditAgent

# --- 7. Specialized Agent Tests ---
def test_specialized_agents_permissions():
    tools = ToolEngine()
    swe = SoftwareEngineerAgent(agent_id="ag_test_swe")
    sec = SecurityAuditAgent(agent_id="ag_test_sec")

    # SWE agent reads file -> SUCCESS
    res_swe = swe.inspect_code(tools, "src/ugos/engines/execution.py")
    assert res_swe["status"] == "SUCCESS"

    # Security agent performs elevated eval -> SUCCESS
    res_sec = sec.audit_expression(tools, "10 * 10")
    assert res_sec["status"] == "SUCCESS"
    assert "100" in res_sec["output"]


# --- 8. Tool Engine File Writer & Diff Tests ---
def test_tool_engine_file_writer_diff():
    tools = ToolEngine()
    target_file = "test_diff_sample.py"
    
    # Write version 1
    res1 = tools.execute_tool(
        tool_name="file_writer",
        agent_id="ag_test_writer",
        permission_level=PermissionLevel.STANDARD_EXEC,
        target=target_file,
        content="x = 10\n"
    )
    assert res1["status"] == "SUCCESS"
    assert "diff" in res1
    assert "+x = 10" in res1["diff"]

    # Write version 2 (Generates modification diff)
    res2 = tools.execute_tool(
        tool_name="file_writer",
        agent_id="ag_test_writer",
        permission_level=PermissionLevel.STANDARD_EXEC,
        target=target_file,
        content="x = 20\ny = 30\n"
    )
    assert res2["status"] == "SUCCESS"
    assert "-x = 10" in res2["diff"]
    assert "+x = 20" in res2["diff"]

    # Clean up file
    if Path(target_file).exists():
        Path(target_file).unlink()