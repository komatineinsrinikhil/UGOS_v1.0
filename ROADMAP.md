# UGOS — Status & Roadmap

Last updated: 2026-08-14

`UGOS_PROJECT_STATUS.md` is the short factual record. This is the longer view:
what actually exists, what is only written down, and what to build next with
enough detail to start without re-deciding anything.

---

# Part 1 — Where the project stands

## 1.1 By component

| Component | File | State | Notes |
|---|---|---|---|
| Policy engine | `src/ugos/security/policy.py` | **Working** | L0–L5, four checks, fail-closed, audit log |
| Tool engine | `src/ugos/core/tools.py` | **Working** | read / write+diff / eval, all policy-gated |
| Memory | `src/ugos/core/memory.py` | **Working** | SQLite, episodic + semantic, survives restart |
| DAG orchestrator | `src/ugos/engines/orchestrator.py` | **Working** | Topological ordering |
| Execution sandbox | `src/ugos/engines/execution.py` | **Working** | Docker with process fallback |
| Provider router | `ugos_providers.py` | **Working** | 8 backends, fallback chain, errors explain themselves |
| Agent loop | `ugos_agent.py` | **Working** | Read-only tools, per-tool enforcement, tolerant parsing |
| Web interface | `ugos_web.py` | **Working** | Markdown, highlighting, conversation, agent steps |
| Public demo mode | `ugos_web.py` | **Deployed** | Live on Render, bring-your-own-key, rate limited |
| Base agent | `src/ugos/agents/base.py` | **Working** | Security path cannot be bypassed |
| Specialist agents | `src/ugos/agents/specialized.py` | **2 of 8** | SoftwareEngineer, SecurityAudit |
| Workflows | — | **0 of 9** | Specified only |
| Evaluation harness | — | **Specified only** | `UGOS_800` describes it |
| Identity layer | — | **Dropped in v1.0** | Existed in v0.1 |

## 1.2 The honest summary

**The security core is real.** Policy, sandbox, elevation gate, audit log, and
the agent loop that routes every tool request through them. This is the part of
the project that would survive scrutiny.

**The breadth is not.** Specs describe eight specialist agents and nine
workflows; the code has two agents and no workflows. The README says so, which
is the right call, but it remains the largest gap between document and reality.

**Test coverage now matches the security core.** 18 tests, and every deny path
asserts its reason rather than just a boolean. `ugos_agent.py` and
`ugos_providers.py` remain uncovered.

**It is deployed.** The public demo runs on Render in bring-your-own-key mode,
and has been used with a real key. The security model behaves the same on a
server as it does locally.

## 1.3 Known defects and rough edges

| # | Issue | Impact |
|---|---|---|
| ~~1~~ | ~~Agent loop makes up to 7 model calls per question~~ | Fixed: capped at 4, typical question is 2 |
| ~~2~~ | ~~No retry or backoff on a 429~~ | Fixed: retries once, honours Retry-After |
| 3 | `list_dir` and `system_status` bypass the `ToolEngine` registry | Two code paths for tools instead of one |
| ~~4~~ | ~~No CI~~ | Fixed: GitHub Actions runs 18 tests per push |
| 5 | 22 spec files have run-together paragraphs | Readable but ugly; needs a human pass |
| ~~6~~ | ~~`schemas/v1` empty~~ | Fixed: 44 schemas extracted; the script had a hardcoded Windows path |
| 7 | Agent tools still bypass `ToolEngine` for `list_dir` / `system_status` | Two code paths; see UGOS_600 deviations |

---

# Part 2 — Do these first (hours, not days)

> **Status: all four done, 2026-08-14.** Worst-case model calls cut from 7 to 4;
> 429 retry verified against a rate-limiting server; suite grown from 11 tests
> to 18; CI running on every push. Left here as the record of what was changed
> and why.

## 2.1 Cut the model calls per question

**Problem.** `MAX_STEPS = 6` in `ugos_agent.py`, plus a final call, means up to
seven requests per question. Gemini's free tier counts per minute, so a few
questions exhaust it — which is exactly what happened during the deploy.

**Fix.**

```python
MAX_STEPS = 3            # ugos_agent.py
```

Most questions need one or two tools. Also drop the extra "you have run out of
steps" call: if the loop exhausts, return the last answer it produced rather
than asking again.

**Effort:** minutes. **Impact:** the difference between the demo working and not.

## 2.2 Handle 429 properly

**Problem.** A rate-limit error is treated like any other failure — the provider
is abandoned and the run falls through.

**Fix.** In `ugos_providers.py`, on HTTP 429: wait the `Retry-After` header if
present, otherwise 2s, and retry once. If it fails again, fall through as now.

```python
except urllib.error.HTTPError as exc:
    if exc.code == 429 and not _retried:
        time.sleep(float(exc.headers.get("Retry-After", 2)))
        return self.complete(prompt, system_prompt, _retried=True, **kwargs)
```

**Effort:** ~20 lines. **Impact:** most rate-limit failures disappear.

## 2.3 Add the missing tests

`UGOS_900` already lists them. Add to `tests/test_core.py`:

- L3 actions allowed at L3, refused at L2
- L4 refused without approval, allowed with it
- Fail-closed on a malformed target
- Each deny path asserts its *reason*, not just `False`

**Effort:** an hour. **Impact:** the security work becomes provable rather than
claimed.

## 2.4 Add CI

`.github/workflows/tests.yml`, ~15 lines: run the suite on every push. Free on
GitHub, and it makes the green badge in your README honest.

