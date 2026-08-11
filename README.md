\# UGOS v1.0 — Unified Agent Operating System Specification



<div align="center">



\# 🤖 UGOS v1.0

\### \*User-Guided Agent Operating System\*



\*\*An enterprise-grade, zero-trust execution engine and runtime environment for autonomous AI agents.\*\*



<p align="center">

&#x20; <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge\&logo=python\&logoColor=white" alt="Python 3.12"></a>

&#x20; <a href="https://docs.pytest.org/"><img src="https://img.shields.io/badge/PyTest-11%2F11%20Passing-success?style=for-the-badge\&logo=pytest\&logoColor=white" alt="Test Suite"></a>

&#x20; <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Sandbox-Docker%20%7C%20Process-2496ED?style=for-the-badge\&logo=docker\&logoColor=white" alt="Docker Sandboxing"></a>

&#x20; <a href="https://sqlite.org/"><img src="https://img.shields.io/badge/Storage-SQLite%203-003B57?style=for-the-badge\&logo=sqlite\&logoColor=white" alt="SQLite Storage"></a>

&#x20; <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License"></a>

</p>



\---



\[Key Subsystems](#-key-architecture--subsystems) •

\[Quickstart](#-quickstart--installation) •

\[Demo Workflow](#-live-demo-workflow) •

\[Specification](#-specification--design-docs)



\---



</div>



\## 🌟 Overview



\*\*UGOS (User-Guided Agent Operating System)\*\* is an open-source operating system runtime designed specifically for AI agents. Just as traditional operating systems manage hardware resources for applications, UGOS provides \*\*Zero-Trust Security, DAG Task Orchestration, Sandboxed Container Execution, Persistent Dual-Tier Memory, and Fallback LLM Routing\*\* to guarantee safe and deterministic agent behavior.



\### 🛡️ Core Pillars

\* \*\*🔐 Zero-Trust Security Gate:\*\* Fine-grained policy enforcement (`PolicyEngine`) restricting agent file system and shell operations before execution.

\* \*\*⚡ DAG Task Orchestrator:\*\* Dependency-resolved Directed Acyclic Graph execution for complex multi-agent workflows.

\* \*\*📦 Sandboxed Execution Engine:\*\* Containerized isolation via Docker with graceful process-level fallback.

\* \*\*💾 Persistent Dual-Tier Memory:\*\* SQLite-backed episodic logs and semantic facts retained across sessions (`ugos\_memory.db`).

\* \*\*🔄 Circuit-Breaker LLM Router:\*\* Automatic failover between primary cloud endpoints and 100% offline local models (e.g., Ollama).

\*\*UGOS (Unified Agent Operating System)\*\* is an enterprise-grade, zero-trust framework for orchestrating autonomous AI agents, sandboxed tool executions, multi-provider LLM routing, and persistent episodic/semantic memory.



\---



\## 🏛️ Architecture Overview

┌───────────────────────────┐

&#x20;                   │   CLI Entry Point Driver   │

&#x20;                   │     (src/ugos/main.py)    │

&#x20;                   └─────────────┬─────────────┘

&#x20;                                 │

&#x20;      ┌──────────────────────────┼──────────────────────────┐

&#x20;      ▼                          ▼                          ▼



┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐

│   DAG Orchestrator │     │  Zero-Trust Engine │     │ Memory Engine (DB) │

│ (orchestrator.py)  │     │    (policy.py)     │     │    (memory.py)     │

└──────────┬─────────┘     └──────────┬─────────┘     └──────────┬─────────┘

│                          │                          │

▼                          ▼                          ▼

┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐

│ Execution Sandbox  │     │ Specialized Agents │     │ LLM Provider Router│

│   (execution.py)   │     │  (specialized.py)  │     │    (router.py)     │

└────────────────────┘     └────────────────────┘     └────────────────────┘




---



\## ⚙️ Core Subsystem Specifications



\### 1. Zero-Trust Security Policy Engine (`src/ugos/security/policy.py`)

\* Enforces role-based permissions (`RESTRICTED\_READ`, `STANDARD\_EXEC`, `ADMIN\_SUPERUSER`).

\* Validates every tool action against a strict policy matrix before execution.

\* Restricts filesystem access to dedicated sandbox paths (`/sandbox`, `./tmp`).



\### 2. DAG Workflow Orchestrator (`src/ugos/engines/orchestrator.py`)

\* Resolves task dependency graphs topologically using Directed Acyclic Graphs (DAGs).

\* Supports non-blocking task execution and dependency completion tracking.

\* Captures step-by-step workflow state transitions (`PENDING` ➔ `RUNNING` ➔ `COMPLETED` / `FAILED`).



\### 3. Containerized Sandbox Execution (`src/ugos/engines/execution.py`)

\* Executes code inside isolated Docker containers (`python:3.12-slim` image with memory limits and zero network access).

\* Features automatic local process fallback when Docker binary is absent from `PATH`.

\* Polymorphic execution handling accepting direct payloads or task ID strings.



\### 4. Persistent SQLite Memory Engine (`src/ugos/core/memory.py`)

\* Dual-tier memory model: \*\*Episodic\*\* (interaction history) \& \*\*Semantic\*\* (facts \& metadata).

\* Persistent storage backed by an embedded SQLite database (`ugos\_memory.db`).

\* Tag-based indexing and keyword search retrieval.



\### 5. Multi-Provider LLM Router (`src/ugos/llm/router.py`)

\* Abstract LLM provider interface enabling pluggable LLM integrations (OpenAI, Anthropic, Ollama, Custom).

\* Active circuit breaker pattern with automatic failover routing to secondary/mock providers on primary API failure.



\### 6. Sandboxed Tool Engine (`src/ugos/core/tools.py`)

\* Secure file patch engine generating standard Unified Diff format outputs.

\* Isolated command runner preventing arbitrary system shell escalation.



\---



\## 📁 Repository Structure



UGOS\_v1.0\_SPECIFICATION/

├── src/

│   └── ugos/

│       ├── init.py

│       ├── main.py                   # Unified CLI Entry Point

│       ├── agents/

│       │   ├── base.py               # Abstract Base Agent Class

│       │   └── specialized.py        # SoftwareEngineerAgent \& SecurityAuditAgent

│       ├── core/

│       │   ├── memory.py             # SQLite Memory Engine

│       │   └── tools.py              # File Writer \& Unified Diff Tool

│       ├── engines/

│       │   ├── execution.py          # Docker Sandbox / Local Execution Engine

│       │   └── orchestrator.py       # DAG Workflow Coordinator

│       ├── llm/

│       │   └── router.py             # Multi-Provider Router with Failover

│       └── security/

│           └── policy.py             # Zero-Trust Policy Engine

├── tests/

│   └── test\_core.py                  # Complete 11-Part Integration Test Suite

├── ugos\_memory.db                    # Persistent SQLite Memory Store

└── README.md                         # Architecture Documentation


\---



\## 🚀 Quick Start \& CLI Usage



\### Prerequisites

\* \*\*Python 3.10+\*\* (Tested on Python 3.12)

\* \*\*Docker\*\* (Optional: for containerized sandbox execution)



\### 1. Execute Unified CLI Driver



Run the default demo DAG workflow:

---



\## 🚀 Quick Start \& CLI Usage



\### Prerequisites

\* \*\*Python 3.10+\*\* (Tested on Python 3.12)

\* \*\*Docker\*\* (Optional: for containerized sandbox execution)



\### 1. Execute Unified CLI Driver



Run the default demo DAG workflow:

Enable Docker Sandbox Mode:



powershell

python src/ugos/main.py --use-docker --workflow prod\_workflow\_01





\### 2. Run Integration Test Suite



Execute the full 11-part PyTest suite:



powershell

python -m pytest tests/test\_core.py -v





\---



\## 🧪 Test Suite Coverage



| Test Name | Verified Subsystem | Result |

| :--- | :--- | :---: |

| `test\_execution\_engine\_single\_task` | Execution Engine Task Resolution | \*\*PASSED\*\* |

| `test\_orchestrator\_dag\_pipeline` | Topological DAG Dependency Graph | \*\*PASSED\*\* |

| `test\_security\_policy\_enforcement` | Zero-Trust Permission Matrices | \*\*PASSED\*\* |

| `test\_base\_agent\_security\_integration` | Agent Security Context Checks | \*\*PASSED\*\* |

| `test\_tool\_engine\_execution` | Command Execution Sandbox | \*\*PASSED\*\* |

| `test\_memory\_engine\_episodic\_and\_semantic` | In-Memory Facts \& History | \*\*PASSED\*\* |

| `test\_specialized\_agents\_permissions` | `SoftwareEngineerAgent` Role Permissions | \*\*PASSED\*\* |

| `test\_tool\_engine\_file\_writer\_diff` | Patch Generation \& Unified Diffing | \*\*PASSED\*\* |

| `test\_sqlite\_memory\_engine\_persistence` | SQLite Database Schema \& Queries | \*\*PASSED\*\* |

| `test\_llm\_router\_primary\_and\_fallback` | Provider Failover \& Fallback Logic | \*\*PASSED\*\* |

| `test\_execution\_engine\_sandbox\_fallback` | Docker \& Local Fallback Execution | \*\*PASSED\*\* |



\---



\## 📄 License



This specification and reference implementation are released under the \[MIT License](LICENSE).



