# UGOS DOCUMENT METADATA

Document ID: UGOS_201_Base_Agent_Specification

Version: 1.0.0-DRAFT

Status: APPROVED

Category: Agent Architecture / Core Contract

Owner: Komatineni Sri Nikhil

Target Audience: Core Engineers, Systems Architects, Agent Developers

Last Updated: 2026-08-14

---

# UGOS_201: Base Agent Specification

## 1. PURPOSE

Defines the contract every UGOS agent must satisfy: identity, declared
privilege level, and the security-gated path an agent must take before any
action reaches a resource.

`BaseAgent` is the only route by which an agent acts. It holds no tools, no
model, and no domain knowledge. Its single responsibility is to ensure that
nothing an agent wants to do reaches the system without first passing the
Permission Engine (`UGOS_402`).

Specialist agents (`UGOS_210` through `UGOS_217`) inherit this contract and add
domain capability. They do not override the security path.

> **Implementation note.** This document previously contained a duplicate of
> `UGOS_210_Research_Agent.md`. It has been rewritten to describe the real base
> agent contract as implemented in `src/ugos/agents/base.py`.

## 2. SCOPE & BOUNDARIES

### 2.1 In-Scope

- Agent identity attributes and their lifecycle
- The declared privilege level an agent carries
- The mandatory authorization path (`evaluate_and_act`)
- The response contract for allowed and blocked actions
- Requirements placed on subclasses

### 2.2 Out-of-Scope

- Domain capabilities of specialist agents — see `UGOS_210`–`UGOS_217`
- Routing tasks to agents — see `UGOS_104_Task_Router`
- Inter-agent messaging — see `UGOS_220`, `UGOS_221`
- Tool implementations — see `UGOS_107_Tool_Engine`
- Policy rule content — see `UGOS_402_Permission_Engine`

## 3. SYSTEM ARCHITECTURE & COMPONENT MODEL

### 3.1 Identity Attributes

| Attribute | Type | Description |
|---|---|---|
| `agent_id` | string | Stable unique identifier, e.g. `ag_swe_01`. Used in every audit record. |
| `name` | string | Human-readable label, e.g. `DevBot`. Display only; never used for authorization. |
| `role` | string | Functional role, e.g. `Software Engineer`. Declarative. |
| `permission_level` | `PermissionLevel` | Privilege level L0–L5 (`UGOS_400` s.2). Governs what the agent may do. |
| `security_engine` | `PolicyEngine` | The authorization authority. Injected or constructed at initialisation. |

An agent's privilege level is declared at construction and is **not**
self-modifiable at runtime. An agent cannot raise its own clearance; elevation
to L4 or L5 requires the approval gate defined in `UGOS_402` s.3.

### 3.2 Position in the Call Path

```
Specialist Agent (UGOS_210-217)
        │  inherits
        ▼
    BaseAgent  ──requests──▶  PolicyEngine (UGOS_402)
        │                            │
        │                     ALLOW  │  DENY
        ▼                            ▼
   Tool Engine (UGOS_107)     BLOCKED_BY_SECURITY
```

There is no path from a specialist agent to a resource that bypasses this gate.
Any subclass that reaches a resource directly is in violation of this
specification.

## 4. INTERFACE CONTRACTS & DATA SCHEMAS

### 4.1 Construction

```
BaseAgent(
    agent_id: str,
    name: str,
    role: str,
    permission_level: PermissionLevel = PermissionLevel.L1_STANDARD
)
```

### 4.2 Primary Method

