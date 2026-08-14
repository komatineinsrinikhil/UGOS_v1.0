"""
UGOS -- Run One Task
--------------------
Sends a single request through the full UGOS pipeline:

    your question
        -> Zero-Trust security check (is this agent allowed to make the call?)
        -> LLM router (local model first, mock fallback if it is down)
        -> persistent memory (answer saved to ugos_memory.db)

Usage:
    python run_my_task.py                       ask interactively
    python run_my_task.py "your question here"  ask directly
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
for _p in (str(BASE_DIR), str(BASE_DIR / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ugos.core.memory import MemoryEngine
from ugos.llm.router import LLMRouter, MockLLMProvider
from ugos.security.policy import SecurityAction
from ugos.agents.specialized import SoftwareEngineerAgent

from ugos_providers import OllamaLLMProvider, is_real_answer

MODEL_NAME = "phi3"
DEFAULT_PROMPT = "Write a 3-line Python function to compute the Fibonacci sequence."
SESSION_ID = "sess_cli_01"

LINE = "=" * 62


def get_prompt() -> str:
    """Command-line argument, else ask the user, else the default demo prompt."""
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

    prompt = get_prompt()

    # ------------------------------------------------------------------
    # 1. Core engines
    # ------------------------------------------------------------------
    memory = MemoryEngine(db_path=BASE_DIR / "ugos_memory.db")
    session = memory.get_or_create_session(SESSION_ID)
    agent = SoftwareEngineerAgent(name="DevBot")

    # ------------------------------------------------------------------
    # 2. Providers: real model first, mock as a safety net
    # ------------------------------------------------------------------
    ollama = OllamaLLMProvider(model_id=MODEL_NAME)
    router = LLMRouter(
        primary_provider=ollama,
        fallback_providers=[MockLLMProvider()],
    )

    # Friendly pre-flight so the failure is explained, not just thrown
    if not ollama.is_available():
        print("\n  [!] Ollama is not running on this machine.")
        print("      Open Ollama from the Start menu (look for the tray icon),")
        print("      or run:  ollama serve")
        print("      UGOS will still run, but only the mock provider can answer.\n")
    else:
        available = ollama.installed_models()
        if available and not any(m.split(":")[0] == MODEL_NAME for m in available):
            print(f"\n  [!] Model '{MODEL_NAME}' is not downloaded yet.")
            print(f"      Run:  ollama pull {MODEL_NAME}")
            print(f"      Currently installed: {', '.join(available)}\n")

    print(f"\nRequest: {prompt}")

    # ------------------------------------------------------------------
    # 3. Zero-Trust check -- this is a REAL policy decision.
    #
    #    The previous version called agent.can_execute(), a method that does
    #    not exist on BaseAgent. hasattr() returned False, the check was
    #    skipped, and the script printed "AUTHORIZED" without ever asking
    #    the PolicyEngine anything. evaluate_and_act() is the real gate.
    # ------------------------------------------------------------------
    verdict = agent.evaluate_and_act(
        action=SecurityAction.NETWORK_CALL,
        target=f"ollama://{MODEL_NAME}",
    )

    if verdict.get("status") != "SUCCESS":
        print(f"\n  [BLOCKED] {verdict.get('reason', 'Denied by security policy.')}")
        session.log_event(agent.agent_id, "llm_request_blocked", {"prompt": prompt})
        print(LINE + "\n")
        return 1

    print("  [SECURITY] Authorized by PolicyEngine.")
    print(f"  [ROUTER]   Sending to {MODEL_NAME} on this machine...")

    # ------------------------------------------------------------------
    # 4. Ask the model
    # ------------------------------------------------------------------
    result = router.generate(prompt)
    answer = result.get("content", "")

    print("\n" + "-" * 62)
    print(answer if answer else "(no content returned)")
    print("-" * 62)

    # ------------------------------------------------------------------
    # 5. Save ONLY if a real model answered.
    #
    #    The previous version printed "Success: persisted" no matter what,
    #    because router.generate() returns an error dict instead of raising.
    #    That wrote error messages into ugos_memory.db as if they were answers.
    # ------------------------------------------------------------------
    if is_real_answer(result):
        memory.set_global_fact(
            key=f"answer::{prompt[:60]}",
            value=answer,
            tags=[result.get("provider", "unknown"), result.get("model", MODEL_NAME)],
        )
        session.log_event(agent.agent_id, "llm_request", {"prompt": prompt, "provider": result.get("provider")})
        print(f"\n  [SAVED] Answer stored in ugos_memory.db (via {result.get('provider')}).")
        print(LINE + "\n")
        return 0

    if result.get("status") == "ERROR":
        print("\n  [FAILED] No provider could answer. Nothing was saved.")
    else:
        print(f"\n  [NOT SAVED] Answered by '{result.get('provider')}', which is a")
        print("              placeholder, not a real model. Real answers only get saved.")
    print(LINE + "\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
