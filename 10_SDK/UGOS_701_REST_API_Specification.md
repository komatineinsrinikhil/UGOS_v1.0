# UGOS_701_REST_API_Specification.md

**Module:** `10_SDK`

**Specification Version:** `1.0.0`

**File Reference:** `UGOS_701`

**Target Engine Interface:** `UGOS_100_Execution_Engine`, `UGOS_105_Orchestration_Engine`, `UGOS_106_Communication_Engine`, `UGOS_401_Zero_Trust_Model`

**Status:** `ACTIVE SPECIFICATION`

---

## 1. Module Overview & Functional Role

The **REST API Specification (`UGOS_701`)** defines the external HTTP/REST, Server-Sent Events (SSE), and WebSocket gateway contracts, OpenAPI 3.1 endpoint definitions, authentication header bindings, rate-limiting policies, and error payload standards for UGOS v1.0 clusters.

Serving as the primary external integration surface for web dashboards, third-party software, mobile SDKs, and developer tools (including `UGOS_700` CLI), `UGOS_701` exposes full programmatic control over agent lifecycles, workflow execution DAGs, memory queries, and cluster telemetry streaming.

### Primary Objectives

1. **OpenAPI 3.1 Strict Compliance:** Maintain machine-readable, fully validated REST schemas for all endpoints and data transfer objects (DTOs).

2. **Real-Time Telemetry Streaming:** Provide low-latency Server-Sent Events (SSE) and WebSocket streams for real-time log tailing, workflow FSM state updates, and agent status metrics.

3. **Zero-Trust Header Integration:** Mandate HTTP Bearer SPIFFE/JWT tokens and asymmetric request signatures on every incoming API request (`UGOS_401`).

4. **Standardized RFC 7807 Error Handling:** Return unified "Problem Details for HTTP APIs" JSON objects for all client ($4xx$) and server ($5xx$) failure states.

---

## 2. API Endpoint Taxonomy & Routing Hierarchy

All REST API endpoints are version-prefixed under `/v1/` and divided into five primary functional controllers:

/v1├── /health                   [GET] System and engine health checks├── /agents                   [GET, POST] List registered agents / invoke agent│    └── /{agent_id}          [GET] Inspect agent state, capabilities & logs├── /workflows                [POST] Submit DAG workflow execution payload│    └── /{execution_id}      [GET, DELETE] Query workflow status or request cancellation│    └── /{execution_id}/stream [GET - SSE] Stream real-time node execution events├── /memory                   [POST] Query $M_1$-$M_3$ memory stores via hybrid search└── /auth                     [POST] Exchange credentials for short-lived identity tokens

### Core REST Endpoint Summary

| Endpoint Route | HTTP Method | Description | Security Level Required |

| :--- | :---: | :--- | :---: |

| `/v1/health` | `GET` | Cluster engine readiness and liveness probes | $L_0$ |

| `/v1/auth/token` | `POST` | Authenticate agent/operator identity and issue JWT | $L_0$ |

| `/v1/agents` | `GET` | List active agent manifests, health, and status | $L_1$ |

| `/v1/agents/{id}/invoke` | `POST` | Synchronously invoke a target agent action | $L_1$ |

| `/v1/workflows` | `POST` | Asynchronously register and launch a DAG workflow | $L_2$ |

| `/v1/workflows/{id}` | `GET` | Retrieve workflow execution state, completed nodes & outputs | $L_1$ |

| `/v1/workflows/{id}/stream`| `GET` | Server-Sent Events (SSE) stream of real-time execution logs | $L_1$ |

| `/v1/memory/query` | `POST` | Execute hybrid vector/BM25/graph queries against memory | $L_1$ |

---

## 3. Headers, Authentication & Real-Time Event Streaming

### Required HTTP Headers

* **`Authorization`**: `Bearer <spiffe_jwt_token>` *(Mandatory for $L_1$+ endpoints)*

* **`X-UGOS-Tenant-ID`**: Tenant isolation context key (e.g., `tenant_core_prod`)

* **`X-UGOS-Signature`**: SHA-256 HMAC or asymmetric signature of HTTP request body

* **`Content-Type`**: `application/json` (or `text/event-stream` for SSE streaming routes)

### SSE Real-Time Event Stream Format

When connecting to `/v1/workflows/{execution_id}/stream`:

```text

event: NODE_COMPLETED

data: {"node_id": "step_01_scan", "status": "SUCCESS", "elapsed_ms": 142}
```

event: NODE_STARTED

data: {"node_id": "step_02_patch", "assigned_agent": "UGOS_211"}

4. Input & Output Interface Schemas4.1 Ingestion Schema: Workflow Submission Request (WorkflowSubmissionDTO)JSON{

  "$schema": "[https://ugos.dev/schemas/v1/workflow_submission_dto.json](https://ugos.dev/schemas/v1/workflow_submission_dto.json)",

  "workflow_id": "wf_def_500_patching",

  "execution_policy": {

    "max_execution_time_seconds": 1800,

    "concurrency_limit": 5

  },

  "parameters": {

    "target_repository": "mem://workspace/ugos_core/",

    "cve_id": "CVE-2026-49201"

  }

}

4.2 Output Schema: RFC 7807 Error Response (ProblemDetailsDTO)JSON{

  "type": "[https://ugos.dev/errors/PRIVILEGE_INSUFFICIENT](https://ugos.dev/errors/PRIVILEGE_INSUFFICIENT)",

  "title": "Forbidden",

  "status": 403,

  "detail": "Agent UGOS_211 (L2) requested write access to L4 Guarded resource without elevation approval.",

  "instance": "/v1/workflows/wf_exec_902811a",

  "error_code": "UGOS_SEC_403_012",

  "timestamp": "2026-08-11T08:32:00Z"

}

5. System InteroperabilityUGOS_106_Communication_Engine Interoperability: Route HTTP/REST REST API requests internally to gRPC/IPC execution handlers.UGOS_401_Zero_Trust_Model Interoperability: Validate all inbound HTTP Authorization headers and cryptographic signatures before routing requests to core engines.UGOS_700_CLI_Interface Interoperability: Serve as the underlying HTTP endpoint protocol layer consumed by CLI commands.6. Safety Guardrails & Operational Constraints[!CAUTION]Payload Size & Rate Limiting Enforcement: HTTP POST request payloads are hard-capped at $10\text{ MB}$. Requests exceeding rate limits ($1000\text{ req/min}$ per tenant by default) return HTTP $429\text{ Too Many Requests}$ with an explicit Retry-After header.CORS Safety Policy: Cross-Origin Resource Sharing (CORS) is disabled by default; when enabled, origin wildcards (*) are strictly prohibited in production mode.Error Detail Redaction: Production API environments must redact internal stack traces from ProblemDetailsDTO payloads, logging full traces exclusively to $M_2$ Episodic Memory and UGOS_403 audit logs.
