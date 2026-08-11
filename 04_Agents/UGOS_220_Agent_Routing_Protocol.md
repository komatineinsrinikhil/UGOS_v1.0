\# UGOS\_220\_Agent\_Routing\_Protocol.md



\*\*Module:\*\* `04\_Agents`  

\*\*Specification Version:\*\* `1.0.0`  

\*\*File Reference:\*\* `UGOS\_220`  

\*\*Target Engine Interface:\*\* `UGOS\_104\_Task\_Router`, `UGOS\_105\_Orchestration\_Engine`, `UGOS\_106\_Communication\_Engine`  

\*\*Status:\*\* `ACTIVE SPECIFICATION`



\---



\## 1. Module Overview \& System Role



The \*\*Agent Routing Protocol (`UGOS\_220`)\*\* defines the inter-agent delegation standards, message transport formats, context handoff structures, and peer-to-peer message routing rules across the UGOS ecosystem.



While `UGOS\_104\_Task\_Router` executes global scheduling, `UGOS\_220` governs how autonomous agents directly communicate, transfer subtask workloads, negotiate context boundaries, and dispatch peer requests without incurring full orchestration overhead.



\### Primary Objectives

1\. \*\*Standardized Delegation Messaging:\*\* Define a strict JSON framing schema for inter-agent delegation requests, responses, and signaling events.

2\. \*\*Context Handoff Optimization:\*\* Provide lightweight memory referencing pointers (`mem://`) to pass working state between agents without inflating context token windows.

3\. \*\*Routing Discovery \& Capability Matching:\*\* Standardize the protocol for agents to query peer availability and capability matrices.

4\. \*\*Loop \& Cascade Prevention:\*\* Enforce maximum call-depth limits and loop-detection signatures on all peer-delegated routing chains.



\---



\## 2. Core Capabilities \& Task Matrix



| Domain | Capability | Input Vector | Target Output / Action |

| :--- | :--- | :--- | :--- |

| \*\*Peer Dispatch\*\* | Direct Agent-to-Agent Delegation | Handoff Context + Target Agent | Formatted Inter-Agent Frame |

| \*\*Context Compression\*\* | Memory Pointer Serialization | Full Active Context | Lightweight Snapshot URI |

| \*\*Capability Lookup\*\* | Peer Matrix Query | Capability Tag (e.g., `SAST\_SCAN`) | Best Matching Agent Endpoint |

| \*\*Loop Interception\*\* | Hop-Count Tracking | Incoming Routing Header | Accept / Reject Routing Decision |



\---



\## 3. Protocol Architecture \& Routing Sequence



Inter-agent communication follows an asynchronous handshake sequence: \*\*Discover $\\rightarrow$ Frame $\\rightarrow$ Dispatch $\\rightarrow$ Acknowledge $\\rightarrow$ Resolve\*\*.



┌──────────────────┐    1. Peer Query / Discovery    ┌────────────────────────┐│  Origin Agent    ├────────────────────────────────►│  UGOS\_104 Task Router  │└────────┬─────────┘                                 └───────────┬────────────┘│                                                       ││ 2. Direct Delegation Frame (mem:// ref)               │ 1b. Endpoint Match▼                                                       ▼┌─────────────────────────────────────────────────────────────────────────────┐│                            Target Agent Endpoint                            │└────────┬────────────────────────────────────────────────────────────────────┘││ 3. Processing \& Acknowledgment Payload▼┌──────────────────┐│  Origin Agent    │└──────────────────┘

\### Protocol Execution Steps

1\. \*\*Discover:\*\* The originating agent queries `UGOS\_104\_Task\_Router` for an active agent matching required capabilities (e.g., `UGOS\_212` for security scanning).

2\. \*\*Frame:\*\* Originating agent packages the delegation request using the canonical `AgentDelegationFrame` schema.

3\. \*\*Dispatch:\*\* The message is transmitted asynchronously via gRPC / Redis pub-sub channels to the target agent queue.

4\. \*\*Acknowledge:\*\* Target agent accepts the payload, verifies its privilege bounds, and returns a transaction acknowledgement (`ACK`).

5\. \*\*Resolve:\*\* Upon task completion, the target agent posts the result back to the origin agent's memory callback address.



\---



\## 4. Input \& Output Interface Schemas



\### 4.1 Ingestion Schema: Inter-Agent Delegation Frame (`AgentDelegationFrame`)



```json

{

&#x20; "$schema": "\[https://ugos.dev/schemas/v1/agent\_delegation\_frame.json](https://ugos.dev/schemas/v1/agent\_delegation\_frame.json)",

&#x20; "frame\_id": "frm\_route\_902811",

&#x20; "timestamp": "2026-08-10T08:52:00Z",

&#x20; "routing\_header": {

&#x20;   "sender\_agent\_id": "UGOS\_211",

&#x20;   "recipient\_agent\_id": "UGOS\_216",

&#x20;   "hop\_count": 1,

&#x20;   "max\_hops": 3,

&#x20;   "correlation\_id": "corr\_task\_882019"

&#x20; },

&#x20; "payload\_reference": {

&#x20;   "type": "MEMORY\_POINTER",

&#x20;   "context\_uri": "mem://snapshots/ctx\_swe\_task\_882019.json",

&#x20;   "security\_level": "L4\_GUARDED"

&#x20; },

&#x20; "callback\_address": "mem://channels/responses/UGOS\_211\_callback"

}

4.2 Output Schema: Routing Acknowledgment Frame (RoutingAckFrame)JSON{

&#x20; "$schema": "\[https://ugos.dev/schemas/v1/routing\_ack\_frame.json](https://ugos.dev/schemas/v1/routing\_ack\_frame.json)",

&#x20; "ack\_id": "ack\_route\_001923",

&#x20; "frame\_ref": "frm\_route\_902811",

&#x20; "status": "ACCEPTED",

&#x20; "estimated\_processing\_ms": 1200,

&#x20; "queue\_position": 0

}

5\. System InteroperabilityUGOS\_104\_Task\_Router Interoperability: Provide endpoint discovery tables and intercept invalid or out-of-bounds peer delegation requests.UGOS\_105\_Orchestration\_Engine Interoperability: Log routing headers into persistent execution traces to maintain global visibility over subtask trees.UGOS\_106\_Communication\_Engine Interoperability: Transport delegation frames over low-latency IPC, gRPC, or WebSockets depending on execution topology.6. Safety Guardrails \& Operational Constraints\[!CAUTION]Hop-Count Interception: Every routing header must increment hop\_count. If hop\_count > max\_hops (default: 3), the frame is immediately dropped and flagged as a potential infinite delegation loop.Privilege Non-Escalation: A delegating agent cannot request a target agent to perform operations requiring a higher security clearance ($L\_x$) than the delegating agent itself possesses.Memory Isolation: Inter-agent context URIs (context\_uri) must be scoped strictly to the current session ID to prevent unauthorized access across tenant boundaries.

