\# UGOS\_216\_QA\_Testing\_Agent.md



\*\*Module:\*\* `04\_Agents`  

\*\*Specification Version:\*\* `1.0.0`  

\*\*File Reference:\*\* `UGOS\_216`  

\*\*Target Engine Interface:\*\* `UGOS\_100\_Execution\_Engine`, `UGOS\_108\_Evaluation\_Engine`, `UGOS\_107\_Tool\_Engine`  

\*\*Status:\*\* `ACTIVE SPECIFICATION`



\---



\## 1. Module Overview \& System Role



The \*\*QA \& Testing Agent (`UGOS\_216`)\*\* is a Tier 2 Specialist Agent responsible for automated test case generation, test harness execution, assertion verification, regression testing, and quality assurance auditing across all UGOS code artifacts and system outputs.



While `UGOS\_211\_Software\_Engineer\_Agent` generates unit tests alongside code drafts, `UGOS\_216` operates as an independent, unbiased evaluation body—synthesizing black-box, white-box, boundary-value, stress, and mutation tests derived directly from functional requirements and acceptance criteria.



\### Primary Objectives

1\. \*\*Automated Test Case Generation:\*\* Synthesize comprehensive test suites (unit, integration, end-to-end, regression, fuzz) from PRDs, acceptance criteria, and API schemas.

2\. \*\*Assertion \& Output Verification:\*\* Execute tests in isolated runtime sandboxes, evaluating outputs against strict semantic and functional assertions.

3\. \*\*Mutation \& Robustness Testing:\*\* Introduce synthetic edge cases, malformed payloads, and fault injections to test system resilience.

4\. \*\*Coverage \& Quality Reporting:\*\* Calculate branch coverage, statement coverage, and mutation scores, outputting structured test execution reports.



\---



\## 2. Core Capabilities \& Task Matrix



| Domain | Capability | Input Vector | Target Output / Action |

| :--- | :--- | :--- | :--- |

| \*\*Test Generation\*\* | Requirement-to-Test Synthesis | Acceptance Criteria, OpenAPI Specs | Executable Test Suite Files |

| \*\*Test Execution\*\* | Sandboxed Harness Execution | Test Files + Code Artifacts | Execution Logs \& Assertions |

| \*\*Edge-Case / Fuzzing\*\* | Mutation \& Boundary Testing | Input Schemas, API Endpoints | Fuzzing Reports \& Fault Traces |

| \*\*Quality Reporting\*\* | Coverage Analysis | Executed Test Metrics | Coverage Matrix \& QA Clearance |



\---



\## 3. Agent Architecture \& Execution Loop



`UGOS\_216` executes an iterative quality evaluation loop: \*\*Parse Criteria $\\rightarrow$ Synthesize Tests $\\rightarrow$ Execute $\\rightarrow$ Evaluate Assertions $\\rightarrow$ Certify\*\*.



&#x20;                   ┌────────────────────────┐

&#x20;                   │ Acceptance Criteria    │

&#x20;                   └───────────┬────────────┘

&#x20;                               │

&#x20;                               ▼

┌──────────────────┐    ┌────────────────────────┐    ┌──────────────────┐

│ Quality Clearance│ ◄──┤ Synthesize Test Suite  ├──► │ Sandboxed Harness│

└──────────────────┘    └───────────┬────────────┘    └──────────────────┘

│

▼

┌────────────────────────┐

│ Assertion \& Coverage   │

└───────────┬────────────┘





\### Execution Loop Stages

1\. \*\*Parse Criteria:\*\* Ingest User Stories, Given-When-Then criteria from `UGOS\_215`, or code implementations from `UGOS\_211`.

2\. \*\*Synthesize Tests:\*\* Generate test scripts covering positive cases, boundary limits, negative inputs, and concurrent calls.

3\. \*\*Execute:\*\* Dispatch test harnesses to `UGOS\_100\_Execution\_Engine` inside isolated $L\_4$ execution sandboxes.

4\. \*\*Evaluate Assertions:\*\* Validate outputs against assertion trees, capturing performance latencies, stack traces, and unhandled exceptions.

5\. \*\*Certify:\*\* Compute final quality clearance score; pass cleared artifacts to deployment pipelines or return regression reports to `UGOS\_211`.



\---



\## 4. Input \& Output Interface Schemas



\### 4.1 Ingestion Schema: QA Evaluation Request (`QAEvaluationPayload`)



```json

{

&#x20; "$schema": "\[https://ugos.dev/schemas/v1/qa\_evaluation\_payload.json](https://ugos.dev/schemas/v1/qa\_evaluation\_payload.json)",

&#x20; "evaluation\_id": "qa\_eval\_991823",

&#x20; "timestamp": "2026-08-10T09:10:00Z",

&#x20; "target\_artifact": {

&#x20;   "type": "PYTHON\_MODULE",

&#x20;   "source\_ref": "mem://workspace/ugos\_core/rate\_limiter.py",

&#x20;   "spec\_ref": "mem://specs/US\_01\_rate\_limiting.json"

&#x20; },

&#x20; "test\_types\_required": \["UNIT", "BOUNDARY", "MUTATION"],

&#x20; "min\_coverage\_pct": 90.0

}

4.2 Output Schema: QA Certification Report (QACertificationReport)

JSON

{

&#x20; "$schema": "\[https://ugos.dev/schemas/v1/qa\_certification\_report.json](https://ugos.dev/schemas/v1/qa\_certification\_report.json)",

&#x20; "report\_id": "rep\_qa\_004912",

&#x20; "evaluation\_ref": "qa\_eval\_991823",

&#x20; "certification\_status": "PASSED",

&#x20; "metrics": {

&#x20;   "total\_tests\_run": 42,

&#x20;   "tests\_passed": 42,

&#x20;   "tests\_failed": 0,

&#x20;   "line\_coverage\_pct": 96.4,

&#x20;   "mutation\_score\_pct": 91.2

&#x20; },

&#x20; "fuzz\_test\_summary": {

&#x20;   "malformed\_payloads\_injected": 1000,

&#x20;   "unhandled\_exceptions": 0

&#x20; },

&#x20; "clearance\_granted": true

}

5\. System Interoperability

UGOS\_100\_Execution\_Engine Interoperability: Spawn sandboxed test environments to execute test suites securely without side effects.



UGOS\_108\_Evaluation\_Engine Interoperability: Supply test metrics and assertion records to calculate overall task completion scores.



UGOS\_211\_Software\_Engineer\_Agent Interoperability: Return detailed regression reports and failing stack traces when code fails QA checks.



6\. Safety Guardrails \& Operational Constraints

\[!CAUTION]

Independent Verification Rule: UGOS\_216 must generate its own test cases independently of those written by UGOS\_211. Re-using developer test cases as the sole QA standard is strictly prohibited.



Sandbox Enclosure: All test execution must occur inside non-root, ephemeral container environments with CPU, RAM, and disk execution caps.



Zero-Suppression Policy: Failing assertions must never be silenced, ignored, or bypassed automatically; every failure requires resolution or explicit operator override.

