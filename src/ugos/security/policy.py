"""
UGOS_402: Security & Permission Policy Engine
---------------------------------------------
Enforces Zero-Trust access control, resource permission boundaries,
and security audit logging across all UGOS agent tasks.

PRIVILEGE LEVELS (UGOS_400 section 2, UGOS_402)
-----------------------------------------------
Six levels, L0 through L5, as specified:

    L0  Untrusted / Public   Read-only access to public, unclassified data.
    L1  Standard Agent       Read-write working memory; basic tool execution.
    L2  Sandboxed Dev        Code compilation, unit tests, static analysis.
    L3  System Integrator    Multi-agent delegation, API routing, DB queries.
                             Gated by DELEGATE_TASK, ROUTE_API, QUERY_DATABASE.
    L4  Guarded Admin        Security patching, temporary policy overrides.
    L5  Root Kernel          Kernel manipulation, key rotation, spec updates.

The implementation previously had four ad-hoc levels. The old names are kept
as aliases so existing code and tests continue to work:

    READ_ONLY -> L0    STANDARD_EXEC -> L1    ELEVATED -> L2    SYSTEM_ADMIN -> L5

ENFORCEMENT
-----------
Every request passes four checks, in order:

    1. Elevation gate  -- L4 and L5 require explicit approval (UGOS_402 s.3).
    2. Permission level -- may this level perform this kind of action at all?
    3. Forbidden pattern -- is the target a secret or system file?
    4. Sandbox boundary  -- does the resolved target sit inside an allowed root?

Check 4 is what stops an agent escaping the project folder or rewriting this
file. Evaluation is FAIL-CLOSED: an exception during evaluation denies the
request rather than letting it through (UGOS_400).
"""

from enum import Enum
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class PermissionLevel(Enum):
    """Six privilege levels per UGOS_400/UGOS_402, with legacy aliases."""

    L0_UNTRUSTED = "L0_UNTRUSTED"
    L1_STANDARD = "L1_STANDARD"
    L2_SANDBOXED = "L2_SANDBOXED"
    L3_INTEGRATOR = "L3_INTEGRATOR"
    L4_GUARDED = "L4_GUARDED"
    L5_ROOT = "L5_ROOT"

    # Legacy names from the pre-spec implementation. Same value == same member.
    READ_ONLY = "L0_UNTRUSTED"
    STANDARD_EXEC = "L1_STANDARD"
    ELEVATED = "L2_SANDBOXED"
    SYSTEM_ADMIN = "L5_ROOT"

    @classmethod
    def _missing_(cls, value):
        """Accept the old string values, e.g. PermissionLevel('STANDARD_EXEC')."""
        legacy = {
            "READ_ONLY": cls.L0_UNTRUSTED,
            "STANDARD_EXEC": cls.L1_STANDARD,
            "ELEVATED": cls.L2_SANDBOXED,
            "SYSTEM_ADMIN": cls.L5_ROOT,
        }
        if isinstance(value, str):
            return legacy.get(value.strip().upper())
        return None

    @property
    def rank(self) -> int:
        """0-5, for ordering comparisons."""
        return int(self.value[1])