---

# Part 3 — The next real build

## 3.1 Write access with approval — *recommended next*

**Why.** The agent can look but not touch. "Read this and explain it" is a much
smaller demo than "fix this and show me the diff before it changes anything."
It also forces the design question your v0.1 guardrails only gestured at: what
does approval actually look like?

**How.**

1. Add `write_file` to `ReadOnlyToolbox` — rename it `Toolbox` — declaring
   `WRITE_FILE`, so it needs L1 or above.
2. Tighten the sandbox to a dedicated `workspace/` folder rather than the whole
   project, so an agent cannot rewrite UGOS itself.
3. **Do not write immediately.** Return the unified diff (your `ToolEngine`
   already generates it) and pause.
4. The web page renders the diff with Approve and Reject buttons.
5. On approve, a second call commits the write.

**The interesting part** is that approval is a *policy* decision, not a UI one.
`requires_approval: true` belongs in the policy, so the button exists because
the policy demanded it — not because the front end chose to be polite.

**Effort:** a day. **Risk:** real, which is why the sandbox narrows first.

## 3.2 Tools for the L3 actions

L3 gates `DELEGATE_TASK`, `ROUTE_API`, `QUERY_DATABASE`, but nothing requests
them. Three small tools would exercise the level:

- **`ask_specialist`** → `DELEGATE_TASK`. Hands a subtask to
  `SecurityAuditAgent` and returns its answer. This is your multi-agent story in
  its smallest honest form.
- **`fetch_url`** → `ROUTE_API`. Retrieves a URL. Needs an allowlist in policy,
  or it becomes an open proxy.
- **`query_memory`** → `QUERY_DATABASE`. Read-only SQL against
  `ugos_memory.db`. Lets an agent answer "what did we decide last week?", which
  finally makes the memory tier visible to users.

**Effort:** half a day. **Impact:** turns a specification claim into a
demonstration.

## 3.3 The evaluation harness

`UGOS_800` specifies it; nothing runs it. Build `evaluate.py`:

- A list of probes with expected verdicts (the table is already in the spec)
- Runs each through the real pipeline
- Reports pass/fail, and counts **false allows** separately as blocking
- Saves results per run so regressions are visible

**Effort:** a day. **Impact:** you can claim the security works and point at
evidence rather than a screenshot.

---

# Part 4 — Bigger directions

## 4.1 Extract UGOS as an importable package

**The idea.** Stop being an app; become something people `pip install`. The
differentiator is *policy as the API* — you cannot construct an agent without
declaring what it may do.

```python
from ugos import Agent

app = Agent(model="gemini", policy="ugos.policy.yaml")

@app.tool(requires="read_file")
def read_notes(path: str) -> str:
    return open(path).read()

app.run("summarise my notes")
```

**Steps.** Move `policy.py`, `tools.py`, `memory.py` and the agent loop into a
`ugos/` package; keep the web UI as an example that imports it; add
`pyproject.toml`; publish to PyPI. The web interface becomes proof the API is
usable, which is the best reason to keep it.

**Effort:** a weekend for a rough version. **Risk:** a crowded field. Competing
on features is unwinnable; competing on "security is structural, not advisory"
is narrow enough to defend.

## 4.2 Declarative policy files

Today the policy lives in Python. Moving it to YAML means it can be reviewed,
diffed, and owned by someone who does not write code:

```yaml
level: L1
sandbox: ./workspace
forbid: ["*.env", "*.key", "*credentials*"]
tools:
  read_notes: L0
  send_email: L3
elevation:
  L4: human
```

This is the single change that would most make UGOS feel like infrastructure
rather than a program. **Effort:** a day. Do it *before* 4.1, since the package
API should take a policy file from the start.

## 4.3 Streaming responses

Answers currently appear all at once after a pause. Streaming word-by-word is
most of what "polished" means in an AI interface. Requires server-sent events
and streaming support per provider. **Effort:** a day. **Impact:** cosmetic but
large.

## 4.4 Ship it as an application

PyInstaller wraps Python and your code into one `UGOS.exe` — download,
double-click, no Python needed. Two obstacles: the AI still has to come from
somewhere, and unsigned executables trigger Windows SmartScreen. Fine for a
portfolio, awkward for strangers.

## 4.5 Revisit the identity layer

v0.1 had an Identity Engine — one operating system, many personas, swap the
profile. v1.0 dropped it. Worth reconsidering: agents are defined by privilege
today, but "what is this agent for" is not fully answered by a permission level.
An identity file per agent — role, tone, scope — would reconnect the two
versions.

---

# Part 5 — Suggested order

| When | Do | Why |
|---|---|---|
| ~~Done~~ | ~~2.1, 2.2, 2.3, 2.4~~ | Rate limits fixed, security provable, CI green |
| ~~Done~~ | ~~Deploy to Render~~ | Live, bring-your-own-key |
| ~~Done~~ | ~~3.1 write access~~ | Proposes a diff; a human approves |
| **Next** | **3.3 evaluation harness** | Turns the security claim into evidence |
| Then | 4.2 policy files | Turns it into infrastructure |
| Then | 3.3 evaluation | Evidence for the security claim |
| Later | 4.1 package | Only after the API has been used in anger |
| Someday | 3.2, 4.3, 4.4, 4.5 | Valuable, not urgent |

**If you only do one thing:** 2.1 and 2.2, then deploy. A working public URL is
worth more than any amount of additional local capability, because it is the
only version of this that other people can see.
