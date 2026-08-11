"""
UGOS_200 / UGOS_201: Base Agent Architecture
---------------------------------------------
Standard worker node implementation governing agent lifecycle, prompt handling,
and security-gated action execution.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ugos.security.policy import PolicyEngine, PermissionLevel, SecurityAction

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class BaseAgent:
    """Foundational Autonomous Agent implementation derived from UGOS_200 spec."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        permission_level: PermissionLevel = PermissionLevel.STANDARD_EXEC
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.permission_level = permission_level
        self.security_engine = PolicyEngine()
        
        logging.info(f"Initialized Agent '{self.name}' ({self.agent_id}) [Role: {self.role} | Perms: {self.permission_level.value}]")

    def evaluate_and_act(self, action: SecurityAction, target: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evaluates action against Zero-Trust policy before executing."""
        logging.info(f"Agent '{self.name}' requesting action: {action.value} on '{target or 'N/A'}'")
        
        is_allowed = self.security_engine.authorize_action(
            agent_id=self.agent_id,
            permission_level=self.permission_level,
            action=action,
            target=target
        )

        if not is_allowed:
            return {
                "status": "BLOCKED_BY_SECURITY",
                "agent_id": self.agent_id,
                "action": action.value,
                "target": target,
                "reason": "Action violated Zero-Trust policy rules."
            }

        # Simulated action execution
        return {
            "status": "SUCCESS",
            "agent_id": self.agent_id,
            "action": action.value,
            "target": target,
            "result": f"Agent '{self.name}' executed '{action.value}' successfully."
        }

if __name__ == "__main__":
    print("\n--- Testing Base Agent Architecture ---")
    
    # Create a Software Engineer Agent with standard execution permissions
    dev_agent = BaseAgent(
        agent_id="ag_dev_01",
        name="CoderBot",
        role="Software Engineer",
        permission_level=PermissionLevel.STANDARD_EXEC
    )

    # Test 1: Valid write action (Should SUCCEED)
    res1 = dev_agent.evaluate_and_act(
        action=SecurityAction.WRITE_FILE,
        target="src/ugos/engines/execution.py"
    )
    print("\nResult 1:", res1)

    # Test 2: Shell execution request (Should be BLOCKED because STANDARD_EXEC cannot run shell)
    res2 = dev_agent.evaluate_and_act(
        action=SecurityAction.EXECUTE_SHELL,
        target="system_command"
    )
    print("\nResult 2:", res2)
