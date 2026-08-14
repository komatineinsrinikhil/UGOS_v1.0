# Origins — how UGOS got here

UGOS did not start as software. It started as nine Word documents describing how
a custom GPT should behave.

This folder is that version, preserved. It is kept because the distance between
it and the current system is the most interesting thing about the project.

---

## v0.1 — Universal GPT Operating System

*Nine documents, ~26,500 words, drafted early August 2026.*

The acronym meant something different then: **Universal GPT Operating System**.
The idea was a portable behaviour layer — one operating system that could power
many custom GPTs, with only the identity swapped:

> The Identity Engine defines who the AI is within a specific GPT
> implementation. Unlike the Operating System, which controls *how* the AI
> behaves, the Identity Engine controls *what identity* the AI represents. This
> separation ensures that the same Operating System can power multiple GPTs by
> replacing only the Identity Profile.
>
> — `01_UGOS_CORE_IDENTITY_SYSTEM`

It covered reasoning lifecycles, five layers of memory, a four-level agent
hierarchy, seven categories of tool, communication standards, and a governance
layer whose philosophy was stated in one line:

> Trust is earned through honesty, not confidence.
>
> — `07_UGOS_SAFETY_GOVERNANCE_SYSTEM`

---

## The shift

v0.1 was written as **instructions to a model**. The Guardrails Engine says the
AI *must* act honestly, *must* prevent hallucinations, *must* protect
confidentiality, *must* resist prompt injection.

Every one of those is a request. A model can ignore a request, be argued out of
it, or lose track of it halfway through a long conversation. Nothing in v0.1
could stop a model that decided otherwise, because there was nothing outside the
model to do the stopping.

v1.0 moved the same concerns **out of the prompt and into code**.

The clearest example is a section v0.1 called *Prompt Injection Resistance* — a
list of behaviours the AI should maintain when someone tries to talk it out of
its rules. In v1.0 there is no equivalent instruction, because the question no
longer arises in that form: the model may *request* a tool, and a policy engine
decides whether it runs. An injected prompt can change what the model asks for.
It cannot change what the policy allows.

That is the whole distance between the two versions:

| | v0.1 | v1.0 |
|---|---|---|
| Form | Word documents | Python runtime + specification |
| Security | Instructions the model should follow | Checks the model cannot bypass |
| Subject | One AI with a persona | Many agents with privilege levels L0–L5 |
| Failure mode | Model ignores the instruction | Action is refused before it executes |
| Enforcement | Trust | Code |

**Asking became enforcing.** Everything else is detail.

---

## What carried over

| v0.1 document | Became | Notes |
|---|---|---|
| `02_INTELLIGENCE_REASONING` | `03_Engines/UGOS_101`, `UGOS_103` | The seven-stage reasoning lifecycle split into Reasoning and Decision engines |
| `03_MEMORY_KNOWLEDGE` | `06_Memory_Knowledge/UGOS_300–311` | Five memory layers compressed to two tiers — episodic and semantic — and implemented in SQLite |
| `04_AGENT_WORKFLOW` | `04_Agents`, `05_Workflows`, `UGOS_105` | The four-level agent hierarchy became eight specialist agent specs and nine workflows |
| `05_COMMUNICATION_OUTPUT` | `03_Engines/UGOS_106` | Substantially shortened |
| `07_SAFETY_GOVERNANCE` | `08_Governance_Security/UGOS_400–403` | The largest transformation: guardrail *principles* became a policy engine with six privilege levels, forbidden-path patterns and a sandbox boundary |
| `09_ARCHITECTURE_DEPLOYMENT` | `02_Architecture/UGOS_010–013` | Response lifecycle became the request lifecycle and task state model |

## What was dropped

**The Identity layer has no counterpart in v1.0.** The idea that one operating
system runs many personas by swapping an identity profile did not survive the
move from custom GPTs to agents — agents are defined by capability and privilege
level, not by personality.

Whether that was the right cut is an open question. Identity mattered when the
product was a GPT someone talks to. It matters less when the product is a
runtime that executes tasks. But "which agent am I and what am I for" is not
entirely answered by a permission level.

## What is still unfinished

Two v0.1 documents map onto v1.0 modules that are still empty placeholders:

- `06_TOOL_EXTENSION` — seven tool categories, an integration framework, and
  selection logic. v1.0's `07_Tools_Plugins` has no content, and
  `UGOS_107_Tool_Engine` is the shortest spec in the set.
- `08_LEARNING_IMPROVEMENT` — a learning lifecycle in seven stages. v1.0's
  `09_Evaluation` has no content.

The thinking exists. It was simply left behind in the rewrite.

---

## About these files

The nine documents are reproduced here as markdown for readability, converted
from the original `.docx` files, which are kept alongside them in `originals/`.
The conversion changed formatting only — no wording was added, removed or
reordered.

They are a historical record, not current specification. Where v0.1 and v1.0
disagree, **v1.0 is authoritative**.
