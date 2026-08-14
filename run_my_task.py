"""
UGOS -- Run One Task
====================
Sends a single request through the full UGOS pipeline:

    your request
        -> Zero-Trust security check (is this agent allowed to make the call?)
        -> LLM router (primary brain, then fallback, then mock)
        -> persistent memory (real answers saved to ugos_memory.db)

Which brain is used is set in ugos_config.py.

Usage:
    python run_my_task.py                       ask interactively
    python run_my_task.py "your request here"   ask directly
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
for _p in (str(BASE_DIR), str(BASE_DIR / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ugos.core.memory import MemoryEngine
from ugos.security.policy import SecurityAction
from ugos.agents.specialized import SoftwareEngineerAgent

import ugos_config as cfg
from ugos_providers import build_router, describe_setup, is_real_answer

DEFAULT_PROMPT = "Write a 3-line Python function to compute the Fibonacci sequence."
SESSION_ID = "sess_cli_01"
LINE = "=" * 64


def show_setup() -> None:
    """Prints which brain is active and whether it is actually usable."""
    setup = describe_setup()

    for role in ("primary", "fallback"):
        info = setup.get(role)
        if not info:
            continue
        where = "on this machine" if info.get("local") else "over the internet"
        mark = "OK " if info["ready"] else "!! "
        print(f"  {mark}{role:9} {info['name']} ({info['model']}) {where}")
        if info.get("problem"):
            print(f"             -> {info['problem']}")

    if not setup["primary"]["ready"] and not (setup["fallback"] or {}).get("ready"):
        print("\n  No working brain. UGOS will run, but nothing real can answer.")
        print("  Edit ugos_config.py to pick a different one.")


def get_prompt() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()
    try:
        typed = input("\nWhat would you like UGOS to do?\n(press Enter for the demo task)\n> ").strip()
    except EOFError:
        return DEFAULT_PROMPT
    return typed or DEFAULT_PROMPT


def main() -> int:
    print("\n" + LINE)
    print(" UGOS -- Task Execution under Zero-Trust Security")
    print(LINE)

    show_setup()
    prompt = get_prompt()

    memory = MemoryEngine(db_path=BASE_DIR / "ugos_memory.db")
    session = memory.get_or_create_session(SESSION_ID)
    agent = SoftwareEngineerAgent(name="DevBot")
    router = build_router()

    print(f"\nRequest: {prompt}")

    # ------------------------------------------------------------------
    # Zero-Trust check -- a REAL policy decision.
    #
    # The original called agent.can_execute(), a method BaseAgent does not
    # have. The hasattr() guard fell through to authorized = True, so this
    # printed "AUTHORIZED" without consulting the PolicyEngine at all.
    # ------------------------------------------------------------------
    verdict = agent.evaluate_and_act(
        action=SecurityAction.NETWORK_CALL,
        target=f"{cfg.PRIMARY}://{cfg.MODELS.get(cfg.PRIMARY, '')}",
    )
    if verdict.get("status") != "SUCCESS":
        print(f"\n  [BLOCKED] {verdict.get('reason', 'Denied by security policy.')}")
        session.log_event(agent.agent_id, "llm_request_blocked", {"prompt": prompt})
        print(LINE + "\n")
        return 1

    print("  [SECURITY] Authorized by PolicyEngine.")
    print("  [ROUTER]   Thinking...")

    result = router.generate(prompt)
    answer = result.get("content", "")

    print("\n" + "-" * 64)
    print(answer if answer else "(no content returned)")
    print("-" * 64)

    # ------------------------------------------------------------------
    # Save ONLY if a real model answered.
    #
    # The original printed "Success: persisted" unconditionally, because
    # router.generate() returns an error dict instead of raising -- so
    # failures were written into ugos_memory.db as if they were answers.
    # ------------------------------------------------------------------
    if is_real_answer(result):
        memory.set_global_fact(
            key=f"answer::{prompt[:60]}",
            value=answer,
            tags=[result.get("provider", "unknown"), result.get("model", "")],
        )
        session.log_event(
            agent.agent_id, "llm_request",
            {"prompt": prompt, "provider": result.get("provider")},
        )
        print(f"\n  [SAVED] Stored in ugos_memory.db -- answered by {result.get('provider')}.")
        print(LINE + "\n")
        return 0

    if result.get("status") == "ERROR":
        print("\n  [FAILED] No provider could answer. Nothing was saved.")
    else:
        print(f"\n  [NOT SAVED] Answered by '{result.get('provider')}', a placeholder")
        print("              rather than a real model. Only real answers are saved.")
    print(LINE + "\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
