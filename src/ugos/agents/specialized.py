"""
UGOS_201 / UGOS_202: Specialized Agent Subclasses
--------------------------------------------------
Extends BaseAgent with role-specific capabilities, default permission profiles,
and tool interactions for engineering and security auditing tasks.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ugos.agents.base import BaseAgent
from ugos.security.policy import PermissionLevel, SecurityAction
from ugos.core.tools import ToolEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SoftwareEngineerAgent(BaseAgent):
    """UGOS_201: Specialized agent for software development, code reading, and testing."""

    def __init__(self, agent_id: str = "ag_swe_01", name: str = "DevEngine"):
        super().__init__(
            agent_id=agent_id,
            name=name,
            role="Software Engineer",
            permission_level=PermissionLevel.STANDARD_EXEC
        )
        logging.info(f"Initialized {self.role} Agent '{self.name}' ({self.permission_level.value})")

    def inspect_code(self, tool_engine: ToolEngine, file_path: str) -> Dict[str, Any]:
        """Reads code files through the tool execution engine."""
        return tool_engine.execute_tool(
            tool_name="file_reader",
            agent_id=self.agent_id,
            permission_level=self.permission_level,
            target=file_path
        )


class SecurityAuditAgent(BaseAgent):
    """UGOS_202: Specialized agent for security policy reviews and vulnerability scans."""

    def __init__(self, agent_id: str = "ag_sec_01", name: str = "SecGuard"):
        super().__init__(
            agent_id=agent_id,
            name=name,
            role="Security Auditor",
            permission_level=PermissionLevel.ELEVATED
        )
        logging.info(f"Initialized {self.role} Agent '{self.name}' ({self.permission_level.value})")

    def audit_expression(self, tool_engine: ToolEngine, expression: str) -> Dict[str, Any]:
        """Evaluates expressions safely under elevated permission controls."""
        return tool_engine.execute_tool(
            tool_name="python_eval",
            agent_id=self.agent_id,
            permission_level=self.permission_level,
            code=expression
        )


if __name__ == "__main__":
    tools = ToolEngine()
    print("\n--- Testing Specialized Domain Agents ---")

    # Instantiate specialized agents
    swe_agent = SoftwareEngineerAgent()
    sec_agent = SecurityAuditAgent()

    # SWE Agent reads file (Should succeed under STANDARD_EXEC)
    res_swe = swe_agent.inspect_code(tools, "src/ugos/engines/execution.py")
    print("\nSWE Agent Code Inspection:", res_swe["status"])

    # Sec Agent evaluates expression (Should succeed under ELEVATED)
    res_sec = sec_agent.audit_expression(tools, "100 * 5")
    print("Security Agent Audit Eval:", res_sec["status"], "| Result:", res_sec.get("output"))
