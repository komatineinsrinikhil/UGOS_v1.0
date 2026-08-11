"""
UGOS_107: Tool Execution Engine & Capability Registry
-----------------------------------------------------
Manages sandboxed tool registration, permission checking via PolicyEngine,
and safe execution for file reading, file writing with unified diff generation,
and expression/code evaluation.
"""

import sys
import logging
import difflib
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ugos.security.policy import PolicyEngine, PermissionLevel, SecurityAction

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class ToolEngine:
    """UGOS Sandboxed Tool Execution Router with Patch/Diff capabilities."""

    def __init__(self, security_policy: Optional[PolicyEngine] = None):
        self.policy = security_policy or PolicyEngine()
        self.registry: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()
        logging.info("Initialized UGOS Tool Execution Engine")

    def _register_default_tools(self):
        """Registers system core capabilities into tool registry."""
        self.registry["file_reader"] = {
            "action": SecurityAction.READ_FILE,
            "handler": self._handle_file_reader
        }
        self.registry["file_writer"] = {
            "action": SecurityAction.WRITE_FILE,
            "handler": self._handle_file_writer
        }
        self.registry["python_eval"] = {
            "action": SecurityAction.EXECUTE_SHELL,
            "handler": self._handle_python_eval
        }
        logging.info("Tools registered: 'file_reader', 'file_writer', 'python_eval'")

    def _handle_file_reader(self, target: str) -> Dict[str, Any]:
        """Reads content from target file path."""
        path = Path(target)
        if not path.exists():
            return {"status": "ERROR", "reason": f"File '{target}' does not exist."}
        try:
            content = path.read_text(encoding="utf-8")
            return {"status": "SUCCESS", "output": content}
        except Exception as e:
            return {"status": "ERROR", "reason": str(e)}

    def _handle_file_writer(self, target: str, content: str) -> Dict[str, Any]:
        """Writes/updates content in target path and generates unified diff patch."""
        path = Path(target)
        old_content = ""
        if path.exists():
            try:
                old_content = path.read_text(encoding="utf-8")
            except Exception:
                old_content = ""

        # Generate Unified Patch Diff
        old_lines = old_content.splitlines(keepends=True)
        new_lines = content.splitlines(keepends=True)
        diff = "".join(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{target}",
            tofile=f"b/{target}"
        ))

        try:
            # Ensure parent directories exist
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {
                "status": "SUCCESS",
                "output": f"Successfully wrote {len(content)} characters to '{target}'.",
                "diff": diff if diff else "No changes detected."
            }
        except Exception as e:
            return {"status": "ERROR", "reason": str(e)}

    def _handle_python_eval(self, code: str) -> Dict[str, Any]:
        """Evaluates python mathematical or algorithmic expressions."""
        try:
            result = eval(code, {"__builtins__": {}}, {})
            return {"status": "SUCCESS", "output": f"Evaluated result: {result}"}
        except Exception as e:
            return {"status": "ERROR", "reason": f"Eval failure: {str(e)}"}

    def execute_tool(
        self,
        tool_name: str,
        agent_id: str,
        permission_level: PermissionLevel,
        **kwargs
    ) -> Dict[str, Any]:
        """Validates tool permissions through PolicyEngine before execution dispatch."""
        if tool_name not in self.registry:
            return {"status": "DENIED", "reason": f"Tool '{tool_name}' not registered."}

        tool_meta = self.registry[tool_name]
        required_action = tool_meta["action"]
        target = kwargs.get("target")

        # 1. Zero-Trust Security Policy Gate
        authorized = self.policy.authorize_action(
            agent_id=agent_id,
            permission_level=permission_level,
            action=required_action,
            target=target
        )

        if not authorized:
            return {
                "status": "DENIED",
                "reason": f"Action '{required_action.value}' not authorized for agent '{agent_id}' under permission level {permission_level.value}."
            }

        # 2. Handler Execution Dispatch
        handler = tool_meta["handler"]
        if tool_name == "file_reader":
            return handler(target=kwargs.get("target", ""))
        elif tool_name == "file_writer":
            return handler(target=kwargs.get("target", ""), content=kwargs.get("content", ""))
        elif tool_name == "python_eval":
            return handler(code=kwargs.get("code", ""))

        return {"status": "ERROR", "reason": "Unknown execution routing."}


if __name__ == "__main__":
    print("\n--- Testing ToolEngine with File Writer & Patch Generator ---")
    tools = ToolEngine()
    
    test_file = "sandbox_test.py"
    v1_code = "print('Hello UGOS v1.0')\n"
    v2_code = "print('Hello UGOS v1.0 Engine')\n# Added patch line\n"

    # Test 1: Write initial version
    res1 = tools.execute_tool(
        tool_name="file_writer",
        agent_id="ag_dev_01",
        permission_level=PermissionLevel.STANDARD_EXEC,
        target=test_file,
        content=v1_code
    )
    print("\n[Write V1 Status]:", res1["status"])
    print("[V1 Diff Patch]:\n" + res1.get("diff", ""))

    # Test 2: Modify version and generate patch diff
    res2 = tools.execute_tool(
        tool_name="file_writer",
        agent_id="ag_dev_01",
        permission_level=PermissionLevel.STANDARD_EXEC,
        target=test_file,
        content=v2_code
    )
    print("[Write V2 Status]:", res2["status"])
    print("[V2 Unified Patch Diff]:\n" + res2.get("diff", ""))

    # Clean up temporary test file
    if Path(test_file).exists():
        Path(test_file).unlink()
        print("Cleaned up temporary test file 'sandbox_test.py'.\n")
