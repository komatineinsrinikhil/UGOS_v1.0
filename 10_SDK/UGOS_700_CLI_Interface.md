\# UGOS\_700\_CLI\_Interface.md



\*\*Module:\*\* `10\_SDK`  

\*\*Specification Version:\*\* `1.0.0`  

\*\*File Reference:\*\* `UGOS\_700`  

\*\*Target Engine Interface:\*\* `UGOS\_100\_Execution\_Engine`, `UGOS\_105\_Orchestration\_Engine`, `UGOS\_106\_Communication\_Engine`  

\*\*Status:\*\* `ACTIVE SPECIFICATION`



\---



\## 1. Module Overview \& Functional Role



The \*\*CLI Interface Specification (`UGOS\_700`)\*\* defines the command-line interface tools, terminal syntax taxonomy, execution entry points, interactive REPL shell mode, output formatting modes, and local configuration management for interacting with UGOS v1.0 clusters.



Operating as the primary local developer and administrative tool, `ugos` CLI allows human operators, DevOps automation scripts, and local CI/CD pipelines to dispatch workflows, query agent statuses, inspect memory stores, manage authorization tokens, and tail execution logs in real time.



\### Primary Objectives

1\. \*\*Deterministic Command Taxonomy:\*\* Enforce structured, verb-noun command patterns (`ugos <resource> <action> \[flags]`).

2\. \*\*Multi-Format Output Rendering:\*\* Support interactive terminal tables, colored logs, raw JSON, YAML, and quiet machine-parsable text streams (`--output json|yaml|table`).

3\. \*\*Interactive REPL \& TUI Diagnostics:\*\* Provide an interactive Terminal User Interface (TUI) mode for live agent monitoring, workflow graph visualization, and real-time log streaming.

4\. \*\*Secure Local Context Management:\*\* Manage zero-trust authentication tokens, tenant profiles, and cluster connection endpoints locally in encrypted configuration files (`\~/.ugos/config.yaml`).



\---



\## 2. Command Taxonomy \& Command Tree



The `ugos` executable exposes six core command namespaces:



ugos├── agent        (list, inspect, invoke, logs)├── workflow     (run, status, cancel, list-history)├── memory       (query, inspect-m1, clear-cache)├── auth         (login, token-refresh, list-permissions)├── config       (set-context, show, set)└── system       (health, stats, tail-logs)

\### Core CLI Command Summary



| Command Syntax | Operational Purpose | Default Privilege Required |

| :--- | :--- | :---: |

| `ugos agent list` | List registered active agents and health statuses | $L\_0$ |

| `ugos agent invoke <agent\_id>` | Synchronously trigger an agent action payload | $L\_1$ |

| `ugos workflow run <file.json>` | Dispatch a DAG workflow execution payload (`UGOS\_500`) | $L\_2$ |

| `ugos workflow status <exec\_id>` | Inspect active state and completed node execution list | $L\_1$ |

| `ugos memory query "<query>"` | Query semantic/episodic memory stores ($M\_2$/$M\_3$) | $L\_1$ |

| `ugos system health` | Ping execution engine, orchestration nodes, and vector stores | $L\_0$ |



\---



\## 3. Configuration File Schema (`\~/.ugos/config.yaml`)



```yaml

version: "1.0.0"

current\_context: "prod-cluster"

contexts:

&#x20; - name: "prod-cluster"

&#x20;   endpoint: "\[https://api.ugos.dev:8443](https://api.ugos.dev:8443)"

&#x20;   tenant\_id: "tenant\_core\_prod"

&#x20;   auth\_type: "SPIFFE\_JWT"

&#x20;   credential\_vault\_ref: "keyring://ugos/prod"

&#x20;   default\_output\_format: "table"

&#x20; - name: "local-dev"

&#x20;   endpoint: "\[http://127.0.0.1:8080](http://127.0.0.1:8080)"

&#x20;   tenant\_id: "tenant\_dev\_local"

&#x20;   auth\_type: "NONE"

&#x20;   default\_output\_format: "json"

4\. Input \& Output Interface Schemas4.1 Input Schema: Command Execution Spec (CLICommandInputPayload)JSON{

&#x20; "$schema": "\[https://ugos.dev/schemas/v1/cli\_command\_input\_payload.json](https://ugos.dev/schemas/v1/cli\_command\_input\_payload.json)",

&#x20; "command": "workflow run",

&#x20; "arguments": \["--file", "wf\_refactor.json", "--async"],

&#x20; "flags": {

&#x20;   "output": "json",

&#x20;   "timeout\_seconds": 120,

&#x20;   "context": "prod-cluster"

&#x20; },

&#x20; "invocation\_timestamp": "2026-08-11T08:31:00Z"

}

4.2 Output Schema: Structured CLI Response (CLICommandResponse)JSON{

&#x20; "$schema": "\[https://ugos.dev/schemas/v1/cli\_command\_response.json](https://ugos.dev/schemas/v1/cli\_command\_response.json)",

&#x20; "exit\_code": 0,

&#x20; "status": "SUCCESS",

&#x20; "data": {

&#x20;   "execution\_id": "wf\_exec\_902811a",

&#x20;   "workflow\_ref": "wf\_def\_500\_patching",

&#x20;   "state": "RUNNING",

&#x20;   "started\_at": "2026-08-11T08:31:01Z"

&#x20; },

&#x20; "messages": \["Workflow wf\_exec\_902811a successfully submitted to cluster."]

}

5\. System InteroperabilityUGOS\_105\_Orchestration\_Engine Interoperability: Dispatch workflow payloads and pull real-time FSM execution state updates over gRPC/REST.UGOS\_401\_Zero\_Trust\_Model Interoperability: Attach local SPIFFE/JWT tokens to CLI gRPC request headers for every executed command.UGOS\_701\_REST\_API\_Specification Interoperability: Function as the primary client wrapper consuming REST API endpoints.6. Safety Guardrails \& Operational Constraints\[!CAUTION]Interactive High-Privilege Confirmation: Any CLI command attempting an operation that requires $L\_4$ Guarded or $L\_5$ Root privilege (e.g., system configuration mutation or force workflow termination) MUST prompt for explicit interactive terminal confirmation (\[y/N]) unless overridden by --force-yes-i-know-what-i-am-doing.Non-Zero Exit Code Mapping: Command errors return standardized POSIX exit codes: 1 (General error), 2 (CLI flag syntax error), 126 (Permission denied / insufficient privilege level), 130 (Terminated by Ctrl+C).Credential Storage Invariant: Plaintext tokens or secret keys must NEVER be written to stdout or saved in unencrypted config files; credentials must be stored in OS keyrings (e.g., SecretService, Keychain).