class SecurityAction(Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EXECUTE_SHELL = "execute_shell"
    NETWORK_CALL = "network_call"
    MODIFY_SYSTEM = "modify_system"
    # L3 capabilities (UGOS_400 s.2: "multi-agent delegation, internal API
    # routing, database queries"). Until these existed, L3 granted nothing
    # beyond L2 and the level was decorative.
    DELEGATE_TASK = "delegate_task"
    ROUTE_API = "route_api"
    QUERY_DATABASE = "query_database"


FILE_ACTIONS = (SecurityAction.READ_FILE, SecurityAction.WRITE_FILE)

# UGOS_402 s.3: elevation to L4 or L5 requires dual-agent quorum or human
# operator consent. Until UGOS_702 exists, an explicit caller-supplied flag
# stands in for that approval -- but the default is deny.
ELEVATION_GATED_LEVELS = frozenset({"L4_GUARDED", "L5_ROOT"})


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

        # Capabilities per privilege level. Each level includes everything
        # below it; the ladder is cumulative.
        self.allowed_actions = {
            PermissionLevel.L0_UNTRUSTED: [
                SecurityAction.READ_FILE,
            ],
            PermissionLevel.L1_STANDARD: [
                SecurityAction.READ_FILE,
                SecurityAction.WRITE_FILE,
                SecurityAction.NETWORK_CALL,
            ],
            PermissionLevel.L2_SANDBOXED: [
                SecurityAction.READ_FILE,
                SecurityAction.WRITE_FILE,
                SecurityAction.NETWORK_CALL,
                SecurityAction.EXECUTE_SHELL,
            ],
            PermissionLevel.L3_INTEGRATOR: [
                SecurityAction.READ_FILE,
                SecurityAction.WRITE_FILE,
                SecurityAction.NETWORK_CALL,
                SecurityAction.EXECUTE_SHELL,
                SecurityAction.DELEGATE_TASK,
                SecurityAction.ROUTE_API,
                SecurityAction.QUERY_DATABASE,
            ],
            PermissionLevel.L4_GUARDED: [
                SecurityAction.READ_FILE,
                SecurityAction.WRITE_FILE,
                SecurityAction.NETWORK_CALL,
                SecurityAction.EXECUTE_SHELL,
                SecurityAction.DELEGATE_TASK,
                SecurityAction.ROUTE_API,
                SecurityAction.QUERY_DATABASE,
                SecurityAction.MODIFY_SYSTEM,
            ],
            PermissionLevel.L5_ROOT: list(SecurityAction),
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
            f"Levels: L0-L5 | Sandbox roots: {[str(r) for r in self.sandbox_roots]})"
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
        target: Optional[str] = None,
        elevation_approved: bool = False,
    ) -> bool:
        """
        Evaluates whether an agent action is permitted under Zero-Trust rules.

        elevation_approved stands in for the dual-agent quorum or human consent
        that UGOS_402 requires before an agent may operate at L4 or L5. It
        defaults to False: elevation is denied unless someone says otherwise.
        """
        decision = "DENIED"
        reason = "Unknown"

        try:
            # Check 1: Elevation gate for L4/L5
            if permission_level.value in ELEVATION_GATED_LEVELS and not elevation_approved:
                reason = (
                    f"Level '{permission_level.value}' requires explicit elevation approval "
                    f"(UGOS_402: dual-agent quorum or human operator consent)."
                )
                return False

            # Check 2: Action permission level
            if action not in self.allowed_actions.get(permission_level, []):
                reason = f"Permission level '{permission_level.value}' cannot perform action '{action.value}'."
                return False

            # Check 3: Target path inspection for file operations
            if target and action in FILE_ACTIONS:
                for pattern in self.forbidden_path_patterns:
                    if re.search(pattern, target, re.IGNORECASE):
                        reason = f"Target resource '{target}' matches forbidden pattern '{pattern}'."
                        return False

                # Check 4: Sandbox boundary
                if not self._within_sandbox(target):
                    roots = ", ".join(str(r) for r in self.sandbox_roots)
                    reason = f"Target '{target}' lies outside the permitted sandbox ({roots})."
                    return False

            decision = "ALLOWED"
            reason = "Action complies with Zero-Trust security rules."
            return True

        except Exception as exc:
            # Fail-closed (UGOS_400): an error during evaluation denies.
            decision = "DENIED"
            reason = f"Policy evaluation failed; denying by default. ({exc})"
            return False

        finally:
            log_entry = {
                "agent_id": agent_id,
                "permission_level": permission_level.value,
                "action": action.value,
                "target": target,
                "decision": decision,
                "reason": reason,
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

    # L0 read of a project file (ALLOW)
    security.authorize_action("agent_01", PermissionLevel.L0_UNTRUSTED,
                              SecurityAction.READ_FILE, "src/ugos/engines/execution.py")

    # L0 attempting shell execution (DENY)
    security.authorize_action("agent_01", PermissionLevel.L0_UNTRUSTED,
                              SecurityAction.EXECUTE_SHELL, "rm -rf /")

    # L1 attempting to read a secret file (DENY)
    security.authorize_action("agent_02", PermissionLevel.L1_STANDARD,
                              SecurityAction.READ_FILE, ".env")

    # L1 attempting to escape the sandbox (DENY)
    security.authorize_action("agent_03", PermissionLevel.L1_STANDARD,
                              SecurityAction.READ_FILE, "../../../secrets.txt")

    # L4 without approval (DENY), then with approval (ALLOW)
    security.authorize_action("agent_04", PermissionLevel.L4_GUARDED,
                              SecurityAction.MODIFY_SYSTEM, "policy_override")
    security.authorize_action("agent_04", PermissionLevel.L4_GUARDED,
                              SecurityAction.MODIFY_SYSTEM, "policy_override",
                              elevation_approved=True)

    # Legacy names still resolve
    print("\nLegacy alias check:",
          PermissionLevel.STANDARD_EXEC is PermissionLevel.L1_STANDARD,
          PermissionLevel("ELEVATED") is PermissionLevel.L2_SANDBOXED)
