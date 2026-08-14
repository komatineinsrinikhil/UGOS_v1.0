# UGOS DOCUMENT METADATA

Document ID: UGOS_900_Testing_Standard

Version: 1.0.0-DRAFT

Status: APPROVED

Category: Testing / Engineering Standard

Owner: Komatineni Sri Nikhil

Target Audience: Core Engineers, Contributors

Last Updated: 2026-08-14

---

# UGOS_900: Testing Standard

## 1. PURPOSE

Defines what must be tested in UGOS, how, and what may not be merged without a
test. Testing here means verifying the components behave as specified.
Evaluating whether an agent's *answers* are good is a separate concern
(`UGOS_800`).

The distinction matters because the two fail differently. A broken component
fails loudly. A working component with a wrong policy fails silently, and
silence is what this standard exists to prevent.

## 2. SCOPE & BOUNDARIES

### 2.1 In-Scope

- Required coverage by subsystem
- Rules for security tests specifically
- How to test code that calls a model
- What blocks a merge

### 2.2 Out-of-Scope

- Answer quality and grounding — see `UGOS_800`
- Runtime audit logging — see `UGOS_403`

## 3. SYSTEM ARCHITECTURE & COMPONENT MODEL

### 3.1 Current suite

`tests/test_core.py`, 11 tests, all passing:

| Test | Verifies |
|---|---|
| `test_execution_engine_single_task` | Task resolution |
| `test_orchestrator_dag_pipeline` | Topological dependency order |
| `test_security_policy_enforcement` | Permission matrix, forbidden patterns |
| `test_base_agent_security_integration` | Agents cannot bypass the gate |
| `test_tool_engine_execution` | Dispatch and refusal |
| `test_memory_engine_episodic_and_semantic` | Both memory tiers |
| `test_specialized_agents_permissions` | Inherited restrictions |
| `test_tool_engine_file_writer_diff` | Unified diff generation |
| `test_sqlite_memory_engine_persistence` | Storage survives restart |
| `test_llm_router_primary_and_fallback` | Failover chain |
| `test_execution_engine_sandbox_fallback` | Docker to process fallback |

### 3.2 Required coverage

| Subsystem | Required |
|---|---|
| `security/policy.py` | Every level against every action; every forbidden pattern; sandbox escape; elevation gate both ways; fail-closed on malformed input |
| `core/tools.py` | Each tool allowed and refused; error distinct from refusal |
| `core/memory.py` | Both tiers; persistence across instances |
| `llm/router.py` | Primary success; primary failure to fallback; total failure |
| `ugos_agent.py` | Tool request parsed; refusal fed back; step cap; malformed model output |
| `ugos_providers.py` | Response shape per provider; each error class distinguished |

## 4. INTERFACE CONTRACTS & DATA SCHEMAS

Tests use the real objects. A test that constructs a fake `PolicyEngine` to make
another test pass has removed the thing being verified.

Model calls are the exception, and are stubbed with a scripted provider that
returns fixed strings — including deliberately malformed ones, because that is
what small models actually produce.

```python
class Scripted(BaseLLMProvider):
    def __init__(self, replies):
        super().__init__("Scripted", "fixture-1")
        self.replies = list(replies)
    def complete(self, prompt, system_prompt=None, **kw):
        return {"status": "SUCCESS", "provider": "Scripted", "model": "fixture-1",
                "content": self.replies.pop(0), "usage": {}}
```

## 5. PROCESS FLOWS & STATE MACHINES

```bash
python -m pytest tests/test_core.py -v
```

Every test must pass before a commit that touches `src/`. A test that is
expected to fail is deleted or fixed, never commented out — a commented test is
a claim of coverage that does not exist.

## 6. BUSINESS RULES & OPERATIONAL POLICIES

- **BR-900-01** A change to `security/policy.py` MUST add or update a test.
  There is no such thing as an obvious security change.
- **BR-900-02** Security tests assert the *reason*, not only the boolean.
  Passing for the wrong reason hides the next bug.
- **BR-900-03** Every deny path is tested. An untested deny is an assumption.
- **BR-900-04** Tests use real components; only the model is stubbed.
- **BR-900-05** Tests clean up files they create.
- **BR-900-06** Tests do not require network access. A suite that needs the
  internet cannot verify the offline path.
- **BR-900-07** A bug fix ships with the test that would have caught it.

## 7. EXCEPTION HANDLING & RESILIENCE

| Condition | Behaviour |
|---|---|
| Test needs a model | Use a scripted provider, never a live one |
| Test needs a file | Create in the sandbox, delete afterwards |
| Test needs Docker | Assert the fallback path instead |
| Flaky test | Fix or delete; a flaky test trains people to ignore failures |

## 8. SECURITY, PERMISSIONS & GOVERNANCE

Security tests carry an extra requirement: they must assert *why*. Checking that
reading `.env` returns `False` is weak — it would still pass if the file simply
did not exist. The assertion must name the cause:

```python
allowed = policy.authorize_action("a", P.L1_STANDARD, A.READ_FILE, ".env")
assert allowed is False
assert "forbidden pattern" in policy.last_decision()["reason"]
```

Every deny path in `authorize_action` has a distinct reason, and each MUST be
covered: elevation gate, permission level, forbidden pattern, sandbox boundary,
fail-closed.

## 9. OBSERVABILITY & METRICS

Report per run: pass count, fail count, and which deny paths were exercised. The
last is the useful one — a suite that never exercises the sandbox boundary is
not testing the sandbox boundary, no matter how green it looks.

## 10. TRACEABILITY & REVISION HISTORY

### 10.1 Requirements Mapping

| Requirement ID | Description | Validation Method |
|---|---|---|
| FR-900-01 | Suite runs without network access | Manual verification |
| FR-900-02 | Every policy deny path has a test | Coverage review |
| FR-900-03 | Suite passes before every `src/` commit | Developer discipline |

### 10.2 Known Deviations

| Deviation | Status |
|---|---|
| The suite has no test for the L3 actions, the elevation gate, or fail-closed behaviour, though all three are implemented and were verified manually. Those checks belong in `test_core.py`. | Open |
| `ugos_agent.py` and `ugos_providers.py` have no tests in the committed suite; both were verified with scripted providers during development only. | Open |
| Nothing enforces BR-900-01 automatically. There is no CI. | Open |

### 10.3 Revision History

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| 1.0.0-DRAFT | 2026-08-14 | Komatineni Sri Nikhil | Initial standard, describing the existing 11-test suite and the coverage it still lacks. |
