# UGOS_216_QA_Testing_Agent.md

**Module:** `04_Agents`

**Specification Version:** `1.0.0`

**File Reference:** `UGOS_216`

**Target Engine Interface:** `UGOS_100_Execution_Engine`, `UGOS_108_Evaluation_Engine`, `UGOS_107_Tool_Engine`

**Status:** `ACTIVE SPECIFICATION`

---

## 1. Module Overview & System Role

The **QA & Testing Agent (`UGOS_216`)** is a Tier 2 Specialist Agent responsible for automated test case generation, test harness execution, assertion verification, regression testing, and quality assurance auditing across all UGOS code artifacts and system outputs.

While `UGOS_211_Software_Engineer_Agent` generates unit tests alongside code drafts, `UGOS_216` operates as an independent, unbiased evaluation body—synthesizing black-box, white-box, boundary-value, stress, and mutation tests derived directly from functional requirements and acceptance criteria.

### Primary Objectives

1. **Automated Test Case Generation:** Synthesize comprehensive test suites (unit, integration, end-to-end, regression, fuzz) from PRDs, acceptance criteria, and API schemas.

2. **Assertion & Output Verification:** Execute tests in isolated runtime sandboxes, evaluating outputs against strict semantic and functional assertions.

3. **Mutation & Robustness Testing:** Introduce synthetic edge cases, malformed payloads, and fault injections to test system resilience.

4. **Coverage & Quality Reporting:** Calculate branch coverage, statement coverage, and mutation scores, outputting structured test execution reports.

---

## 2. Core Capabilities & Task Matrix

| Domain | Capability | Input Vector | Target Output / Action |

| :--- | :--- | :--- | :--- |

| **Test Generation** | Requirement-to-Test Synthesis | Acceptance Criteria, OpenAPI Specs | Executable Test Suite Files |

| **Test Execution** | Sandboxed Harness Execution | Test Files + Code Artifacts | Execution Logs & Assertions |

| **Edge-Case / Fuzzing** | Mutation & Boundary Testing | Input Schemas, API Endpoints | Fuzzing Reports & Fault Traces |

| **Quality Reporting** | Coverage Analysis | Executed Test Metrics | Coverage Matrix & QA Clearance |

---

## 3. Agent Architecture & Execution Loop

`UGOS_216` executes an iterative quality evaluation loop: **Parse Criteria $\rightarrow$ Synthesize Tests $\rightarrow$ Execute $\rightarrow$ Evaluate Assertions $\rightarrow$ Certify**.

                    ┌────────────────────────┐

                    │ Acceptance Criteria    │

                    └───────────┬────────────┘

                                │

                                ▼

┌──────────────────┐    ┌────────────────────────┐    ┌──────────────────┐

│ Quality Clearance│ ◄──┤ Synthesize Test Suite  ├──► │ Sandboxed Harness│

└──────────────────┘    └───────────┬────────────┘    └──────────────────┘

│

▼

┌────────────────────────┐

│ Assertion & Coverage   │

└───────────┬────────────┘

### Execution Loop Stages

1. **Parse Criteria:** Ingest User Stories, Given-When-Then criteria from `UGOS_215`, or code implementations from `UGOS_211`.

2. **Synthesize Tests:** Generate test scripts covering positive cases, boundary limits, negative inputs, and concurrent calls.

3. **Execute:** Dispatch test harnesses to `UGOS_100_Execution_Engine` inside isolated $L_4$ execution sandboxes.

4. **Evaluate Assertions:** Validate outputs against assertion trees, capturing performance latencies, stack traces, and unhandled exceptions.

5. **Certify:** Compute final quality clearance score; pass cleared artifacts to deployment pipelines or return regression reports to `UGOS_211`.

---

## 4. Input & Output Interface Schemas

### 4.1 Ingestion Schema: QA Evaluation Request (`QAEvaluationPayload`)

```json

{

  "$schema": "[https://ugos.dev/schemas/v1/qa_evaluation_payload.json](https://ugos.dev/schemas/v1/qa_evaluation_payload.json)",

  "evaluation_id": "qa_eval_991823",

  "timestamp": "2026-08-10T09:10:00Z",

  "target_artifact": {

    "type": "PYTHON_MODULE",

    "source_ref": "mem://workspace/ugos_core/rate_limiter.py",

    "spec_ref": "mem://specs/US_01_rate_limiting.json"

  },

  "test_types_required": ["UNIT", "BOUNDARY", "MUTATION"],

  "min_coverage_pct": 90.0

}
```

4.2 Output Schema: QA Certification Report (QACertificationReport)

JSON

{

  "$schema": "[https://ugos.dev/schemas/v1/qa_certification_report.json](https://ugos.dev/schemas/v1/qa_certification_report.json)",

  "report_id": "rep_qa_004912",

  "evaluation_ref": "qa_eval_991823",

  "certification_status": "PASSED",

  "metrics": {

    "total_tests_run": 42,

    "tests_passed": 42,

    "tests_failed": 0,

    "line_coverage_pct": 96.4,

    "mutation_score_pct": 91.2

  },

  "fuzz_test_summary": {

    "malformed_payloads_injected": 1000,

    "unhandled_exceptions": 0

  },

  "clearance_granted": true

}

5. System Interoperability

UGOS_100_Execution_Engine Interoperability: Spawn sandboxed test environments to execute test suites securely without side effects.

UGOS_108_Evaluation_Engine Interoperability: Supply test metrics and assertion records to calculate overall task completion scores.

UGOS_211_Software_Engineer_Agent Interoperability: Return detailed regression reports and failing stack traces when code fails QA checks.

6. Safety Guardrails & Operational Constraints

[!CAUTION]

Independent Verification Rule: UGOS_216 must generate its own test cases independently of those written by UGOS_211. Re-using developer test cases as the sole QA standard is strictly prohibited.

Sandbox Enclosure: All test execution must occur inside non-root, ephemeral container environments with CPU, RAM, and disk execution caps.

Zero-Suppression Policy: Failing assertions must never be silenced, ignored, or bypassed automatically; every failure requires resolution or explicit operator override.
