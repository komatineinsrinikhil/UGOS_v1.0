# UGOS v1.0 — PROJECT STATUS TRACKER

Last Updated: 2026-08-14

Specification: 53 / 53 planned spec files drafted (100% of active modules).
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

## RESERVED / NOT YET DRAFTED

Folders exist on disk but are intentionally empty:

- [ ] 07_Tools_Plugins
- [ ] 09_Evaluation
- [ ] 11_Testing
- [ ] schemas/v1 — intended for JSON schemas from `extract_schemas.py`, which has
      not been run against the current doc set

## IMPLEMENTATION STATUS

Working and tested:

- Zero-trust policy engine with three checks: permission level, forbidden
  pattern, and sandbox boundary
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

## OPEN GAPS

- **Permission levels do not match the spec.** Code has four
  (`READ_ONLY`, `STANDARD_EXEC`, `ELEVATED`, `SYSTEM_ADMIN`); `UGOS_400`/
  `UGOS_402` define six (L0–L5).
- **`UGOS_201_Base_Agent_Specification.md` duplicates `UGOS_210_Research_Agent.md`**
  and needs rewriting as the real base agent contract.
- **Spec describes eight specialised agents and nine workflows; the code has two
  agents and no workflow implementations.** Those documents are design, not code.
  The README says so explicitly — keep it that way.
- **Agent tools are read-only.** Write access needs tightened sandbox roots and a
  confirmation step before it is safe to enable.
- **Spec markdown is damaged.** Every file under `00_Master` through `10_SDK`
  contains backslash-escaped markdown (`\#`, `\*\*`, `\_`) and `&#x20;` entities
  from a bad paste; several have unterminated code fences that swallow later
  sections. `UGOS_104_Task_Router.md` is the clearest example.

## NEXT RESUME POINTS

Pick one; none is in progress:

1. Clean the spec markdown (56 files) — mechanical, unblocks reading them at all
2. Reconcile the permission-level mismatch between code and `UGOS_400`/`UGOS_402`
3. Rewrite `UGOS_201` as the real base agent spec
4. Add write access to the agent: sandbox roots + diff + confirmation
5. Draft one of the reserved modules (07 / 09 / 11)
