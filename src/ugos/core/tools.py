"""
UGOS_107: Tool Execution Engine
-------------------------------
Provides tool registration, input validation, and security-gated
execution of agent capabilities.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ugos.security.policy import PolicyEngine, PermissionLevel, SecurityAction

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class ToolEngine:
    """Registry and sandboxed executor for agent tools."""

    def __init__(self):
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.security_engine = PolicyEngine()
        self._register_default_tools()
        logging.info("Initialized UGOS Tool Execution Engine")

    def _register_default_tools(self):
        """Registers core built-in system tools."""
        
        # Tool: File Reader
        self.register_tool(
            name="file_reader",
            description="Reads text from a target file path.",
            action_type=SecurityAction.READ_FILE,
            handler=self._tool_read_file
        )

        # Tool: Code Executor (Python)
        self.register_tool(
            name="python_eval",
            description="Executes a Python snippet inside a controlled scope.",
            action_type=SecurityAction.EXECUTE_SHELL,
            handler=self._tool_python_eval
        )

    def register_tool(self, name: str, description: str, action_type: SecurityAction, handler: Callable):
        """Registers a new tool into the Tool Engine registry."""
        self.registry[name] = {
            "name": name,
            "description": description,
            "action_type": action_type,
            "handler": handler
        }
        logging.info(f"Tool registered: '{name}' (Action: {action_type.value})")

    def execute_tool(
        self,
        tool_name: str,
        agent_id: str,
        permission_level: PermissionLevel,
        target: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Validates tool permissions and executes handler if authorized."""
        
        if tool_name not in self.registry:
            return {
                "status": "ERROR",
                "reason": f"Tool '{tool_name}' is not registered in Tool Engine."
            }

        tool = self.registry[tool_name]
        
        # Zero-Trust Security Gate
        is_allowed = self.security_engine.authorize_action(
            agent_id=agent_id,
            permission_level=permission_level,
            action=tool["action_type"],
            target=target
        )

        if not is_allowed:
            return {
                "status": "BLOCKED_BY_SECURITY",
                "tool_name": tool_name,
                "reason": f"Execution of tool '{tool_name}' violated security policy."
            }

        # Execute registered tool handler
        try:
            result = tool["handler"](target=target, **kwargs)
            return {
                "status": "SUCCESS",
                "tool_name": tool_name,
                "output": result
            }
        except Exception as e:
            return {
                "status": "EXECUTION_ERROR",
                "tool_name": tool_name,
                "error": str(e)
            }

    # Default Tool Handlers
    @staticmethod
    def _tool_read_file(target: Optional[str] = None, **kwargs) -> str:
        if not target:
            raise ValueError("Target file path is required.")
        path = Path(target)
        if not path.exists():
            return f"File not found: {target}"
        return path.read_text(encoding="utf-8")[:500]  # Return preview

    @staticmethod
    def _tool_python_eval(code: str = "", **kwargs) -> str:
        # Evaluates simple math/expressions safely
        result = eval(code, {"__builtins__": {}})
        return f"Evaluated result: {result}"

if __name__ == "__main__":
    tools = ToolEngine()
    
    print("\n--- Testing Tool Execution Engine ---")

    # Test 1: Standard agent reading execution.py via file_reader tool (Should SUCCEED)
    res1 = tools.execute_tool(
        tool_name="file_reader",
        agent_id="ag_dev_01",
        permission_level=PermissionLevel.STANDARD_EXEC,
        target="src/ugos/engines/execution.py"
    )
    print("\nResult 1 (Read File):", res1["status"])

    # Test 2: Standard agent calling python_eval tool (Requires EXECUTE_SHELL -> Should DENY)
    res2 = tools.execute_tool(
        tool_name="python_eval",
        agent_id="ag_dev_01",
        permission_level=PermissionLevel.STANDARD_EXEC,
        code="2 + 2"
    )
    print("\nResult 2 (Python Eval - Standard Perms):", res2)

    # Test 3: Elevated agent calling python_eval tool (Should ALLOW & SUCCEED)
    res3 = tools.execute_tool(
        tool_name="python_eval",
        agent_id="ag_admin_01",
        permission_level=PermissionLevel.ELEVATED,
        code="10 * 5"
    )
    print("\nResult 3 (Python Eval - Elevated Perms):", res3)