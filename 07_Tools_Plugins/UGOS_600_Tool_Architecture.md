# UGOS DOCUMENT METADATA

Document ID: UGOS_600_Tool_Architecture

Version: 1.0.0-DRAFT

Status: APPROVED

Category: Tools & Plugins / Architecture

Owner: Komatineni Sri Nikhil

Target Audience: Core Engineers, Tool Authors, Systems Architects

Last Updated: 2026-08-14

---

# UGOS_600: Tool Architecture

## 1. PURPOSE

Defines how capability reaches an agent. A UGOS agent has no inherent ability to
touch anything: it can read no file, run no command, and reach no service except
by requesting a registered tool, which the Permission Engine (`UGOS_402`) then
allows or refuses.

This document specifies the registry, the dispatch path, and the rules a tool
must satisfy to be registered at all.

> **Lineage.** This module derives from the v0.1 Tool Integration Framework
> (`archive/v0.1/06_UGOS_TOOL_EXTENSION_SYSTEM.md`), which described seven tool
> categories and selection logic for a custom GPT. That document was advisory —
> guidance a model was asked to follow. This one is enforced: tools are objects
> in a registry with a declared security action, and dispatch is impossible
> without passing the gate.

## 2. SCOPE & BOUNDARIES

### 2.1 In-Scope

- The tool registry and its entry shape
- The dispatch path from agent request to execution
- The security contract every tool must satisfy
- Tool categories and the privilege level each implies
- Failure semantics

### 2.2 Out-of-Scope

- The plugin packaging format — see `UGOS_601`
- Policy rule content — see `UGOS_402`
- Which agent is chosen for a task — see `UGOS_104`
- Agent-side reasoning about which tool to request — see `UGOS_200`

## 3. SYSTEM ARCHITECTURE & COMPONENT MODEL

### 3.1 The registry

`ToolEngine` (`src/ugos/core/tools.py`) holds a dictionary of tool name to
entry. Each entry declares two things:

| Field | Meaning |
|---|---|
| `action` | The `SecurityAction` this tool requires. Not advisory — this is what the policy is asked about. |
| `handler` | The callable that runs once, and only once, the policy has allowed it. |

Registered in the reference implementation:

| Tool | Required action | Minimum level |
|---|---|---|
| `file_reader` | `READ_FILE` | L0 |
| `file_writer` | `WRITE_FILE` | L1 |
| `python_eval` | `EXECUTE_SHELL` | L2 |

### 3.2 Dispatch path

```
Agent requests tool by name
        │
        ▼
  Tool in registry?  ──no──▶ DENIED: "Tool 'x' not registered."
        │ yes
        ▼
  PolicyEngine.authorize_action(agent_id, level, entry.action, target)
        │
   ALLOW │ DENY ──▶ DENIED, with reason, recorded in the audit log
        ▼
  entry.handler(...)  ──▶ result
```

The registry lookup happens *before* the policy check, so an unregistered name
is refused without consulting policy. There is no path to `handler` that skips
`authorize_action`.

### 3.3 Tool categories

v0.1 defined seven categories. Restated here with the privilege level each
implies, which is the part that was missing:

| Category | Example | Implied level |
|---|---|---|
| Knowledge retrieval | read a file, list a folder | L0 |
| File processing | write a file, generate a diff | L1 |
| Code execution | evaluate an expression, run tests | L2 |
| External APIs | call a third-party service | L3 (`ROUTE_API`) |
| Data access | query a database | L3 (`QUERY_DATABASE`) |
| Delegation | hand a subtask to another agent | L3 (`DELEGATE_TASK`) |
| System administration | patch, override policy | L4, elevation required |

A tool MUST declare the lowest action that covers what it actually does. A tool
that declares `READ_FILE` and then writes is a specification violation and a
security defect.

## 4. INTERFACE CONTRACTS & DATA SCHEMAS

### 4.1 Invocation

```
ToolEngine.execute_tool(
    tool_name: str,
    agent_id: str,
    permission_level: PermissionLevel,
    **kwargs
) -> Dict[str, Any]
```

`kwargs` carries the tool's own arguments. `target` is special: when present it
is passed to the policy for pattern and sandbox evaluation.

### 4.2 Response — allowed

```json
{ "status": "SUCCESS", "output": "..." }
```

### 4.3 Response — refused

```json
{
  "status": "DENIED",
  "reason": "Action 'write_file' not authorized for agent 'ag_reader_01' under permission level L0_UNTRUSTED."
}
```

