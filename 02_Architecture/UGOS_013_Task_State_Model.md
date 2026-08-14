# UGOS DOCUMENT METADATA

Document ID: UGOS_013_Task_State_Model

Version: 1.0.0-DRAFT

Status: APPROVED

Category: Architecture / State Machine

Owner: Core Engineering Architecture Group

Target Audience: Core Engineers, QA Testers, System Architects

Last Updated: 2026-08-09

---

# UGOS_013: Task Finite State Machine (FSM)

## 1. PURPOSE

This document specifies the mandatory finite state machine governing task states, transition conditions, and timeout rules within the UGOS Orchestrator.

---

## 2. STATE TRANSITION DIAGRAM

[ RECEIVED ] ---> [ ANALYZING ] ---> [ PLANNING ] ---> [ WAITING_APPROVAL ]

|

v

[ COMPLETED ] <--- [ VERIFYING ] <--- [ EXECUTING ] <----------+

|                   |                   |

v                   v                   v

[ FAILED ]          [ FAILED ]          [ BLOCKED ]

---

## 3. STATE DEFINITIONS & TRANSITION RULES

| Current State | Target State | Trigger / Condition | Timeout |

|---|---|---|---|

| **`RECEIVED`** | `ANALYZING` | Payload validated against API Schema; `TaskID` created. | 5 sec |

| **`ANALYZING`** | `PLANNING` | Complexity score > Threshold $T_{plan}$. | 10 sec |

| **`ANALYZING`** | `EXECUTING` | Complexity score <= Threshold $T_{plan}$ (Simple Task). | 10 sec |

| **`PLANNING`** | `WAITING_APPROVAL` | DAG contains $L_4$ or $L_5$ high-risk tool operations. | 30 sec |

| **`PLANNING`** | `EXECUTING` | DAG contains only $L_0$ - $L_3$ operations. | 30 sec |

| **`WAITING_APPROVAL`** | `EXECUTING` | Human approval token validated. | 300 sec |

| **`WAITING_APPROVAL`** | `BLOCKED` / `FAILED` | Approval rejected or timeout reached. | -- |

| **`EXECUTING`** | `VERIFYING` | All DAG node tasks completed successfully. | 300 sec |

| **`EXECUTING`** | `FAILED` | Unhandled agent crash, tool failure, or timeout. | -- |

| **`VERIFYING`** | `COMPLETED` | Evaluation checks passed (Confidence >= 0.85). | 15 sec |

| **`VERIFYING`** | `FAILED` | Output fails safety gate or confidence check. | -- |

---

## 4. REVISION HISTORY

| Version | Date | Author | Summary of Changes |

|---|---|---|---|

| 1.0.0-DRAFT | 2026-08-09 | Core Engineering Architecture Group | Initial Release of Task State Model |
