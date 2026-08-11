\# UGOS\_701\_REST\_API\_Specification.md



\*\*Module:\*\* `10\_SDK`  

\*\*Specification Version:\*\* `1.0.0`  

\*\*File Reference:\*\* `UGOS\_701`  

\*\*Target Engine Interface:\*\* `UGOS\_100\_Execution\_Engine`, `UGOS\_105\_Orchestration\_Engine`, `UGOS\_106\_Communication\_Engine`, `UGOS\_401\_Zero\_Trust\_Model`  

\*\*Status:\*\* `ACTIVE SPECIFICATION`



\---



\## 1. Module Overview \& Functional Role



The \*\*REST API Specification (`UGOS\_701`)\*\* defines the external HTTP/REST, Server-Sent Events (SSE), and WebSocket gateway contracts, OpenAPI 3.1 endpoint definitions, authentication header bindings, rate-limiting policies, and error payload standards for UGOS v1.0 clusters.



Serving as the primary external integration surface for web dashboards, third-party software, mobile SDKs, and developer tools (including `UGOS\_700` CLI), `UGOS\_701` exposes full programmatic control over agent lifecycles, workflow execution DAGs, memory queries, and cluster telemetry streaming.



\### Primary Objectives

1\. \*\*OpenAPI 3.1 Strict Compliance:\*\* Maintain machine-readable, fully validated REST schemas for all endpoints and data transfer objects (DTOs).

2\. \*\*Real-Time Telemetry Streaming:\*\* Provide low-latency Server-Sent Events (SSE) and WebSocket streams for real-time log tailing, workflow FSM state updates, and agent status metrics.

3\. \*\*Zero-Trust Header Integration:\*\* Mandate HTTP Bearer SPIFFE/JWT tokens and asymmetric request signatures on every incoming API request (`UGOS\_401`).

4\. \*\*Standardized RFC 7807 Error Handling:\*\* Return unified "Problem Details for HTTP APIs" JSON objects for all client ($4xx$) and server ($5xx$) failure states.



\---



\## 2. API Endpoint Taxonomy \& Routing Hierarchy



All REST API endpoints are version-prefixed under `/v1/` and divided into five primary functional controllers:



/v1├── /health                   \[GET] System and engine health checks├── /agents                   \[GET, POST] List registered agents / invoke agent│    └── /{agent\_id}          \[GET] Inspect agent state, capabilities \& logs├── /workflows                \[POST] Submit DAG workflow execution payload│    └── /{execution\_id}      \[GET, DELETE] Query workflow status or request cancellation│    └── /{execution\_id}/stream \[GET - SSE] Stream real-time node execution events├── /memory                   \[POST] Query $M\_1$-$M\_3$ memory stores via hybrid search└── /auth                     \[POST] Exchange credentials for short-lived identity tokens

\### Core REST Endpoint Summary



| Endpoint Route | HTTP Method | Description | Security Level Required |

| :--- | :---: | :--- | :---: |

| `/v1/health` | `GET` | Cluster engine readiness and liveness probes | $L\_0$ |

| `/v1/auth/token` | `POST` | Authenticate agent/operator identity and issue JWT | $L\_0$ |

| `/v1/agents` | `GET` | List active agent manifests, health, and status | $L\_1$ |

| `/v1/agents/{id}/invoke` | `POST` | Synchronously invoke a target agent action | $L\_1$ |

| `/v1/workflows` | `POST` | Asynchronously register and launch a DAG workflow | $L\_2$ |

| `/v1/workflows/{id}` | `GET` | Retrieve workflow execution state, completed nodes \& outputs | $L\_1$ |

| `/v1/workflows/{id}/stream`| `GET` | Server-Sent Events (SSE) stream of real-time execution logs | $L\_1$ |

| `/v1/memory/query` | `POST` | Execute hybrid vector/BM25/graph queries against memory | $L\_1$ |



\---



\## 3. Headers, Authentication \& Real-Time Event Streaming



\### Required HTTP Headers

\* \*\*`Authorization`\*\*: `Bearer <spiffe\_jwt\_token>` \*(Mandatory for $L\_1$+ endpoints)\*

\* \*\*`X-UGOS-Tenant-ID`\*\*: Tenant isolation context key (e.g., `tenant\_core\_prod`)

\* \*\*`X-UGOS-Signature`\*\*: SHA-256 HMAC or asymmetric signature of HTTP request body

\* \*\*`Content-Type`\*\*: `application/json` (or `text/event-stream` for SSE streaming routes)



\### SSE Real-Time Event Stream Format

When connecting to `/v1/workflows/{execution\_id}/stream`:

```text

event: NODE\_COMPLETED

data: {"node\_id": "step\_01\_scan", "status": "SUCCESS", "elapsed\_ms": 142}



event: NODE\_STARTED

data: {"node\_id": "step\_02\_patch", "assigned\_agent": "UGOS\_211"}

4\. Input \& Output Interface Schemas4.1 Ingestion Schema: Workflow Submission Request (WorkflowSubmissionDTO)JSON{

&#x20; "$schema": "\[https://ugos.dev/schemas/v1/workflow\_submission\_dto.json](https://ugos.dev/schemas/v1/workflow\_submission\_dto.json)",

&#x20; "workflow\_id": "wf\_def\_500\_patching",

&#x20; "execution\_policy": {

&#x20;   "max\_execution\_time\_seconds": 1800,

&#x20;   "concurrency\_limit": 5

&#x20; },

&#x20; "parameters": {

&#x20;   "target\_repository": "mem://workspace/ugos\_core/",

&#x20;   "cve\_id": "CVE-2026-49201"

&#x20; }

}

4.2 Output Schema: RFC 7807 Error Response (ProblemDetailsDTO)JSON{

&#x20; "type": "\[https://ugos.dev/errors/PRIVILEGE\_INSUFFICIENT](https://ugos.dev/errors/PRIVILEGE\_INSUFFICIENT)",

&#x20; "title": "Forbidden",

&#x20; "status": 403,

&#x20; "detail": "Agent UGOS\_211 (L2) requested write access to L4 Guarded resource without elevation approval.",

&#x20; "instance": "/v1/workflows/wf\_exec\_902811a",

&#x20; "error\_code": "UGOS\_SEC\_403\_012",

&#x20; "timestamp": "2026-08-11T08:32:00Z"

}

5\. System InteroperabilityUGOS\_106\_Communication\_Engine Interoperability: Route HTTP/REST REST API requests internally to gRPC/IPC execution handlers.UGOS\_401\_Zero\_Trust\_Model Interoperability: Validate all inbound HTTP Authorization headers and cryptographic signatures before routing requests to core engines.UGOS\_700\_CLI\_Interface Interoperability: Serve as the underlying HTTP endpoint protocol layer consumed by CLI commands.6. Safety Guardrails \& Operational Constraints\[!CAUTION]Payload Size \& Rate Limiting Enforcement: HTTP POST request payloads are hard-capped at $10\\text{ MB}$. Requests exceeding rate limits ($1000\\text{ req/min}$ per tenant by default) return HTTP $429\\text{ Too Many Requests}$ with an explicit Retry-After header.CORS Safety Policy: Cross-Origin Resource Sharing (CORS) is disabled by default; when enabled, origin wildcards (\*) are strictly prohibited in production mode.Error Detail Redaction: Production API environments must redact internal stack traces from ProblemDetailsDTO payloads, logging full traces exclusively to $M\_2$ Episodic Memory and UGOS\_403 audit logs.

