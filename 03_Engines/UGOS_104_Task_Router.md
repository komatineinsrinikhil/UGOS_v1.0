# UGOS DOCUMENT METADATA

Document ID: UGOS_104_Task_Router

Version: 1.0.0-DRAFT

Status: APPROVED

Category: Core Engine / Routing

Owner: Core Engineering Architecture Group

Target Audience: Core Engineers, Systems Architects, Multi-Agent Developers

Last Updated: 2026-08-09

---

# UGOS_104: Task Router Specification

## 1. PURPOSE

The Task Router dynamically matches task requirements and DAG steps to appropriate specialist agents based on capability parameters, operational availability, and performance history.

---

## 2. ROUTING SCHEMA & AGENT MATCHING (JSON)

```json

{

  "routing_id": "ROUTE-8012",

  "task_id": "TASK-5012",

  "subtask_id": "STEP-01",

  "required_capabilities": ["file_read", "pattern_matching"],

  "required_security_level": "L1",

  "candidate_agents": [

    {

      "agent_id": "Research_Agent",

      "capability_match_score": 0.95,

      "health_status": "ONLINE",

      "current_load": 2

    },

    {

      "agent_id": "Software_Engineer_Agent",

      "capability_match_score": 0.70,

      "health_status": "ONLINE",

      "current_load": 0

    }

  ],

  "assigned_agent": "Research_Agent"

}
```

## 3. SELECTION ALGORITHM

Capability Filter: Filter agent registry for agents possessing 100% of required_capabilities.Security Gate Filter: Eliminate agents lacking authorization for required_security_level.Load Balancing Score ($S_r$):$$S_r = (MatchScore \times 0.7) + ((1 - CurrentLoad/MaxLoad) \times 0.3)$$Select agent with highest $S_r$.

## 4. REVISION HISTORY

VersionDateAuthorSummary of Changes1.0.0-DRAFT2026-08-09Core Engineering Architecture GroupInitial Release of Task Router Specification
