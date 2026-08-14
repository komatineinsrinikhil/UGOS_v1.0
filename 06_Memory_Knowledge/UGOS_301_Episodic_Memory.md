# UGOS_301_Episodic_Memory.md

**Module:** `06_Memory_Knowledge`

**Specification Version:** `1.0.0`

**File Reference:** `UGOS_301`

**Target Engine Interface:** `UGOS_100_Execution_Engine`, `UGOS_105_Orchestration_Engine`, `UGOS_108_Evaluation_Engine`

**Status:** `ACTIVE SPECIFICATION`

---

## 1. Module Overview & Functional Role

The **Episodic Memory Specification (`UGOS_301`)** defines the time-series event storage, execution history indexing, session trace logging, and reflective retrieval mechanisms for $M_2$ Episodic Memory in the UGOS ecosystem.

While $M_1$ Working Memory handles active prompt context, $M_2$ Episodic Memory records chronological agent experiences, tool call results, error stack traces, user interaction histories, and DAG subtask state transitions. This allows agents to reflect on prior mistakes, maintain cross-session continuity, and reconstruct precise execution timelines.

### Primary Objectives

1. **Chronological Trace Persistence:** Record structured event logs for every agent action, tool invocation, and state transition across task lifecycles.

2. **Sub-Second Temporal & Event Queries:** Provide low-latency querying ($<20\text{ms}$) by session ID, time window, agent ID, or execution status.

3. **Reflective Summarization & Experience Retrieval:** Enable agents to query past task outcomes (e.g., "How was a similar refactoring bug resolved in prior sessions?") to inform current reasoning loops.

4. **Automated Lifecycle & Compaction:** Consolidate granular step-by-step execution logs into high-level episodic summaries to prevent storage bloat.

---

## 2. Core Architecture & Storage Topology

$M_2$ Episodic Memory is stored in a high-throughput time-series event store (e.g., DuckDB / Timescale / Structured Parquet logs) indexed by timestamp, session correlation ID, and agent identity.

┌─────────────────────────────────────────────────────────────┐│                 Incoming Execution Events                   ││      (Agent Actions, Tool Outputs, Error Traces)            │└──────────────────────────────┬──────────────────────────────┘│▼┌─────────────────────────────────────────────────────────────┐│ Temporal Indexer & Structuring Engine ($M_2$ Ingestion)      │└──────────────────────────────┬──────────────────────────────┘│┌──────────────────┴──────────────────┐▼                                     ▼┌───────────────────────┐             ┌───────────────────────┐│ Granular Trace Logs   │             │ Compressed Episodic   ││ (TTL: 7-30 Days)      │             │ Summaries (Permanent) │└───────────────────────┘             └───────────────────────┘

### Key Storage Structures

* **Execution Event Logs:** Granular JSONL / Parquet event streams recording inputs, actions, intermediate reasoning, tool calls, and execution latencies.

* **Session Summaries:** Compressed natural-language and structured summaries generated at task completion, summarizing goals, decisions, failures, and resolution paths.

* **Error & Reflection Signatures:** Fingerprinted error hashes mapped to successful remediation steps for instant lookup during fault recovery loops.

---

## 3. Ingestion & Retrieval Execution Loop

1. **Ingest:** Intercept events from `UGOS_105_Orchestration_Engine` and structured agent outputs during runtime.

2. **Structure:** Append metadata tags (`session_id`, `agent_id`, `workflow_id`, `execution_status`, `error_fingerprint`).

3. **Query / Reconstruct:** Retrieve chronological event sequences or search for past similar experiences based on prompt embedding or tags.

4. **Reflect / Summarize:** Upon workflow completion, synthesize the raw trace into a compressed episodic summary record.

---

## 4. Input & Output Interface Schemas

### 4.1 Ingestion Schema: Episodic Event Log (`EpisodicEventPayload`)

```json

{

  "$schema": "[https://ugos.dev/schemas/v1/episodic_event_payload.json](https://ugos.dev/schemas/v1/episodic_event_payload.json)",

  "event_id": "ep_evt_902811b",

  "timestamp": "2026-08-11T08:05:00Z",

  "session_context": {

    "session_id": "sess_882019",

    "workflow_id": "wf_refactor_901823",

    "agent_id": "UGOS_211"

  },

  "event_type": "TOOL_EXECUTION_COMPLETED",

  "payload": {

    "tool_name": "ast_patch_applier",

    "input_params": {"file": "ugos/net/http_client.py"},

    "output_status": "SUCCESS",

    "execution_time_ms": 142

  },

  "error_fingerprint": null

}
```

4.2 Output Schema: Episodic Experience Query Result (EpisodicQueryResponse)JSON{

  "$schema": "[https://ugos.dev/schemas/v1/episodic_query_response.json](https://ugos.dev/schemas/v1/episodic_query_response.json)",

  "query_id": "ep_q_001923",

  "search_criteria": {

    "agent_id": "UGOS_211",

    "error_fingerprint": "ERR_AST_SYNTAX_PARSER_OOM",

    "limit": 3

  },

  "experiences_found": [

    {

      "session_id": "sess_771020",

      "timestamp": "2026-08-10T08:22:18Z",

      "problem_summary": "AST parser ran out of memory on multi-gigabyte source file.",

      "resolution_applied": "Applied chunked streaming AST parser with 50MB file buffer.",

      "outcome": "SUCCESS"

    }

  ],

  "retrieval_latency_ms": 12.4

}

5. System InteroperabilityUGOS_105_Orchestration_Engine Interoperability: Emit real-time event signals during subtask execution for instant episodic log persistence.UGOS_108_Evaluation_Engine Interoperability: Query historical episodic performance metrics to compute agent success rates and task quality scores.UGOS_213_Data_Analyst_Agent Interoperability: Run high-throughput analytical queries over aggregated $M_2$ time-series logs for trend analysis.6. Safety Guardrails & Operational Constraints[!CAUTION]Tenant & Privilege Isolation: Episodic logs are scoped strictly to the owning tenant and authorization layer ($L_0$–$L_5$). Agents executing low-privilege tasks cannot query episodic memory traces created during high-privilege administrative sessions.Automated Data Scrubbing: Secrets, API tokens, and PII detected in tool logs are scrubbed via regex filters prior to episodic storage.Trace Retention Policy: Uncompressed step-by-step logs are retained for 30 days (configurable), after which they are automatically compacted into high-level session summaries and purged from raw storage.

&#x09;
