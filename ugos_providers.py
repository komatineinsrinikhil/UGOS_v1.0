"""
UGOS Provider Bindings
======================
Real (non-mock) LLM providers, plus the factory that builds the router.

Three provider classes cover essentially the whole market:

    OllamaLLMProvider        Ollama running on this machine
    OpenAICompatibleProvider Groq, OpenRouter, OpenAI, Together, LM Studio,
                             Jan -- anything speaking the OpenAI dialect
    GeminiProvider           Google Gemini (its own request format)

Which one is used is decided in ugos_config.py, not here.

Contract:
    BaseLLMProvider.complete() must return a DICTIONARY of the same shape
    MockLLMProvider returns. A provider that returns a bare string breaks any
    caller doing response["provider"] -- including src/ugos/main.py line 65.
"""

import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
for _p in (str(BASE_DIR), str(BASE_DIR / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ugos.llm.router import BaseLLMProvider, LLMRouter, MockLLMProvider

import ugos_config as cfg


# ===========================================================================
# HTTP
# ===========================================================================

def _urlopen(req, timeout: int, retries: int = 1):
    """
    urlopen that retries once on 429.

    Free tiers rate limit per minute, and the agent loop makes several calls
    per question, so a single 429 is usually a brief wait rather than a real
    failure. Honours Retry-After when the service sends it.
    """
    for attempt in range(retries + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt >= retries:
                raise
            try:
                wait = float(exc.headers.get("Retry-After", 2))
            except (TypeError, ValueError):
                wait = 2.0
            logging.warning(f"Rate limited (429). Waiting {min(wait, 30):.0f}s and retrying once.")
            time.sleep(min(wait, 30))


# ===========================================================================
# Secrets
# ===========================================================================

def load_env_file(path: Path = BASE_DIR / ".env") -> None:
    """
    Reads KEY=VALUE lines from .env into the environment.

    Kept deliberately tiny so no third-party package is needed. Real
    environment variables always win over the file, so you can override a
    key for one run without editing anything.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_api_key(service: str) -> Optional[str]:
    """Returns the key for a service, or None if it is not set."""
    load_env_file()
    name = cfg.KEY_NAMES.get(service)
    if not name:
        return None
    value = os.environ.get(name, "").strip()
    return value or None


# ===========================================================================
# Providers
# ===========================================================================

class OllamaLLMProvider(BaseLLMProvider):
    """Ollama on this machine. No internet, no key, no cost."""

    def __init__(self, model_id: str = "phi3", host: str = None, timeout: int = None):
        super().__init__(provider_name="Ollama", model_id=model_id)
        self.host = (host or cfg.OLLAMA_HOST).rstrip("/")
        # Local models on CPU are slow, and the agent loop sends a much larger
        # prompt than a plain question. 120s was not enough for phi3.
        self.timeout = timeout or getattr(cfg, "LOCAL_TIMEOUT_SECONDS", 300)

    def is_available(self) -> bool:
        try:
            with urllib.request.urlopen(self.host, timeout=3):
                return True
        except Exception:
            return False

    def installed_models(self) -> List[str]:
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=5) as r:
                data = json.loads(r.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []

    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": False,
            # Caps runaway generation. Small models will happily ramble for
            # thousands of tokens, which is most of where the wait goes.
            "options": {"num_predict": getattr(cfg, "LOCAL_MAX_TOKENS", 800)},
        }
        if system_prompt:
            body["system"] = system_prompt

        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Ollama rejected the request ({exc.code}). "
                f"Is '{self.model_id}' downloaded? Run: ollama pull {self.model_id}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Ollama is not reachable at {self.host}. "
                f"Open Ollama from the Start menu, or run: ollama serve ({exc})"
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


class OpenAICompatibleProvider(BaseLLMProvider):
    """
    One class for every service speaking the OpenAI dialect.

    Cloud: Groq, OpenRouter, OpenAI, Together.
    Local: LM Studio, Jan, llama.cpp server, llamafile.

    Only the address and the key differ, which is why they all live in
    ugos_config.ENDPOINTS rather than in code.
    """

    def __init__(
        self,
        service: str,
        model_id: str,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 120,
    ):
        super().__init__(provider_name=service.capitalize(), model_id=model_id)
        self.service = service
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def is_available(self) -> bool:
        """Local servers: is anything listening? Cloud: do we have a key?"""
        if self.service in cfg.NEEDS_KEY:
            return bool(self.api_key)
        try:
            with urllib.request.urlopen(f"{self.base_url}/models", timeout=3):
                return True
        except Exception:
            return False

    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if self.service in cfg.NEEDS_KEY and not self.api_key:
            raise RuntimeError(
                f"No API key for {self.service}. Put "
                f"{cfg.KEY_NAMES.get(self.service, 'THE_KEY')}=... in your .env file."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.service == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/komatineinsrinikhil/UGOS_v1.0"
            headers["X-Title"] = "UGOS"

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps({"model": self.model_id, "messages": messages}).encode("utf-8"),
            headers=headers,
        )
        try:
            with _urlopen(req, self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:250]
            hint = ""
            if exc.code in (401, 403):
                hint = " -- the API key looks wrong or expired."
            elif exc.code == 429:
                hint = (" -- rate limit still hit after a retry. Free tiers count per minute; "
                        "wait a moment, or switch PRIMARY in ugos_config.py to a service with "
                        "a higher free limit such as groq.")
            elif exc.code == 404:
                hint = f" -- the model '{self.model_id}' may not exist on this service."
            raise RuntimeError(f"{self.provider_name} returned {exc.code}{hint} {detail}") from exc
        except urllib.error.URLError as exc:
            where = "the internet" if self.service in cfg.NEEDS_KEY else self.base_url
            raise RuntimeError(f"Could not reach {where} for {self.provider_name}. ({exc})") from exc

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"{self.provider_name} sent an unexpected reply: {str(payload)[:200]}") from exc

        if not content or not content.strip():
            raise RuntimeError(f"{self.provider_name} returned an empty response.")

        usage = payload.get("usage") or {}
        return {
            "status": "SUCCESS",
            "provider": self.provider_name,
            "model": payload.get("model", self.model_id),
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini. Its own request format, so it needs its own class."""

    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model_id: str = "gemini-3.5-flash", api_key: Optional[str] = None, timeout: int = 120):
        super().__init__(provider_name="Gemini", model_id=model_id)
        self.api_key = api_key
        self.timeout = timeout

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError(
                "No Gemini API key. Put GEMINI_API_KEY=... in your .env file. "
                "Get one free at https://aistudio.google.com/apikey"
            )

        body: Dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        req = urllib.request.Request(
            f"{self.ENDPOINT}/{self.model_id}:generateContent",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
        )
        try:
            with _urlopen(req, self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:250]
            hint = ""
            if exc.code in (400, 401, 403):
                hint = " -- the API key looks wrong, or the Gemini API is not enabled for it."
            elif exc.code == 429:
                hint = (" -- rate limit still hit after a retry. Gemini's free tier counts per "
                        "minute; wait a moment, or try groq, which allows more.")
            elif exc.code == 404:
                hint = f" -- model '{self.model_id}' not found. Check MODELS in ugos_config.py."
            raise RuntimeError(f"Gemini returned {exc.code}{hint} {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach Gemini. Are you online? ({exc})") from exc

        try:
            content = payload["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            blocked = payload.get("promptFeedback", {}).get("blockReason")
            if blocked:
                raise RuntimeError(f"Gemini refused the request (reason: {blocked}).") from exc
            raise RuntimeError(f"Gemini sent an unexpected reply: {str(payload)[:200]}") from exc

        usage = payload.get("usageMetadata") or {}
        return {
            "status": "SUCCESS",
            "provider": self.provider_name,
            "model": self.model_id,
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
            },
        }


# ===========================================================================
# Factory
# ===========================================================================

def build_provider(name: Optional[str]) -> Optional[BaseLLMProvider]:
    """Turns a name from ugos_config into a ready provider. None if unknown."""
    if not name:
        return None
    name = name.lower().strip()
    model = cfg.MODELS.get(name, "")

    if name == "ollama":
        return OllamaLLMProvider(model_id=model or "phi3")
    if name == "gemini":
        return GeminiProvider(model_id=model or "gemini-3.5-flash", api_key=get_api_key("gemini"))
    if name in cfg.ENDPOINTS:
        return OpenAICompatibleProvider(
            service=name,
            model_id=model,
            base_url=cfg.ENDPOINTS[name],
            api_key=get_api_key(name),
        )
    return None


class RecordingRouter(LLMRouter):
    """
    LLMRouter that remembers why each provider failed.

    The stock router logs failures to the console and returns the next
    provider's answer, so a caller sees a mock reply with no explanation.
    That is how a 120-second Ollama timeout showed up in the web page as
    "this came from a placeholder" and nothing else.
    """

    def __init__(self, primary_provider, fallback_providers=None):
        super().__init__(primary_provider, fallback_providers)
        self.last_errors: List[Dict[str, str]] = []

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        self.last_errors = []
        for provider in [self.primary_provider] + self.fallback_providers:
            try:
                return provider.complete(prompt=prompt, system_prompt=system_prompt, **kwargs)
            except Exception as exc:
                message = str(exc)
                if "timed out" in message.lower() or "timeout" in message.lower():
                    message = (f"{provider.model_id} did not reply in time. Local models are slow on "
                               f"CPU; try a smaller model, or switch to a cloud brain in ugos_config.py.")
                self.last_errors.append({"provider": provider.provider_name, "error": message[:400]})
                logging.warning(f"Provider {provider.provider_name} failed: {exc}")
        return {"status": "ERROR", "content": "All LLM providers in the fallback chain failed.", "provider": None}


def build_router_for(service: str, api_key: Optional[str], allow_mock: bool = False) -> LLMRouter:
    """
    Router for a caller-supplied key -- the public demo path.

    The server holds no key in this mode. Whatever the visitor pastes is used
    for that one request and never stored, logged, or written to disk.
    """
    service = (service or "").lower().strip()
    model = cfg.MODELS.get(service, "")

    if service == "gemini":
        provider = GeminiProvider(model_id=model or "gemini-3.5-flash", api_key=api_key)
    elif service in cfg.ENDPOINTS:
        provider = OpenAICompatibleProvider(
            service=service, model_id=model,
            base_url=cfg.ENDPOINTS[service], api_key=api_key,
        )
    else:
        raise RuntimeError(f"Unknown service '{service}'.")

    fallbacks = [MockLLMProvider()] if allow_mock else []
    return RecordingRouter(primary_provider=provider, fallback_providers=fallbacks)


def public_services() -> List[Dict[str, str]]:
    """Services a visitor can supply their own key for, with where to get one."""
    where = {
        "gemini": "https://aistudio.google.com/apikey",
        "groq": "https://console.groq.com/keys",
        "openrouter": "https://openrouter.ai/keys",
        "openai": "https://platform.openai.com/api-keys",
        "together": "https://api.together.xyz/settings/api-keys",
    }
    return [
        {"id": s, "model": cfg.MODELS.get(s, ""), "keyUrl": where.get(s, "")}
        for s in ("gemini", "groq", "openrouter", "openai", "together")
    ]


def build_router() -> LLMRouter:
    """Assembles the router described by ugos_config.py."""
    primary = build_provider(cfg.PRIMARY)
    if primary is None:
        raise RuntimeError(
            f"PRIMARY = '{cfg.PRIMARY}' in ugos_config.py is not a known brain. "
            f"Valid options: ollama, gemini, {', '.join(cfg.ENDPOINTS)}"
        )

    fallbacks: List[BaseLLMProvider] = []
    secondary = build_provider(cfg.FALLBACK)
    if secondary is not None:
        fallbacks.append(secondary)
    if getattr(cfg, "ALLOW_MOCK_FALLBACK", True):
        fallbacks.append(MockLLMProvider())

    return RecordingRouter(primary_provider=primary, fallback_providers=fallbacks)


def describe_setup() -> Dict[str, Any]:
    """Plain description of the active setup, for status displays."""
    def one(name):
        if not name:
            return None
        p = build_provider(name)
        if p is None:
            return {"name": name, "model": "?", "ready": False, "problem": "unknown brain"}

        ready = p.is_available()
        problem = None
        if not ready:
            if name in cfg.NEEDS_KEY:
                problem = f"no API key ({cfg.KEY_NAMES.get(name)} missing from .env)"
            elif name == "ollama":
                problem = "Ollama is not running"
            else:
                problem = f"nothing is listening at {cfg.ENDPOINTS.get(name, '?')}"
        elif name == "ollama":
            installed = p.installed_models()
            wanted = cfg.MODELS.get("ollama", "")
            if installed and not any(m.split(":")[0] == wanted for m in installed):
                ready, problem = False, f"model not downloaded -- run: ollama pull {wanted}"

        return {
            "name": name,
            "model": cfg.MODELS.get(name, ""),
            "local": name not in cfg.NEEDS_KEY,
            "ready": ready,
            "problem": problem,
        }

    return {
        "primary": one(cfg.PRIMARY),
        "fallback": one(cfg.FALLBACK),
        "mockAllowed": getattr(cfg, "ALLOW_MOCK_FALLBACK", True),
    }


def is_real_answer(result: Dict[str, Any]) -> bool:
    """
    True only if a genuine model answered.

    The router falls back to MockLLMProvider when real providers fail, and a
    mock reply still carries status SUCCESS -- so status alone is not enough.
    """
    if not isinstance(result, dict) or result.get("status") != "SUCCESS":
        return False
    provider = (result.get("provider") or "").lower()
    return "mock" not in provider and "simulated" not in provider
