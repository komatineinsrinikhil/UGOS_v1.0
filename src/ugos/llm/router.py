"""
UGOS_500: LLM Provider Bindings & Router Architecture
-----------------------------------------------------
Provides unified LLM provider abstractions, model-agnostic routing,
and automated fallback capabilities for local or remote inference.
"""

import sys
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class BaseLLMProvider(ABC):
    """Abstract interface for all UGOS LLM backends."""

    def __init__(self, provider_name: str, model_id: str):
        self.provider_name = provider_name
        self.model_id = model_id

    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generates a text completion for a given prompt."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """Local deterministic mock LLM provider for testing and offline fallback."""

    def __init__(self, model_id: str = "mock-ugos-v1"):
        super().__init__(provider_name="MockLocalProvider", model_id=model_id)

    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        logging.info(f"[{self.provider_name}] Processing completion request...")
        return {
            "status": "SUCCESS",
            "provider": self.provider_name,
            "model": self.model_id,
            "content": f"[MOCK RESPONSE] Handled prompt: '{prompt[:40]}...'",
            "usage": {"prompt_tokens": len(prompt.split()), "completion_tokens": 12}
        }


class SimulatedAPIProvider(BaseLLMProvider):
    """Simulated remote API provider to test failover logic."""

    def __init__(self, model_id: str = "gpt-4o", should_fail: bool = False):
        super().__init__(provider_name="SimulatedAPIProvider", model_id=model_id)
        self.should_fail = should_fail

    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if self.should_fail:
            logging.warning(f"[{self.provider_name}] API call failed! Triggering fallback.")
            raise RuntimeError("API Connection Timeout or Auth Error")

        logging.info(f"[{self.provider_name}] API completion successful.")
        return {
            "status": "SUCCESS",
            "provider": self.provider_name,
            "model": self.model_id,
            "content": f"[API RESPONSE] Processed prompt successfully via {self.model_id}.",
            "usage": {"prompt_tokens": len(prompt.split()), "completion_tokens": 15}
        }


class LLMRouter:
    """Manages primary and fallback LLM providers for robust task completion."""

    def __init__(self, primary_provider: BaseLLMProvider, fallback_providers: Optional[List[BaseLLMProvider]] = None):
        self.primary_provider = primary_provider
        self.fallback_providers = fallback_providers or []
        logging.info(f"LLMRouter initialized | Primary: {self.primary_provider.provider_name}")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Attempts completion via primary provider, falling back sequentially on error."""
        providers_to_try = [self.primary_provider] + self.fallback_providers

        for provider in providers_to_try:
            try:
                result = provider.complete(prompt=prompt, system_prompt=system_prompt, **kwargs)
                return result
            except Exception as e:
                logging.warning(f"Provider {provider.provider_name} failed: {e}")

        return {
            "status": "ERROR",
            "content": "All LLM providers in fallback chain failed.",
            "provider": None
        }


if __name__ == "__main__":
    print("\n--- Testing UGOS LLM Router & Fallback Mechanism ---")

    # Scenario 1: Primary API succeeds
    primary_api = SimulatedAPIProvider(model_id="gpt-4o", should_fail=False)
    local_fallback = MockLLMProvider()
    
    router = LLMRouter(primary_provider=primary_api, fallback_providers=[local_fallback])
    res1 = router.generate("Analyze system architecture security policies.")
    print("\n[Scenario 1 - Primary API Success]:", res1)

    # Scenario 2: Primary API fails, fallback triggers
    failing_api = SimulatedAPIProvider(model_id="gpt-4o", should_fail=True)
    fallback_router = LLMRouter(primary_provider=failing_api, fallback_providers=[local_fallback])
    res2 = fallback_router.generate("Generate unified patch diff for file_writer.")
    print("\n[Scenario 2 - Fallback to Local Mock]:", res2)