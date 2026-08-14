# UGOS_214_Project_Manager_Agent.md

**Module:** `04_Agents`

**Specification Version:** `1.0.0`

**File Reference:** `UGOS_214`

**Target Engine Interface:** `UGOS_102_Planning_Engine`, `UGOS_104_Task_Router`, `UGOS_105_Orchestration_Engine`

**Status:** `ACTIVE SPECIFICATION`

---

## 1. Module Overview & System Role

The **Project Manager Agent (`UGOS_214`)** is a Tier 3 Specialist Agent responsible for high-level Directed Acyclic Graph (DAG) progress tracking, subtask decomposition monitoring, resource allocation optimization, milestone reporting, and workflow dependency resolution across multi-agent execution pipelines.

While `UGOS_105_Orchestration_Engine` handles low-level process thread scheduling, `UGOS_214` operates at the semantic project level—translating macro objectives into operational task structures, tracking execution velocity, detecting dependency bottlenecks, and compiling progress summaries for system operators.

### Primary Objectives

1. **Dynamic Task Decomposition & DAG Mapping:** Convert high-level goals into executable, dependency-aware DAG subtask nodes.

2. **Multi-Agent Milestone Tracking:** Monitor active subtask states across specialized agents (`UGOS_210`–`UGOS_217`), updating project completion matrices in real time.

3. **Bottleneck & Critical Path Analysis:** Compute critical path latencies, identify blocked subtasks, and trigger re-routing or resource re-allocation via `UGOS_104_Task_Router`.

4. **Automated Status Synthesis & Reporting:** Generate structured sprint/milestone summaries, burndown metrics, and risk projections.

---

## 2. Core Capabilities & Task Matrix

| Domain | Capability | Input Vector | Target Output / Action |

| :--- | :--- | :--- | :--- |

| **Task Decomposition** | Goal-to-DAG Transformation | User Prompt / PRD | Multi-Node Execution Graph |

| **Progress Tracking** | Real-Time State Ingestion | Agent State Telemetry Streams | Updated Project State Vector |

| **Dependency Management** | Critical Path Optimization | Task Topology + Runtime Latency | Re-ordered / Parallelized Subtasks |

| **Resource Scheduling** | Load Balancing Allocation | Agent Workload Capacities | Optimal Agent Dispatch Directives |

| **Project Reporting** | Status Summary Synthesis | Completed Artifact Logs | Markdown Progress Digest |

---

## 3. Agent Architecture & Execution Loop

`UGOS_214` operates on a continuous management loop: **Decompose $\rightarrow$ Schedule $\rightarrow$ Monitor $\rightarrow$ Rebalance $\rightarrow$ Report**.

                    ┌────────────────────────┐

                    │   Macro Objective/PRD  │

                    └───────────┬────────────┘

                                │

                                ▼

┌──────────────────┐    ┌────────────────────────┐    ┌──────────────────┐│ Generate Report  │ ◄──┤ Decompose & Map DAG    ├──► │ Dispatch Tasks   │└──────────────────┘    └───────────┬────────────┘    └──────────────────┘│▼┌────────────────────────┐│  Monitor & Rebalance   │└───────────┬────────────┘

### Execution Loop Stages

1. **Decompose:** Ingest user objectives or requirements documents and break them down into concrete subtasks with explicit dependencies.

2. **Schedule:** Map subtasks to optimal specialist agents based on capability matrices and current node load scores.

3. **Monitor:** Intercept real-time event signals from `UGOS_105_Orchestration_Engine` to track subtask state transitions (`PENDING` $\rightarrow$ `RUNNING` $\rightarrow$ `COMPLETED`).

4. **Rebalance:** Detect stalled subtasks or execution timeouts, re-assigning subgraphs or triggering fallback routines.

5. **Report:** Synthesize project velocity metrics, completion percentages, and milestone summaries into human-readable and machine-parseable outputs.

---

## 4. Input & Output Interface Schemas

### 4.1 Ingestion Schema: Project Plan Request (`ProjectPlanPayload`)

```json

{

  "$schema": "[https://ugos.dev/schemas/v1/project_plan_payload.json](https://ugos.dev/schemas/v1/project_plan_payload.json)",

  "project_id": "prj_pm_901823",

  "timestamp": "2026-08-10T09:00:00Z",

  "macro_objective": "Build and deploy a secure REST API service for user authentication.",

  "subtasks": [

    {

      "id": "task_01",

      "name": "Research OAuth2 standards",

      "target_agent": "UGOS_210",

      "dependencies": []

    },

    {

      "id": "task_02",

      "name": "Generate API implementation code",

      "target_agent": "UGOS_211",

      "dependencies": ["task_01"]

    },

    {

      "id": "task_03",

      "name": "Audit source code for security flaws",

      "target_agent": "UGOS_212",

      "dependencies": ["task_02"]

    }

  ],

  "sla_deadline": "2026-08-10T12:00:00Z"

}
```

4.2 Output Schema: Project Status Directive (ProjectStatusDirective)JSON{

  "$schema": "[https://ugos.dev/schemas/v1/project_status_directive.json](https://ugos.dev/schemas/v1/project_status_directive.json)",

  "directive_id": "dir_pm_009812",

  "project_ref": "prj_pm_901823",

  "overall_progress_pct": 66.7,

  "completed_subtasks": ["task_01", "task_02"],

  "active_subtasks": ["task_03"],

  "critical_path_latency_ms": 14200,

  "health_status": "ON_TRACK",

  "next_milestone": "Security audit completion by UGOS_212"

}

5. System InteroperabilityUGOS_102_Planning_Engine Interoperability: Validate DAG topologies for cycles ($G=(V,E)$) before submitting task graphs to the execution bus.UGOS_104_Task_Router Interoperability: Query real-time agent availability and dispatch decomposed subtasks to target agent queues.UGOS_105_Orchestration_Engine Interoperability: Receive subtask state change events and persist high-level project milestones in system memory.6. Safety Guardrails & Operational Constraints[!CAUTION]No Direct Tool Execution: UGOS_214 is strictly an administrative and managerial agent. It cannot directly mutate codebases, execute shell scripts, or alter network infrastructure; all actions must be delegated to specialized Tier 2 agents.Cycle Interception: Any generated task decomposition graph containing circular dependencies must be halted and rejected prior to dispatch.SLA Threshold Alerts: If projected completion time exceeds the allocated sla_deadline, UGOS_214 must immediately raise an alert event to UGOS_105_Orchestration_Engine.
