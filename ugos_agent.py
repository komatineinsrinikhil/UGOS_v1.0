"""
UGOS Agent Loop -- read-only tools under Zero-Trust
===================================================
This is what turns UGOS from a chatbot into an agent.

A chatbot answers in one shot. An agent runs a cycle:

    model decides it needs something
        -> asks for a tool
        -> PolicyEngine ALLOWS or DENIES the request
        -> the result (or the refusal) goes back to the model
        -> repeat until it has an answer

The security engine sits in the middle of that cycle, not beside it. The model
never touches a file directly: it can only ask, and the policy decides. A
refusal is fed back as an observation, so the model learns it may not have
that file rather than silently failing.

Tools are READ-ONLY by design. Nothing here can modify your disk.
"""

import json
import os
import platform
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
for _p in (str(BASE_DIR), str(BASE_DIR / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ugos.core.tools import ToolEngine
from ugos.security.policy import PolicyEngine, PermissionLevel, SecurityAction

MAX_STEPS = 6
MAX_FILE_CHARS = 6000
MAX_DIR_ENTRIES = 120


# ===========================================================================
# Tools
# ===========================================================================

class ReadOnlyToolbox:
    """
    The three things the model is allowed to ask for.

    Every one goes through PolicyEngine.authorize_action() before it runs.
    read_file delegates to the project's existing ToolEngine so there is one
    code path for file access, not two.
    """

    def __init__(self, sandbox_root: Path = None, permission_level=PermissionLevel.READ_ONLY):
        self.root = Path(sandbox_root or BASE_DIR).resolve()
        self.permission_level = permission_level
        self.policy = PolicyEngine(default_profile="STRICT", sandbox_roots=[self.root])
        self.tools = ToolEngine(security_policy=self.policy)

    # -- descriptions handed to the model ---------------------------------

    SPECS = [
        {
            "name": "read_file",
            "args": {"path": "path to the file, relative to the project folder"},
            "description": "Read a text file and return its contents.",
        },
        {
            "name": "list_dir",
            "args": {"path": "folder path, or '.' for the project folder"},
            "description": "List the files and folders inside a folder.",
        },
        {
            "name": "system_status",
            "args": {},
            "description": "Report this computer's operating system, CPU count, and free disk space.",
        },
    ]

    def catalogue(self) -> str:
        lines = []
        for spec in self.SPECS:
            args = ", ".join(f'"{k}"' for k in spec["args"]) or "none"
            lines.append(f'- {spec["name"]}({args}) -- {spec["description"]}')
        return "\n".join(lines)

    def _resolve(self, path: str) -> str:
        """
        Anchor relative paths to the sandbox root, not the process working
        directory. Without this, launching UGOS from anywhere other than the
        project folder makes "." resolve outside the sandbox and every request
        gets refused for the wrong reason.
        """
        p = Path(path)
        return str(p if p.is_absolute() else (self.root / p))

    # -- dispatch ----------------------------------------------------------

    def run(self, name: str, args: Dict[str, Any], agent_id: str = "ag_reader_01") -> Dict[str, Any]:
        """Runs a tool request. Always returns a dict with 'allowed' and 'output'."""
        if name == "read_file":
            return self._read_file(str(args.get("path", "")).strip(), agent_id)
        if name == "list_dir":
            return self._list_dir(str(args.get("path", ".")).strip() or ".", agent_id)
        if name == "system_status":
            return self._system_status(agent_id)
        return {
            "allowed": False,
            "output": f"There is no tool called '{name}'. Available: "
                      + ", ".join(s["name"] for s in self.SPECS),
        }

    def _read_file(self, path: str, agent_id: str) -> Dict[str, Any]:
        if not path:
            return {"allowed": False, "output": "read_file needs a 'path'."}

        target = self._resolve(path)
        result = self.tools.execute_tool(
            tool_name="file_reader",
            agent_id=agent_id,
            permission_level=self.permission_level,
            target=target,
        )

        if result.get("status") == "DENIED":
            decision = self.policy.last_decision() or {}
            return {
                "allowed": False,
                "output": f"REFUSED by the security policy. {decision.get('reason', '')}".strip(),
            }
        if result.get("status") == "ERROR":
            return {"allowed": True, "output": f"Could not read it: {result.get('reason')}"}

        content = result.get("output", "")
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS] + f"\n... [truncated, file is {len(content)} characters]"
        return {"allowed": True, "output": content}

    def _list_dir(self, path: str, agent_id: str) -> Dict[str, Any]:
        target = self._resolve(path)
        allowed = self.policy.authorize_action(
            agent_id=agent_id,
            permission_level=self.permission_level,
            action=SecurityAction.READ_FILE,
            target=target,
        )
        if not allowed:
            decision = self.policy.last_decision() or {}
            return {
                "allowed": False,
                "output": f"REFUSED by the security policy. {decision.get('reason', '')}".strip(),
            }

        folder = Path(target)
        if not folder.is_dir():
            return {"allowed": True, "output": f"'{path}' is not a folder."}

        entries = []
        for item in sorted(folder.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if item.name in {".git", "__pycache__", ".pytest_cache"}:
                continue
            entries.append(f"{item.name}/" if item.is_dir() else f"{item.name}  ({item.stat().st_size} bytes)")
            if len(entries) >= MAX_DIR_ENTRIES:
                entries.append("... [more entries not shown]")
                break
        return {"allowed": True, "output": "\n".join(entries) or "(empty folder)"}

    def _system_status(self, agent_id: str) -> Dict[str, Any]:
        # No file is touched, so only the permission-level check applies.
        allowed = self.policy.authorize_action(
            agent_id=agent_id,
            permission_level=self.permission_level,
            action=SecurityAction.READ_FILE,
            target=None,
        )
        if not allowed:
            return {"allowed": False, "output": "REFUSED by the security policy."}

        try:
            usage = shutil.disk_usage(str(self.root))
            disk = (f"{usage.free / 1e9:.1f} GB free of {usage.total / 1e9:.1f} GB "
                    f"({usage.used / usage.total * 100:.0f}% used)")
        except Exception:
            disk = "unavailable"

        lines = [
            f"Operating system: {platform.system()} {platform.release()}",
            f"Machine: {platform.machine()}",
            f"Python: {platform.python_version()}",
            f"CPU cores: {os.cpu_count()}",
            f"Disk: {disk}",
            f"Project folder: {self.root}",
        ]
        try:
            import psutil  # optional
            mem = psutil.virtual_memory()
            lines.append(f"Memory: {mem.available / 1e9:.1f} GB available of {mem.total / 1e9:.1f} GB")
        except Exception:
            pass
        return {"allowed": True, "output": "\n".join(lines)}


# ===========================================================================
# The loop
# ===========================================================================

SYSTEM_PROMPT = """You are UGOS, an assistant that can inspect a project folder using tools.

TOOLS YOU MAY REQUEST:
{catalogue}

HOW TO REPLY -- this matters, read carefully:
Reply with ONE JSON object and nothing else. No explanation around it, no
markdown fences.

To use a tool:
{{"tool": "read_file", "args": {{"path": "ugos_config.py"}}}}

To give your final answer:
{{"answer": "your answer here"}}

RULES:
- If you can answer without a tool, answer immediately. Do not use tools for
  general knowledge questions.
- Request one tool at a time. You will be shown the result and can then
  request another or answer.
- A tool may be REFUSED by the security policy. That is normal and expected.
  Do not retry a refused request. Tell the user plainly that the security
  policy blocked it and why.
- You are read-only. You cannot create, modify or delete anything.
- After at most {max_steps} tool uses you must give a final answer."""


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Pulls the first JSON object out of a model reply, tolerating fences and chatter."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    depth, start = 0, None
    for i, ch in enumerate(cleaned):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    parsed = json.loads(cleaned[start:i + 1])
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    start = None
    return None


def run_agent(
    router,
    request: str,
    toolbox: Optional[ReadOnlyToolbox] = None,
    max_steps: int = MAX_STEPS,
) -> Dict[str, Any]:
    """
    Runs the think-act-observe cycle and returns the answer plus a full trace.

    The trace is the interesting part: every tool the model asked for, whether
    the policy allowed it, and why not when it did not.
    """
    toolbox = toolbox or ReadOnlyToolbox()
    system = SYSTEM_PROMPT.format(catalogue=toolbox.catalogue(), max_steps=max_steps)

    transcript = f"User request: {request}\n"
    steps: List[Dict[str, Any]] = []
    started = time.time()
    provider = model = None
    seen: List[str] = []

    for step_no in range(1, max_steps + 1):
        result = router.generate(transcript, system_prompt=system)
        provider = result.get("provider")
        model = result.get("model")

        if result.get("status") != "SUCCESS":
            return _finish("No provider could answer.", steps, provider, model, started, failed=True)

        raw = (result.get("content") or "").strip()
        parsed = _extract_json(raw)

        # Model ignored the format. Take its prose as the answer rather than
        # failing -- small models do this constantly.
        if parsed is None:
            return _finish(raw, steps, provider, model, started, malformed=True)

        if "answer" in parsed and "tool" not in parsed:
            return _finish(str(parsed["answer"]), steps, provider, model, started)

        name = str(parsed.get("tool", "")).strip()
        args = parsed.get("args") or {}
        if not isinstance(args, dict):
            args = {}

        signature = f"{name}:{json.dumps(args, sort_keys=True)}"
        if signature in seen:
            transcript += "\nYou already requested that and got the result above. Give your final answer now.\n"
            continue
        seen.append(signature)

        outcome = toolbox.run(name, args)
        steps.append({
            "step": step_no,
            "tool": name,
            "args": args,
            "allowed": outcome["allowed"],
            "output": outcome["output"][:1200],
        })

        verdict = "RESULT" if outcome["allowed"] else "REFUSED BY SECURITY POLICY"
        transcript += (
            f"\nYou requested: {name}({json.dumps(args)})\n"
            f"{verdict}:\n{outcome['output'][:MAX_FILE_CHARS]}\n"
        )

    transcript += "\nYou have used all your tool steps. Give your final answer now as {\"answer\": \"...\"}.\n"
    final = router.generate(transcript, system_prompt=system)
    parsed = _extract_json(final.get("content", "")) or {}
    answer = parsed.get("answer") or final.get("content") or "Ran out of steps without reaching an answer."
    return _finish(str(answer), steps, final.get("provider", provider), final.get("model", model), started)


def _finish(answer, steps, provider, model, started, failed=False, malformed=False) -> Dict[str, Any]:
    return {
        "answer": answer,
        "steps": steps,
        "provider": provider,
        "model": model,
        "seconds": round(time.time() - started, 1),
        "failed": failed,
        "malformed": malformed,
    }
