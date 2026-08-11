\# UGOS\_211\_Software\_Engineer\_Agent.md



\*\*Module:\*\* `04\_Agents`  

\*\*Specification Version:\*\* `1.0.0`  

\*\*File Reference:\*\* `UGOS\_211`  

\*\*Target Engine Interface:\*\* `UGOS\_100\_Execution\_Engine`, `UGOS\_107\_Tool\_Engine`, `UGOS\_108\_Evaluation\_Engine`  

\*\*Status:\*\* `ACTIVE SPECIFICATION`



\---



\## 1. Module Overview \& System Role



The \*\*Software Engineer Agent (`UGOS\_211`)\*\* is a Tier 2 Specialist Agent responsible for automated code generation, multi-file refactoring, unit test suite synthesis, syntax tree manipulation, and iterative debugging across the UGOS environment.



Operating under an $L\_4$ Guarded security clearance within ephemeral sandboxed execution environments, `UGOS\_211` converts software requirements, technical specifications, and bug tickets into production-grade source code backed by comprehensive test suites and verified type safety.



\### Primary Objectives

1\. \*\*Automated Code Synthesis:\*\* Generate idiomatic, modular source code across target languages (Python, Rust, TypeScript, C++) following system-wide coding standards.

2\. \*\*Multi-File Refactoring \& AST Manipulation:\*\* Perform structural AST-level code modifications, dependency graph updates, and API migrations without introducing regressions.

3\. \*\*Test Suite Synthesis \& Execution:\*\* Write unit, integration, and property-based test suites, validating correctness inside isolated $L\_4$ sandboxes.

4\. \*\*Iterative Debugging \& Self-Correction:\*\* Analyze stack traces, compilation errors, and failing test assertions to synthesize minimal patch revisions.



\---



\## 2. Core Capabilities \& Task Matrix



| Domain | Capability | Input Vector | Target Output / Action |

| :--- | :--- | :--- | :--- |

| \*\*Code Generation\*\* | Specification-to-Code Synthesis | Architectural Spec / Prompt | Clean Module Code \& Imports |

| \*\*Testing \& QA\*\* | Test Suite Construction | Source File / Schema | Unit \& Integration Test Files |

| \*\*Refactoring\*\* | AST Transformation | Source Tree + Goal Spec | Refactored Codebase Commit |

| \*\*Debugging\*\* | Traceback Analysis | Error Log + Source Code | Minimal Patch Payload |

| \*\*Dependency Management\*\* | Software Package Audit | `requirements.txt` / `Cargo.toml` | Resolved Dependency Matrix |



\---



\## 3. Agent Architecture \& Execution Loop



`UGOS\_211` follows a test-driven iteration loop: \*\*Parse Spec $\\rightarrow$ Draft Code $\\rightarrow$ Synthesize Tests $\\rightarrow$ Sandbox Run $\\rightarrow$ Refine\*\*.



&#x20;                   ┌────────────────────────┐

&#x20;                   │ Specification / Ticket │

&#x20;                   └───────────┬────────────┘

&#x20;                               │

&#x20;                               ▼

┌──────────────────┐    ┌────────────────────────┐    ┌──────────────────┐│ Patch \& Commit   │ ◄──┤ Draft Code \& Tests     ├──► │ Sandbox Execution│└──────────────────┘    └───────────┬────────────┘    └──────────────────┘│▼┌────────────────────────┐│ Diagnostic / Retry Loop│└────────────────────────┘

\### Execution Loop Stages

1\. \*\*Parse Spec:\*\* Ingest technical specification, target interface contracts, and existing project context.

2\. \*\*Draft Code \& Tests:\*\* Synthesize source modules alongside corresponding test cases matching interface assertions.

3\. \*\*Sandbox Execution:\*\* Dispatch executable artifacts to `UGOS\_100\_Execution\_Engine` inside an isolated $L\_4$ container environment.

4\. \*\*Diagnostic \& Retry Loop:\*\* Ingest compilation or runtime test failures, isolate faulty AST nodes, and apply targeted bug fixes (up to `max\_iterations`).

5\. \*\*Patch \& Commit:\*\* Format, lint, and return final code diffs along with test coverage verification reports.



\---



\## 4. Input \& Output Interface Schemas



\### 4.1 Ingestion Schema: Software Engineering Task (`SoftwareEngTaskPayload`)



```json

{

&#x20; "$schema": "\[https://ugos.dev/schemas/v1/software\_eng\_task\_payload.json](https://ugos.dev/schemas/v1/software\_eng\_task\_payload.json)",

&#x20; "task\_id": "task\_swe\_882019",

&#x20; "timestamp": "2026-08-10T08:45:00Z",

&#x20; "task\_type": "FEATURE\_IMPLEMENTATION",

&#x20; "target\_language": "python",

&#x20; "specification\_ref": "mem://specs/UGOS\_201\_Base\_Agent\_Specification.md",

&#x20; "workspace\_root": "mem://workspace/ugos\_core/",

&#x20; "test\_coverage\_threshold": 0.90

}

4.2 Output Schema: Code Artifact Directive (CodeArtifactDirective)JSON{

&#x20; "$schema": "\[https://ugos.dev/schemas/v1/code\_artifact\_directive.json](https://ugos.dev/schemas/v1/code\_artifact\_directive.json)",

&#x20; "directive\_id": "dir\_swe\_001928",

&#x20; "task\_ref": "task\_swe\_882019",

&#x20; "execution\_status": "SUCCESS",

&#x20; "files\_modified": \[

&#x20;   "ugos/agents/base\_agent.py",

&#x20;   "tests/test\_base\_agent.py"

&#x20; ],

&#x20; "patch\_ref": "mem://patches/swe\_task\_882019.patch",

&#x20; "test\_results": {

&#x20;   "tests\_passed": 18,

&#x20;   "tests\_failed": 0,

&#x20;   "line\_coverage\_pct": 94.2

&#x20; }

}

5\. System InteroperabilityUGOS\_100\_Execution\_Engine Interoperability: Request ephemeral sandbox instances to execute code, run tests, and measure execution performance.UGOS\_107\_Tool\_Engine Interoperability: Invoke compilers, static analyzers (e.g., ruff, clippy, mypy), linter suites, and git version control tools.UGOS\_108\_Evaluation\_Engine Interoperability: Submit generated code artifacts for automatic security scanning, constraint checking, and code style validation.
6. Safety Guardrails \& Operational Constraints\[!WARNING]Sandbox Isolation: All code synthesized by UGOS\_211 must run strictly inside an ephemeral sandbox with non-root privileges, restricted network access, and hard CPU/memory limits.Static Analysis Gate: Code must pass static type checking and zero-critical-issue linting before execution or patch submission.No Arbitrary System Calls: Direct raw execution of destructive shell commands (rm -rf, raw socket writes) is intercepted and blocked at the tool gateway ($L\_4$).

