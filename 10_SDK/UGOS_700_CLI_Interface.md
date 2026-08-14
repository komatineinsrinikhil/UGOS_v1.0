# UGOS_700_CLI_Interface.md

**Module:** `10_SDK`

**Specification Version:** `1.0.0`

**File Reference:** `UGOS_700`

**Target Engine Interface:** `UGOS_100_Execution_Engine`, `UGOS_105_Orchestration_Engine`, `UGOS_106_Communication_Engine`

**Status:** `ACTIVE SPECIFICATION`

---

## 1. Module Overview & Functional Role

The **CLI Interface Specification (`UGOS_700`)** defines the command-line interface tools, terminal syntax taxonomy, execution entry points, interactive REPL shell mode, output formatting modes, and local configuration management for interacting with UGOS v1.0 clusters.

Operating as the primary local developer and administrative tool, `ugos` CLI allows human operators, DevOps automation scripts, and local CI/CD pipelines to dispatch workflows, query agent statuses, inspect memory stores, manage authorization tokens, and tail execution logs in real time.

### Primary Objectives

1. **Deterministic Command Taxonomy:** Enforce structured, verb-noun command patterns (`ugos <resource> <action> [flags]`).

2. **Multi-Format Output Rendering:** Support interactive terminal tables, colored logs, raw JSON, YAML, and quiet machine-parsable text streams (`--output json|yaml|table`).

3. **Interactive REPL & TUI Diagnostics:** Provide an interactive Terminal User Interface (TUI) mode for live agent monitoring, workflow graph visualization, and real-time log streaming.

4. **Secure Local Context Management:** Manage zero-trust authentication tokens, tenant profiles, and cluster connection endpoints locally in encrypted configuration files (`~/.ugos/config.yaml`).

---

## 2. Command Taxonomy & Command Tree

The `ugos` executable exposes six core command namespaces:

ugos├── agent        (list, inspect, invoke, logs)├── workflow     (run, status, cancel, list-history)├── memory       (query, inspect-m1, clear-cache)├── auth         (login, token-refresh, list-permissions)├── config       (set-context, show, set)└── system       (health, stats, tail-logs)

### Core CLI Command Summary

| Command Syntax | Operational Purpose | Default Privilege Required |

| :--- | :--- | :---: |

| `ugos agent list` | List registered active agents and health statuses | $L_0$ |

| `ugos agent invoke <agent_id>` | Synchronously trigger an agent action payload | $L_1$ |

| `ugos workflow run <file.json>` | Dispatch a DAG workflow execution payload (`UGOS_500`) | $L_2$ |

| `ugos workflow status <exec_id>` | Inspect active state and completed node execution list | $L_1$ |

| `ugos memory query "<query>"` | Query semantic/episodic memory stores ($M_2$/$M_3$) | $L_1$ |

| `ugos system health` | Ping execution engine, orchestration nodes, and vector stores | $L_0$ |

---

## 3. Configuration File Schema (`~/.ugos/config.yaml`)

```yaml

version: "1.0.0"

current_context: "prod-cluster"

contexts:

  - name: "prod-cluster"

    endpoint: "[https://api.ugos.dev:8443](https://api.ugos.dev:8443)"

    tenant_id: "tenant_core_prod"

    auth_type: "SPIFFE_JWT"

    credential_vault_ref: "keyring://ugos/prod"

    default_output_format: "table"

  - name: "local-dev"

    endpoint: "[http://127.0.0.1:8080](http://127.0.0.1:8080)"

    tenant_id: "tenant_dev_local"

    auth_type: "NONE"

    default_output_format: "json"

4. Input & Output Interface Schemas4.1 Input Schema: Command Execution Spec (CLICommandInputPayload)JSON{

  "$schema": "[https://ugos.dev/schemas/v1/cli_command_input_payload.json](https://ugos.dev/schemas/v1/cli_command_input_payload.json)",

  "command": "workflow run",

  "arguments": ["--file", "wf_refactor.json", "--async"],

  "flags": {

    "output": "json",

    "timeout_seconds": 120,

    "context": "prod-cluster"

  },

  "invocation_timestamp": "2026-08-11T08:31:00Z"

}
```

4.2 Output Schema: Structured CLI Response (CLICommandResponse)JSON{

  "$schema": "[https://ugos.dev/schemas/v1/cli_command_response.json](https://ugos.dev/schemas/v1/cli_command_response.json)",

  "exit_code": 0,

  "status": "SUCCESS",

  "data": {

    "execution_id": "wf_exec_902811a",

    "workflow_ref": "wf_def_500_patching",

    "state": "RUNNING",

    "started_at": "2026-08-11T08:31:01Z"

  },

  "messages": ["Workflow wf_exec_902811a successfully submitted to cluster."]

}

5. System InteroperabilityUGOS_105_Orchestration_Engine Interoperability: Dispatch workflow payloads and pull real-time FSM execution state updates over gRPC/REST.UGOS_401_Zero_Trust_Model Interoperability: Attach local SPIFFE/JWT tokens to CLI gRPC request headers for every executed command.UGOS_701_REST_API_Specification Interoperability: Function as the primary client wrapper consuming REST API endpoints.6. Safety Guardrails & Operational Constraints[!CAUTION]Interactive High-Privilege Confirmation: Any CLI command attempting an operation that requires $L_4$ Guarded or $L_5$ Root privilege (e.g., system configuration mutation or force workflow termination) MUST prompt for explicit interactive terminal confirmation ([y/N]) unless overridden by --force-yes-i-know-what-i-am-doing.Non-Zero Exit Code Mapping: Command errors return standardized POSIX exit codes: 1 (General error), 2 (CLI flag syntax error), 126 (Permission denied / insufficient privilege level), 130 (Terminated by Ctrl+C).Credential Storage Invariant: Plaintext tokens or secret keys must NEVER be written to stdout or saved in unencrypted config files; credentials must be stored in OS keyrings (e.g., SecretService, Keychain).
