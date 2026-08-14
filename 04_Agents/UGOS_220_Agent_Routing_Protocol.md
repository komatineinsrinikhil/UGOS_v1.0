# UGOS_220_Agent_Routing_Protocol.md

**Module:** `04_Agents`

**Specification Version:** `1.0.0`

**File Reference:** `UGOS_220`

**Target Engine Interface:** `UGOS_104_Task_Router`, `UGOS_105_Orchestration_Engine`, `UGOS_106_Communication_Engine`

**Status:** `ACTIVE SPECIFICATION`

---

## 1. Module Overview & System Role

The **Agent Routing Protocol (`UGOS_220`)** defines the inter-agent delegation standards, message transport formats, context handoff structures, and peer-to-peer message routing rules across the UGOS ecosystem.

While `UGOS_104_Task_Router` executes global scheduling, `UGOS_220` governs how autonomous agents directly communicate, transfer subtask workloads, negotiate context boundaries, and dispatch peer requests without incurring full orchestration overhead.

### Primary Objectives

1. **Standardized Delegation Messaging:** Define a strict JSON framing schema for inter-agent delegation requests, responses, and signaling events.

2. **Context Handoff Optimization:** Provide lightweight memory referencing pointers (`mem://`) to pass working state between agents without inflating context token windows.

3. **Routing Discovery & Capability Matching:** Standardize the protocol for agents to query peer availability and capability matrices.

4. **Loop & Cascade Prevention:** Enforce maximum call-depth limits and loop-detection signatures on all peer-delegated routing chains.

---

## 2. Core Capabilities & Task Matrix

| Domain | Capability | Input Vector | Target Output / Action |

| :--- | :--- | :--- | :--- |

| **Peer Dispatch** | Direct Agent-to-Agent Delegation | Handoff Context + Target Agent | Formatted Inter-Agent Frame |

| **Context Compression** | Memory Pointer Serialization | Full Active Context | Lightweight Snapshot URI |

| **Capability Lookup** | Peer Matrix Query | Capability Tag (e.g., `SAST_SCAN`) | Best Matching Agent Endpoint |

| **Loop Interception** | Hop-Count Tracking | Incoming Routing Header | Accept / Reject Routing Decision |

---

## 3. Protocol Architecture & Routing Sequence

Inter-agent communication follows an asynchronous handshake sequence: **Discover $\rightarrow$ Frame $\rightarrow$ Dispatch $\rightarrow$ Acknowledge $\rightarrow$ Resolve**.

┌──────────────────┐    1. Peer Query / Discovery    ┌────────────────────────┐│  Origin Agent    ├────────────────────────────────►│  UGOS_104 Task Router  │└────────┬─────────┘                                 └───────────┬────────────┘│                                                       ││ 2. Direct Delegation Frame (mem:// ref)               │ 1b. Endpoint Match▼                                                       ▼┌─────────────────────────────────────────────────────────────────────────────┐│                            Target Agent Endpoint                            │└────────┬────────────────────────────────────────────────────────────────────┘││ 3. Processing & Acknowledgment Payload▼┌──────────────────┐│  Origin Agent    │└──────────────────┘

### Protocol Execution Steps

1. **Discover:** The originating agent queries `UGOS_104_Task_Router` for an active agent matching required capabilities (e.g., `UGOS_212` for security scanning).

2. **Frame:** Originating agent packages the delegation request using the canonical `AgentDelegationFrame` schema.

3. **Dispatch:** The message is transmitted asynchronously via gRPC / Redis pub-sub channels to the target agent queue.

4. **Acknowledge:** Target agent accepts the payload, verifies its privilege bounds, and returns a transaction acknowledgement (`ACK`).

5. **Resolve:** Upon task completion, the target agent posts the result back to the origin agent's memory callback address.

---

## 4. Input & Output Interface Schemas

### 4.1 Ingestion Schema: Inter-Agent Delegation Frame (`AgentDelegationFrame`)

```json

{

  "$schema": "[https://ugos.dev/schemas/v1/agent_delegation_frame.json](https://ugos.dev/schemas/v1/agent_delegation_frame.json)",

  "frame_id": "frm_route_902811",

  "timestamp": "2026-08-10T08:52:00Z",

  "routing_header": {

    "sender_agent_id": "UGOS_211",

    "recipient_agent_id": "UGOS_216",

    "hop_count": 1,

    "max_hops": 3,

    "correlation_id": "corr_task_882019"

  },

  "payload_reference": {

    "type": "MEMORY_POINTER",

    "context_uri": "mem://snapshots/ctx_swe_task_882019.json",

    "security_level": "L4_GUARDED"

  },

  "callback_address": "mem://channels/responses/UGOS_211_callback"

}
```

4.2 Output Schema: Routing Acknowledgment Frame (RoutingAckFrame)JSON{

  "$schema": "[https://ugos.dev/schemas/v1/routing_ack_frame.json](https://ugos.dev/schemas/v1/routing_ack_frame.json)",

  "ack_id": "ack_route_001923",

  "frame_ref": "frm_route_902811",

  "status": "ACCEPTED",

  "estimated_processing_ms": 1200,

  "queue_position": 0

}

5. System InteroperabilityUGOS_104_Task_Router Interoperability: Provide endpoint discovery tables and intercept invalid or out-of-bounds peer delegation requests.UGOS_105_Orchestration_Engine Interoperability: Log routing headers into persistent execution traces to maintain global visibility over subtask trees.UGOS_106_Communication_Engine Interoperability: Transport delegation frames over low-latency IPC, gRPC, or WebSockets depending on execution topology.6. Safety Guardrails & Operational Constraints[!CAUTION]Hop-Count Interception: Every routing header must increment hop_count. If hop_count > max_hops (default: 3), the frame is immediately dropped and flagged as a potential infinite delegation loop.Privilege Non-Escalation: A delegating agent cannot request a target agent to perform operations requiring a higher security clearance ($L_x$) than the delegating agent itself possesses.Memory Isolation: Inter-agent context URIs (context_uri) must be scoped strictly to the current session ID to prevent unauthorized access across tenant boundaries.
