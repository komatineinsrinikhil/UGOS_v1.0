"""
UGOS Local Provider Bindings
-----------------------------
Real (non-mock) LLM providers for UGOS.

Why this file exists:
    src/ugos/llm/router.py ships with MockLLMProvider and SimulatedAPIProvider.
    Both are fake -- they return canned text and never contact an AI.
    They are useful for testing the plumbing, but they cannot answer anything.

    This file holds providers that talk to a REAL model. Keeping them here means
    every UGOS entry point (run_my_task.py, ugos_web.py, main.py) shares one
    implementation instead of each defining its own.

Contract note:
    BaseLLMProvider.complete() must return a DICTIONARY, the same shape that
    MockLLMProvider and SimulatedAPIProvider return. An earlier version of the
    Ollama provider returned a plain string, which broke any caller that did
    response["provider"] -- including src/ugos/main.py line 65.
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent
for _p in (str(BASE_DIR), str(BASE_DIR / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from ugos.llm.router import BaseLLMProvider
except ModuleNotFoundError:  # pragma: no cover
    from src.ugos.llm.router import BaseLLMProvider


DEFAULT_OLLAMA_HOST = "http://localhost:11434"


class OllamaLLMProvider(BaseLLMProvider):
    """Talks to an Ollama server running on this machine (no internet required)."""

    def __init__(
        self,
        model_id: str = "phi3",
        host: str = DEFAULT_OLLAMA_HOST,
        timeout: int = 120,
    ):
        super().__init__(provider_name="OllamaLocal", model_id=model_id)
        self.host = host.rstrip("/")
        self.timeout = timeout

    def is_available(self) -> bool:
        """True if the Ollama server is up. Used for a friendly pre-flight check."""
        try:
            with urllib.request.urlopen(self.host, timeout=3):
                return True
        except Exception:
            return False

    def installed_models(self) -> list:
        """Model names currently downloaded on this machine."""
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Sends the prompt to Ollama and returns a UGOS-shaped response dict."""
        body: Dict[str, Any] = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            body["system"] = system_prompt

        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:200]
            raise RuntimeError(
                f"Ollama rejected the request ({exc.code}). "
                f"Is the model '{self.model_id}' downloaded? "
                f"Run: ollama pull {self.model_id}. Detail: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Ollama is not reachable at {self.host}. "
                f"Start Ollama from the Start menu, or run: ollama serve. ({exc})"
            ) from exc

        content = payload.get("response", "")
        if not content.strip():
            raise RuntimeError("Ollama returned an empty response.")

        return {
            "status": "SUCCESS",
            "provider": self.provider_name,
            "model": self.model_id,
            "content": content,
            "usage": {
                "prompt_tokens": payload.get("prompt_eval_count", 0),
                "completion_tokens": payload.get("eval_count", 0),
            },
        }


def is_real_answer(result: Dict[str, Any]) -> bool:
    """
    True only if a genuine model answered.

    The router falls back to MockLLMProvider when the real provider fails.
    A mock reply still carries status SUCCESS, so status alone is NOT enough
    to decide whether anything actually got answered.
    """
    if not isinstance(result, dict):
        return False
    if result.get("status") != "SUCCESS":
        return False
    provider = (result.get("provider") or "").lower()
    return "mock" not in provider and "simulated" not in provider
