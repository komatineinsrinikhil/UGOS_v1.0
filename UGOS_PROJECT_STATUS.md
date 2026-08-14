# UGOS v1.0 — PROJECT STATUS TRACKER

Last Updated: 2026-08-14

Specification: 56 spec files (53 original + UGOS_600, UGOS_800, UGOS_900).
Reference implementation: working, 11/11 tests passing.

This file is the single source of truth for project state. Both the human and
any AI assistant working on UGOS should read it before starting, and update it
after finishing. Two assistants working from separate chat histories is how a
codebase quietly breaks.

## COMPLETED SPEC MODULES

- [x] 00_Master: UGOS_000, UGOS_001
- [x] 01_Foundation: UGOS_002 through UGOS_006
- [x] 02_Architecture: UGOS_010 through UGOS_013
- [x] 03_Engines: UGOS_100 through UGOS_109
- [x] 04_Agents: UGOS_200, 201, 210-217, 220, 221 (12 files)
- [x] 05_Workflows: UGOS_500, 510-517 (9 files)
- [x] 06_Memory_Knowledge: UGOS_300, 301, 302, 310, 311 (5 files)
- [x] 08_Governance_Security: UGOS_400 through UGOS_403 (4 files)
- [x] 10_SDK: UGOS_700, UGOS_701 (2 files)

## RESERVED MODULES

Drafted 2026-08-14; only schemas/v1 remains empty:

- [x] 07_Tools_Plugins — UGOS_600 (tool architecture)
- [x] 09_Evaluation — UGOS_800 (evaluation framework)
- [x] 11_Testing — UGOS_900 (testing standard)
- [ ] schemas/v1 — intended for JSON schemas from `extract_schemas.py`, which has
      not been run against the current doc set

## IMPLEMENTATION STATUS

Working and tested:

- Zero-trust policy engine, L0-L5, with four checks: elevation gate, permission
  level, forbidden pattern, and sandbox boundary; fail-closed on error
- SQLite memory (episodic + semantic), surviving restarts
- Tool engine: file read, file write with unified diff, expression evaluation
- DAG orchestrator with topological dependency resolution
- Sandboxed execution (Docker with process fallback)
- Provider routing across eight backends with a fallback chain
- Read-only agent loop with per-tool policy enforcement
- Local web interface and Windows double-click launchers

## CLOSED SINCE THE LAST UPDATE (2026-08-14)

- **Security check was never running.** `run_my_task.py` guarded it with
  `hasattr(agent, "can_execute")`; `BaseAgent` has no such method, so the guard
  fell through to `authorized = True` and the script printed "AUTHORIZED by
  PolicyEngine" without consulting it. Now uses `evaluate_and_act()`.
- **Failed calls were persisted as answers.** `LLMRouter.generate()` returns an
  error dict rather than raising, so every run wrote to `ugos_memory.db`
  regardless of outcome. Persistence is now gated on a real provider answering.
- **No sandbox boundary.** File targets are now resolved and confined to allowed
  roots; `../..` traversal is refused. Previously an agent could have read or
  rewritten `src/ugos/security/policy.py` itself.
- **Ollama provider returned a string** where `BaseLLMProvider` requires a dict,
  which would have raised `TypeError` in `src/ugos/main.py`.
- **Provider failures were silent.** A 120s Ollama timeout surfaced only as
  "this came from a placeholder". Failures now report their reason.
- **`.gitattributes` forced LF on `.bat` files**, which can break `cmd.exe`
  parsing of parenthesised blocks. `.bat`/`.cmd` pinned to CRLF.
- Twelve stale git lock files in `.git/` were blocking commits.
- **Permission levels now match the spec.** Six levels (L0_UNTRUSTED through
  L5_ROOT) per `UGOS_400` s.2, replacing the four ad-hoc ones. Old names are
  kept as enum aliases so existing code and tests are unaffected. Adds the
  `UGOS_402` elevation gate (L4/L5 denied without explicit approval) and a
  fail-closed default on evaluation error.
- **`UGOS_201` rewritten** as the real base agent contract; it previously
  duplicated `UGOS_210_Research_Agent.md`.
- **L3 now gates real capability.** Added `DELEGATE_TASK`, `ROUTE_API` and
  `QUERY_DATABASE` to `SecurityAction`, granted at L3 and above. L2 is refused
  all three. The level was previously decorative.
- **Three reserved modules drafted**: `UGOS_600` tool architecture (from the
  v0.1 Tool Integration Framework), `UGOS_800` evaluation framework (new), and
  `UGOS_900` testing standard.
- **Spec markdown repaired across all 52 files.** 7,466 backslash escapes and
  1,105 `&#x20;` entities removed, 39 unterminated code fences closed. Verified
  by word-level diff: content identical, formatting only.

## OPEN GAPS

- **Spec describes eight specialised agents and nine workflows; the code has two
  agents and no workflow implementations.** Those documents are design, not code.
  The README says so explicitly — keep it that way.
- **Agent tools are read-only.** Write access needs tightened sandbox roots and a
  confirmation step before it is safe to enable.
- **No tool implements the L3 actions yet.** `DELEGATE_TASK`, `ROUTE_API` and
  `QUERY_DATABASE` are defined and gated, but nothing in the registry requests
  them, so L3 is enforceable but unexercised.
- **`UGOS_800` specifies a probe harness that does not exist.** The security
  probes are verified by hand today. Stated plainly in the document.
- **Test coverage lags the code.** No committed tests for the L3 actions, the
  elevation gate, fail-closed behaviour, `ugos_agent.py` or `ugos_providers.py`.
  Listed as deviations in `UGOS_900`.
- **Run-together paragraphs remain in 22 spec files.** The escape damage was
  repaired, but the original paste also destroyed newlines inside some
  paragraphs, gluing sentences together. Numbered headings were restored
  automatically; sentence boundaries inside paragraphs cannot be reconstructed
  without guessing, so those need a human pass. `UGOS_104` section 3 and the
  revision-history tables are the clearest cases.

## NEXT RESUME POINTS

Pick one; none is in progress:

1. Add write access to the agent: sandbox roots + diff + confirmation
2. Build the UGOS_800 probe harness and add the missing tests from UGOS_900
3. Host UGOS behind a public URL — needs a server, `HOST = "0.0.0.0"`, and
   authentication. Without a login, anyone with the link can spend the API key
   and read the sandbox.
4. Write tools for the L3 actions so the level is exercised, not just enforced