```
evaluate_and_act(
    action: SecurityAction,
    target: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

Evaluates the requested action against policy and returns a result. It never
raises on denial; a refusal is a returned value, so callers can surface the
reason rather than handling an exception.

### 4.3 Response Schema — Allowed

```json
{
  "status": "SUCCESS",
  "agent_id": "ag_swe_01",
  "action": "write_file",
  "target": "src/ugos/engines/execution.py",
  "result": "Agent 'DevBot' executed 'write_file' successfully."
}
```

### 4.4 Response Schema — Denied

```json
{
  "status": "BLOCKED_BY_SECURITY",
  "agent_id": "ag_swe_01",
  "action": "execute_shell",
  "target": "system_command",
  "reason": "Action violated Zero-Trust policy rules."
}
```

Callers distinguish outcomes on `status`. `BLOCKED_BY_SECURITY` is a normal,
expected result, not an error condition.

## 5. PROCESS FLOWS & STATE MACHINES

1. **Request** — the agent calls `evaluate_and_act` with an action and target.
2. **Authorize** — `PolicyEngine.authorize_action` applies, in order: the
   elevation gate, the permission-level check, the forbidden-pattern check, and
   the sandbox-boundary check.
3. **Branch** — on denial, return `BLOCKED_BY_SECURITY` with the reason and stop.
   On approval, proceed.
4. **Act** — perform the action, or dispatch to the Tool Engine.
5. **Audit** — the decision is appended to the policy audit log either way
   (`UGOS_403`).

Agents are stateless between calls. Continuity is held in the Memory Engine
(`UGOS_300`), not in agent instances.

## 6. BUSINESS RULES & OPERATIONAL POLICIES

- **BR-201-01** Every resource-affecting action MUST pass through
  `evaluate_and_act`. No subclass may reach a resource directly.
- **BR-201-02** An agent MUST NOT modify its own `permission_level` at runtime.
- **BR-201-03** Denial MUST be returned as a value, never raised, so refusals
  are reportable rather than exceptional.
- **BR-201-04** Every decision, allowed or denied, MUST be recorded in the audit
  log with agent id, action, target and reason.
- **BR-201-05** Agents MUST be constructed with the lowest privilege level
  sufficient for their role (least privilege).
- **BR-201-06** `name` MUST NOT be used in any authorization decision; only
  `agent_id` and `permission_level` are load-bearing.

## 7. EXCEPTION HANDLING & RESILIENCE

| Condition | Behaviour |
|---|---|
| Policy denies the action | Return `BLOCKED_BY_SECURITY` with reason. Do not retry. |
| Policy evaluation raises | Fail closed: deny (`UGOS_400`). |
| Target is malformed or unresolvable | Deny at the sandbox-boundary check. |
| Unknown action | Deny; the action is absent from the level's capability set. |
| Level requires elevation, none granted | Deny at the elevation gate. |

Retrying a denied action is a specification violation. A refusal reflects policy,
not a transient failure, and will not change on repetition.

## 8. SECURITY, PERMISSIONS & GOVERNANCE

Privilege levels are defined in `UGOS_400` s.2 and enforced by `UGOS_402`:

| Level | Designation | Actions available in the current implementation |
|---|---|---|
| L0 | Untrusted / Public | `read_file` |
| L1 | Standard Agent | `read_file`, `write_file`, `network_call` |
| L2 | Sandboxed Dev | L1 + `execute_shell` |
| L3 | System Integrator | Same as L2 today; delegation and DB access are not yet distinct actions |
| L4 | Guarded Admin | L3 + `modify_system`; requires elevation approval |
| L5 | Root Kernel | All actions; requires elevation approval |

Reference agents and their levels:

| Agent | Level | Rationale |
|---|---|---|
| `SoftwareEngineerAgent` | L1 | Reads and writes project files; no shell |
| `SecurityAuditAgent` | L2 | Requires expression evaluation for audit checks |

## 9. OBSERVABILITY & METRICS

Each initialisation emits an identity record: agent id, name, role and level.
Each authorization emits an audit entry containing agent id, level, action,
target, decision and reason, retained in `PolicyEngine.audit_log` and routed per
`UGOS_403`.

Recommended operational indicators: denial rate per agent, denials by check type
(elevation / level / pattern / boundary), and repeat-denial counts, which
indicate an agent operating above its privilege level or a misconfigured task.

## 10. TRACEABILITY & REVISION HISTORY

### 10.1 Requirements Mapping

| Requirement ID | Description | Validation Method |
|---|---|---|
| FR-201-01 | Agent carries a stable identity and declared privilege level | `test_base_agent_security_integration` |
| FR-201-02 | Permitted action returns `SUCCESS` | `test_base_agent_security_integration` |
| FR-201-03 | Action above privilege level returns `BLOCKED_BY_SECURITY` | `test_base_agent_security_integration` |
| FR-201-04 | Specialist agents inherit the security path unchanged | `test_specialized_agents_permissions` |
| FR-201-05 | Every decision is recorded in the audit log | `test_security_policy_enforcement` |

### 10.2 Known Deviations

| Deviation | Status |
|---|---|
| `evaluate_and_act` accepts `payload` but does not yet use it. | Open. Reserved for the execution contract. |
| Allowed actions return a simulated result string rather than dispatching to the Tool Engine. Agents that need real execution call `ToolEngine.execute_tool` directly, which applies the same policy gate. | Open. Consolidation pending. |
| L3 grants no capability beyond L2 under the current five `SecurityAction` values. | Open until delegation and database actions are defined. |

### 10.3 Revision History

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| 1.0.0-DRAFT | 2026-08-09 | Komatineni Sri Nikhil | Initial file created; content was a duplicate of UGOS_210. |
| 1.0.1-DRAFT | 2026-08-14 | Komatineni Sri Nikhil | Rewritten as the real base agent contract. Aligned privilege levels with the L0–L5 hierarchy in UGOS_400/UGOS_402. Documented known deviations. |
