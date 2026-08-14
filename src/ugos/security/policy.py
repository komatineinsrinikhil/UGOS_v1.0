"""
UGOS_402: Security & Permission Policy Engine
---------------------------------------------
Enforces Zero-Trust access control, resource permission boundaries,
and security audit logging across all UGOS agent tasks.

Three checks run on every request, in order:

    1. Permission level  -- may this role perform this kind of action at all?
    2. Forbidden pattern -- is the target a secret or system file?
    3. Sandbox boundary  -- does the target sit inside an allowed root?

Check 3 is what stops an agent walking out of the project directory, or
rewriting this very file. UGOS_400/UGOS_402 require it ("Restricts filesystem
access to dedicated sandbox paths"); until now only checks 1 and 2 existed.
"""

from enum import Enum
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class PermissionLevel(Enum):
    READ_ONLY = "READ_ONLY"
    STANDARD_EXEC = "STANDARD_EXEC"
    ELEVATED = "ELEVATED"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"

class SecurityAction(Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EXECUTE_SHELL = "execute_shell"
    NETWORK_CALL = "network_call"
    MODIFY_SYSTEM = "modify_system"

FILE_ACTIONS = (SecurityAction.READ_FILE, SecurityAction.WRITE_FILE)

class PolicyEngine:
    """Zero-Trust Security & Permission Policy Enforcement Engine."""

    def __init__(
        self,
        default_profile: str = "STRICT",
        sandbox_roots: Optional[List[Union[str, Path]]] = None,
    ):
        self.default_profile = default_profile
        self.audit_log: List[Dict[str, Any]] = []

        # Directories file operations may touch. Anything outside is denied,
        # including paths reached via .. traversal, because targets are fully
        # resolved before comparison. Defaults to the current project folder.
        roots = sandbox_roots if sandbox_roots else [Path.cwd()]
        self.sandbox_roots: List[Path] = []
        for root in roots:
            try:
                self.sandbox_roots.append(Path(root).expanduser().resolve())
            except (OSError, ValueError):
                continue

        # Action permissions per role
        self.allowed_actions = {
            PermissionLevel.READ_ONLY: [SecurityAction.READ_FILE],
            PermissionLevel.STANDARD_EXEC: [
                SecurityAction.READ_FILE,
                SecurityAction.WRITE_FILE,
                SecurityAction.NETWORK_CALL
            ],
            PermissionLevel.ELEVATED: [
                SecurityAction.READ_FILE,
                SecurityAction.WRITE_FILE,
                SecurityAction.EXECUTE_SHELL,
                SecurityAction.NETWORK_CALL
            ],
            PermissionLevel.SYSTEM_ADMIN: list(SecurityAction)
        }

        # Forbidden path patterns (prevent reading secrets or system files)
        self.forbidden_path_patterns = [
            r"^/etc/.*",
            r"^C:\\Windows\\.*",
            r".*\.env$",
            r".*\.env\..*",
            r".*\.pem$",
            r".*\.key$",
            r".*id_rsa.*",
            r".*\.git[/\\]config$",
            r".*credentials.*",
        ]

        logging.info(
            f"Initialized UGOS Security Engine (Profile: {self.default_profile} | "
            f"Sandbox roots: {[str(r) for r in self.sandbox_roots]})"
        )

    def _within_sandbox(self, target: str) -> bool:
        """True if the fully resolved target lies inside an allowed root."""
        if not self.sandbox_roots:
            return True
        try:
            resolved = Path(target).expanduser().resolve()
        except (OSError, ValueError, RuntimeError):
            return False
        for root in self.sandbox_roots:
            try:
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def authorize_action(
        self,
        agent_id: str,
        permission_level: PermissionLevel,
        action: SecurityAction,
        target: Optional[str] = None
    ) -> bool:
        """Evaluates whether an agent action is permitted under Zero-Trust rules."""
        decision = "DENIED"
        reason = "Unknown"

        try:
            # Check 1: Action permission level
            if action not in self.allowed_actions.get(permission_level, []):
                reason = f"Permission level '{permission_level.value}' cannot perform action '{action.value}'."
                return False

            # Check 2: Target path inspection for file operations
            if target and action in FILE_ACTIONS:
                for pattern in self.forbidden_path_patterns:
                    if re.search(pattern, target, re.IGNORECASE):
                        reason = f"Target resource '{target}' matches forbidden pattern '{pattern}'."
                        return False

                # Check 3: Sandbox boundary
                if not self._within_sandbox(target):
                    roots = ", ".join(str(r) for r in self.sandbox_roots)
                    reason = f"Target '{target}' lies outside the permitted sandbox ({roots})."
                    return False

            decision = "ALLOWED"
            reason = "Action complies with Zero-Trust security rules."
            return True

        finally:
            log_entry = {
                "agent_id": agent_id,
                "permission_level": permission_level.value,
                "action": action.value,
                "target": target,
                "decision": decision,
                "reason": reason
            }
            self.audit_log.append(log_entry)
            if decision == "ALLOWED":
                logging.info(f"🔐 [SECURITY ALLOWED] Agent '{agent_id}' -> {action.value} ({target or 'N/A'})")
            else:
                logging.warning(f"🚨 [SECURITY DENIED] Agent '{agent_id}' -> {action.value} ({target or 'N/A'}) | Reason: {reason}")

    def last_decision(self) -> Optional[Dict[str, Any]]:
        """Most recent audit entry, for surfacing the reason to a caller."""
        return self.audit_log[-1] if self.audit_log else None

if __name__ == "__main__":
    security = PolicyEngine()

    print("\n--- Testing Security Engine Policy Checks ---")

    # Test 1: Standard read operation (Should ALLOW)
    security.authorize_action(
        "agent_01", PermissionLevel.READ_ONLY, SecurityAction.READ_FILE, "src/ugos/engines/execution.py"
    )

    # Test 2: READ_ONLY agent attempting shell execution (Should DENY)
    security.authorize_action(
        "agent_01", PermissionLevel.READ_ONLY, SecurityAction.EXECUTE_SHELL, "rm -rf /"
    )

    # Test 3: Agent attempting to read secret file `.env` (Should DENY)
    security.authorize_action(
        "agent_02", PermissionLevel.STANDARD_EXEC, SecurityAction.READ_FILE, ".env"
    )

    # Test 4: Agent attempting to escape the sandbox (Should DENY)
    security.authorize_action(
        "agent_03", PermissionLevel.STANDARD_EXEC, SecurityAction.READ_FILE, "../../../secrets.txt"
    )
