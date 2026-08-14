# UGOS_211_Software_Engineer_Agent.md

**Module:** `04_Agents`

**Specification Version:** `1.0.0`

**File Reference:** `UGOS_211`

**Target Engine Interface:** `UGOS_100_Execution_Engine`, `UGOS_107_Tool_Engine`, `UGOS_108_Evaluation_Engine`

**Status:** `ACTIVE SPECIFICATION`

---

## 1. Module Overview & System Role

The **Software Engineer Agent (`UGOS_211`)** is a Tier 2 Specialist Agent responsible for automated code generation, multi-file refactoring, unit test suite synthesis, syntax tree manipulation, and iterative debugging across the UGOS environment.

Operating under an $L_4$ Guarded security clearance within ephemeral sandboxed execution environments, `UGOS_211` converts software requirements, technical specifications, and bug tickets into production-grade source code backed by comprehensive test suites and verified type safety.

### Primary Objectives

1. **Automated Code Synthesis:** Generate idiomatic, modular source code across target languages (Python, Rust, TypeScript, C++) following system-wide coding standards.

2. **Multi-File Refactoring & AST Manipulation:** Perform structural AST-level code modifications, dependency graph updates, and API migrations without introducing regressions.

3. **Test Suite Synthesis & Execution:** Write unit, integration, and property-based test suites, validating correctness inside isolated $L_4$ sandboxes.

4. **Iterative Debugging & Self-Correction:** Analyze stack traces, compilation errors, and failing test assertions to synthesize minimal patch revisions.

---

## 2. Core Capabilities & Task Matrix

| Domain | Capability | Input Vector | Target Output / Action |

| :--- | :--- | :--- | :--- |

| **Code Generation** | Specification-to-Code Synthesis | Architectural Spec / Prompt | Clean Module Code & Imports |

| **Testing & QA** | Test Suite Construction | Source File / Schema | Unit & Integration Test Files |

| **Refactoring** | AST Transformation | Source Tree + Goal Spec | Refactored Codebase Commit |

| **Debugging** | Traceback Analysis | Error Log + Source Code | Minimal Patch Payload |

| **Dependency Management** | Software Package Audit | `requirements.txt` / `Cargo.toml` | Resolved Dependency Matrix |

---

## 3. Agent Architecture & Execution Loop

`UGOS_211` follows a test-driven iteration loop: **Parse Spec $\rightarrow$ Draft Code $\rightarrow$ Synthesize Tests $\rightarrow$ Sandbox Run $\rightarrow$ Refine**.

                    ┌────────────────────────┐

                    │ Specification / Ticket │

                    └───────────┬────────────┘

                                │

                                ▼

┌──────────────────┐    ┌────────────────────────┐    ┌──────────────────┐│ Patch & Commit   │ ◄──┤ Draft Code & Tests     ├──► │ Sandbox Execution│└──────────────────┘    └───────────┬────────────┘    └──────────────────┘│▼┌────────────────────────┐│ Diagnostic / Retry Loop│└────────────────────────┘

### Execution Loop Stages

1. **Parse Spec:** Ingest technical specification, target interface contracts, and existing project context.

2. **Draft Code & Tests:** Synthesize source modules alongside corresponding test cases matching interface assertions.

3. **Sandbox Execution:** Dispatch executable artifacts to `UGOS_100_Execution_Engine` inside an isolated $L_4$ container environment.

4. **Diagnostic & Retry Loop:** Ingest compilation or runtime test failures, isolate faulty AST nodes, and apply targeted bug fixes (up to `max_iterations`).

5. **Patch & Commit:** Format, lint, and return final code diffs along with test coverage verification reports.

---

## 4. Input & Output Interface Schemas

### 4.1 Ingestion Schema: Software Engineering Task (`SoftwareEngTaskPayload`)

```json

{

  "$schema": "[https://ugos.dev/schemas/v1/software_eng_task_payload.json](https://ugos.dev/schemas/v1/software_eng_task_payload.json)",

  "task_id": "task_swe_882019",

  "timestamp": "2026-08-10T08:45:00Z",

  "task_type": "FEATURE_IMPLEMENTATION",

  "target_language": "python",

  "specification_ref": "mem://specs/UGOS_201_Base_Agent_Specification.md",

  "workspace_root": "mem://workspace/ugos_core/",

  "test_coverage_threshold": 0.90

}
```

4.2 Output Schema: Code Artifact Directive (CodeArtifactDirective)JSON{

  "$schema": "[https://ugos.dev/schemas/v1/code_artifact_directive.json](https://ugos.dev/schemas/v1/code_artifact_directive.json)",

  "directive_id": "dir_swe_001928",

  "task_ref": "task_swe_882019",

  "execution_status": "SUCCESS",

  "files_modified": [

    "ugos/agents/base_agent.py",

    "tests/test_base_agent.py"

  ],

  "patch_ref": "mem://patches/swe_task_882019.patch",

  "test_results": {

    "tests_passed": 18,

    "tests_failed": 0,

    "line_coverage_pct": 94.2

  }

}

5. System InteroperabilityUGOS_100_Execution_Engine Interoperability: Request ephemeral sandbox instances to execute code, run tests, and measure execution performance.UGOS_107_Tool_Engine Interoperability: Invoke compilers, static analyzers (e.g., ruff, clippy, mypy), linter suites, and git version control tools.UGOS_108_Evaluation_Engine Interoperability: Submit generated code artifacts for automatic security scanning, constraint checking, and code style validation.
6. Safety Guardrails & Operational Constraints[!WARNING]Sandbox Isolation: All code synthesized by UGOS_211 must run strictly inside an ephemeral sandbox with non-root privileges, restricted network access, and hard CPU/memory limits.Static Analysis Gate: Code must pass static type checking and zero-critical-issue linting before execution or patch submission.No Arbitrary System Calls: Direct raw execution of destructive shell commands (rm -rf, raw socket writes) is intercepted and blocked at the tool gateway ($L_4$).
