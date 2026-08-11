\# UGOS DOCUMENT METADATA

Document ID: UGOS\_104\_Task\_Router

Version: 1.0.0-DRAFT

Status: APPROVED

Category: Core Engine / Routing

Owner: Core Engineering Architecture Group

Target Audience: Core Engineers, Systems Architects, Multi-Agent Developers

Last Updated: 2026-08-09



\---



\# UGOS\_104: Task Router Specification



\## 1. PURPOSE

The Task Router dynamically matches task requirements and DAG steps to appropriate specialist agents based on capability parameters, operational availability, and performance history.



\---



\## 2. ROUTING SCHEMA \& AGENT MATCHING (JSON)



```json

{

&#x20; "routing\_id": "ROUTE-8012",

&#x20; "task\_id": "TASK-5012",

&#x20; "subtask\_id": "STEP-01",

&#x20; "required\_capabilities": \["file\_read", "pattern\_matching"],

&#x20; "required\_security\_level": "L1",

&#x20; "candidate\_agents": \[

&#x20;   {

&#x20;     "agent\_id": "Research\_Agent",

&#x20;     "capability\_match\_score": 0.95,

&#x20;     "health\_status": "ONLINE",

&#x20;     "current\_load": 2

&#x20;   },

&#x20;   {

&#x20;     "agent\_id": "Software\_Engineer\_Agent",

&#x20;     "capability\_match\_score": 0.70,

&#x20;     "health\_status": "ONLINE",

&#x20;     "current\_load": 0

&#x20;   }

&#x20; ],

&#x20; "assigned\_agent": "Research\_Agent"

}

3\. SELECTION ALGORITHMCapability Filter: Filter agent registry for agents possessing 100% of required\_capabilities.Security Gate Filter: Eliminate agents lacking authorization for required\_security\_level.Load Balancing Score ($S\_r$):$$S\_r = (MatchScore \\times 0.7) + ((1 - CurrentLoad/MaxLoad) \\times 0.3)$$Select agent with highest $S\_r$.4. REVISION HISTORYVersionDateAuthorSummary of Changes1.0.0-DRAFT2026-08-09Core Engineering Architecture GroupInitial Release of Task Router Specification