### 4.4 Response — failed

```json
{ "status": "ERROR", "reason": "File 'notes.txt' does not exist." }
```

`DENIED` and `ERROR` are different outcomes and MUST NOT be collapsed. Refusal
is a policy decision; error is a fault. An agent should report the first and may
reasonably retry differently after the second.

## 5. PROCESS FLOWS & STATE MACHINES

1. **Request** — agent names a tool and supplies arguments.
2. **Resolve** — registry lookup; unknown name returns `DENIED` immediately.
3. **Authorize** — policy evaluates the declared action against the agent's
   level, plus target patterns and sandbox boundary for file actions.
4. **Execute** — handler runs.
5. **Audit** — the decision is recorded either way (`UGOS_403`).

Relative paths MUST be anchored to a sandbox root before evaluation. Resolving
them against the process working directory makes the boundary depend on where
UGOS happened to be started, which is not a boundary.

## 6. BUSINESS RULES & OPERATIONAL POLICIES

- **BR-600-01** No tool executes without a policy decision. No exceptions.
- **BR-600-02** A tool declares exactly one `SecurityAction`, the lowest that
  covers its full behaviour.
- **BR-600-03** Unregistered tool names are refused; the registry is the
  complete list of what exists.
- **BR-600-04** Tools MUST NOT widen their own permissions at runtime.
- **BR-600-05** `DENIED` and `ERROR` are distinct and separately reported.
- **BR-600-06** Refusals are returned as values, never raised.
- **BR-600-07** A tool that takes a path MUST accept it as `target` so the
  policy can inspect it. Hiding the path in another argument bypasses checks 3
  and 4 and is a defect.

## 7. EXCEPTION HANDLING & RESILIENCE

| Condition | Behaviour |
|---|---|
| Unregistered tool | `DENIED`, listing available tools |
| Insufficient privilege | `DENIED` with the level and action named |
| Forbidden target pattern | `DENIED` naming the matched pattern |
| Target outside sandbox | `DENIED` naming the permitted roots |
| Handler raises | `ERROR` with the reason; the agent is not told it succeeded |
| Policy evaluation raises | Fail closed — deny (`UGOS_400`) |

## 8. SECURITY, PERMISSIONS & GOVERNANCE

The registry is the attack surface. Every tool added widens what an agent can
do, and no amount of prompt instruction narrows it again — which is the whole
reason this layer exists rather than a paragraph telling the model to be careful.

Requirements for any new tool:

1. Declare the lowest sufficient action.
2. Pass user-supplied paths as `target`.
3. Assume the arguments are hostile; the model may be repeating something a
   user injected.
4. Prefer read-only. A read tool that turns out to be wrong is an inconvenience;
   a write tool that turns out to be wrong is an incident.

## 9. OBSERVABILITY & METRICS

Every dispatch emits an audit record: agent id, level, tool, action, target,
decision, reason. Worth tracking: refusals per tool (a tool refused constantly
is registered at the wrong level or being requested by the wrong agents), error
rate per tool, and requests for unregistered names, which indicate a model
inventing capabilities.

## 10. TRACEABILITY & REVISION HISTORY

### 10.1 Requirements Mapping

| Requirement ID | Description | Validation Method |
|---|---|---|
| FR-600-01 | Registered tool executes when permitted | `test_tool_engine_execution` |
| FR-600-02 | Tool refused when privilege insufficient | `test_tool_engine_execution` |
| FR-600-03 | File writer produces a unified diff | `test_tool_engine_file_writer_diff` |
| FR-600-04 | Specialist agents inherit tool restrictions | `test_specialized_agents_permissions` |

### 10.2 Known Deviations

| Deviation | Status |
|---|---|
| No tool exists yet for the L3 actions (`DELEGATE_TASK`, `ROUTE_API`, `QUERY_DATABASE`). The actions are defined and gated; the tools are not written. | Open |
| `python_eval` declares `EXECUTE_SHELL` though it evaluates a restricted expression rather than a shell command. Deliberately over-declared: the safer error. | Accepted |
| The agent-facing toolbox (`ugos_agent.ReadOnlyToolbox`) implements `list_dir` and `system_status` outside the `ToolEngine` registry, though both still call the policy directly. | Open — should be registered |

### 10.3 Revision History

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| 1.0.0-DRAFT | 2026-08-14 | Komatineni Sri Nikhil | Initial specification. Supersedes the advisory v0.1 Tool Integration Framework. |
