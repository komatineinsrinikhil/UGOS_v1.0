# UGOS_513_Doc_Generation_Workflow.md

**Module:** `05_Workflows`

**Specification Version:** `1.0.0`

**File Reference:** `UGOS_513`

**Target Engine Interface:** `UGOS_102_Planning_Engine`, `UGOS_105_Orchestration_Engine`, `UGOS_106_Communication_Engine`

**Status:** `ACTIVE SPECIFICATION`

---

## 1. Module Overview & Workflow Purpose

The **Documentation Generation Workflow (`UGOS_513`)** is an automated pipeline designed for codebase scanning, AST docstring extraction, OpenAPI/AsyncAPI specification generation, architecture diagram rendering, and knowledge graph ingestion across the UGOS ecosystem.

Operating across `UGOS_217` (Documentation), `UGOS_210` (Research), `UGOS_211` (Software Engineer), and `UGOS_216` (QA Testing), `UGOS_513` ensures that technical documentation, public API contracts, and internal system knowledge graphs stay synchronized with source code changes with zero manual overhead.

### Primary Objectives

1. **Automated Codebase & AST Ingestion:** Parse multi-language repository trees, extracting type annotations, function signatures, class hierarchies, and inline docstrings.

2. **Multi-Format Technical Documentation Synthesis:** Render clean, structured Markdown API references, OpenAPI 3.1 REST/gRPC schemas, and Mermaid.js architecture flowcharts.

3. **Documentation Drift Detection & Link Auditing:** Execute linter checks to detect outdated documentation references, broken anchors, or missing method signatures via `UGOS_216`.

4. **Knowledge Base Ingestion & Vector Indexing:** Commit verified documentation artifacts to `06_Memory_Knowledge` vector stores for downstream context retrieval.

---

## 2. Workflow Stage Topology

`UGOS_513` executes a 5-phase documentation pipeline: **Scan AST $\rightarrow$ Extract Signatures $\rightarrow$ Synthesize Artifacts $\rightarrow$ Audit & Lint $\rightarrow$ Publish & Index**.

┌─────────────────────────────────────────────────────────────┐

│ Stage 1: Codebase AST Scanning & Dependency Mapping (UGOS_210)│

└──────────────────────────────┬──────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────┐

│ Stage 2: Metadata & Signature Extraction (UGOS_217)        │

└──────────────────────────────┬──────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────┐

│ Stage 3: Multi-Format Doc & Spec Synthesis (UGOS_217)     │

└──────────────────────────────┬──────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────┐

│ Stage 4: Documentation Linter & Link Audit (UGOS_216)     │

└──────────────────────────────┬──────────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────────────┐

│ Stage 5: Repository Publish & Vector Index Ingestion        │

└─────────────────────────────────────────────────────────────┘

---

## 3. Node Execution & Responsibility Matrix

| Node ID | Assigned Specialist | Primary Action | Compensation / Rollback Action |

| :--- | :--- | :--- | :--- |

| `doc_01_scan` | `UGOS_210_Research_Agent` | Parse repository file tree & AST symbol tables | N/A (Read-Only) |

| `doc_02_extract` | `UGOS_217_Documentation_Agent` | Extract docstrings, parameters, and type hints | N/A (Read-Only) |

| `doc_03_synthesize`| `UGOS_217_Documentation_Agent` | Draft Markdown API docs, OpenAPI specs, diagrams | `git checkout -- docs/` (Discard) |

| `doc_04_audit` | `UGOS_216_QA_Testing_Agent` | Audit link validity, snippet syntax, and coverage | Trigger `doc_03_synthesize` revision |

| `doc_05_publish` | `UGOS_105_Orchestration_Engine` | Commit docs to git branch & push to vector store | Revert doc commit |

---

## 4. Input & Output Interface Schemas

### 4.1 Ingestion Schema: Documentation Generation Target (`DocGenerationPayload`)

```json

{

  "$schema": "[https://ugos.dev/schemas/v1/doc_generation_payload.json](https://ugos.dev/schemas/v1/doc_generation_payload.json)",

  "workflow_execution_id": "wf_doc_881920",

  "timestamp": "2026-08-10T09:35:00Z",

  "target_scope": {

    "repository_root": "mem://workspace/ugos_core/",

    "source_directories": ["ugos/engines/", "ugos/agents/"],

    "output_directory": "docs/api/"

  },

  "generation_targets": {

    "api_reference_markdown": true,

    "openapi_spec": true,

    "mermaid_architecture_diagrams": true

  },

  "quality_thresholds": {

    "min_docstring_coverage_pct": 95.0,

    "fail_on_broken_links": true

  }

}
```

4.2 Output Schema: Documentation Generation Result (DocGenerationResult)

JSON

{

  "$schema": "[https://ugos.dev/schemas/v1/doc_generation_result.json](https://ugos.dev/schemas/v1/doc_generation_result.json)",

  "execution_id": "wf_doc_881920",

  "status": "COMPLETED",

  "generation_metrics": {

    "files_scanned": 42,

    "symbols_documented": 312,

    "docstring_coverage_pct": 97.4,

    "generated_artifacts": [

      "docs/api/engines.md",

      "docs/api/agents.md",

      "docs/openapi/ugos_v1_openapi.json"

    ]

  },

  "indexing_status": {

    "vector_embeddings_created": 158,

    "knowledge_graph_nodes_updated": 42

  }

}

5. System Interoperability

UGOS_106_Communication_Engine Interoperability: Stream synthesized documentation previews directly to user interfaces.

UGOS_310_Knowledge_Base_Schema Interoperability: Inject chunked document embeddings directly into persistent vector storage.

UGOS_217_Documentation_Agent Interoperability: Execute core Markdown formatting, linter checking, and OpenAPI schema validation.

6. Safety Guardrails & Operational Constraints

[!IMPORTANT]

Secret Redaction Gate: Stage 2 extraction MUST run automated secret-scanning regex heuristics to strip private credentials, tokens, or environment keys before documentation files are written to disk.

Read-Only Source Enforcement: UGOS_513 operates strictly in read-only mode regarding source code files; it can only write to designated /docs directories or vector indices.

Coverage Interception: If docstring_coverage_pct falls below min_docstring_coverage_pct, UGOS_513 flags missing symbols and returns a non-blocking warning to UGOS_211.
