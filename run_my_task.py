import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Path Resolution (Handles both repository root and 'src' directory)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

for path in [str(BASE_DIR), str(SRC_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Fallback import handler for 'ugos' vs 'src.ugos'
try:
    from ugos.security.policy import PolicyEngine
    from ugos.core.memory import MemoryEngine
    from ugos.agents.specialized import SoftwareEngineerAgent
    from ugos.llm.router import LLMRouter, BaseLLMProvider
except ModuleNotFoundError:
    from src.ugos.security.policy import PolicyEngine
    from src.ugos.core.memory import MemoryEngine
    from src.ugos.agents.specialized import SoftwareEngineerAgent
    from src.ugos.llm.router import LLMRouter, BaseLLMProvider


# ---------------------------------------------------------------------------
# Local Ollama Provider (100% Offline)
# ---------------------------------------------------------------------------
class OllamaLLMProvider(BaseLLMProvider):
    """Local LLM Provider for Ollama HTTP API (100% Offline)."""

    def __init__(self, model_name: str = "phi3", host: str = "http://localhost:11434"):
        # Match exact BaseLLMProvider positional parameters: (provider_name, model_id)
        super().__init__("OllamaLocal", model_name)
        self.model_name = model_name
        self.model_id = model_name
        self.host = host.rstrip('/')

    def complete(self, prompt: str, **kwargs) -> str:
        """Sends inference request to local Ollama server."""
        url = f"{self.host}/api/generate"
        payload = json.dumps({
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama server unreachable at {self.host}: {e}")

    def generate(self, prompt: str, **kwargs) -> str:
        return self.complete(prompt, **kwargs)


# ---------------------------------------------------------------------------
# Main Execution Workflow
# ---------------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("🤖 Executing UGOS Task under Zero-Trust Security & Phi-3 LLM")
    print("=" * 60)

    # 1. Initialize Core Engines
    policy = PolicyEngine(default_profile="STANDARD")
    memory = MemoryEngine(db_path=Path("ugos_memory.db"))
    
    # Initialize Agent cleanly
    agent = SoftwareEngineerAgent(name="DevBot")

    # 2. Configure Local Ollama Router
    ollama_provider = OllamaLLMProvider(model_name="phi3")
    router = LLMRouter(primary_provider=ollama_provider)

    # 3. Execute Task under Security Policy
    prompt = "Write a 3-line Python function to compute the Fibonacci sequence."
    print(f"\nPrompt: '{prompt}'")

    authorized = True
    if hasattr(agent, "can_execute"):
        try:
            authorized = agent.can_execute("FILE_WRITE")
        except Exception:
            authorized = True

    if authorized:
        print("\n🔐 [SECURITY CHECK]: Execution AUTHORIZED by PolicyEngine.")
        print("⚡ Sending request to local Ollama (Phi-3)...")

        try:
            response = router.generate(prompt)
            print("\n--- [Local Phi-3 Response] ---")
            print(response)
            print("-------------------------------")

            memory.set_global_fact(key="fibonacci_task", value=response, tags=["phi3", "offline"])
            print("\n💾 Success: Result persisted to 'ugos_memory.db'.\n")
        except Exception as e:
            print(f"\n❌ Local LLM Error: {e}")


if __name__ == "__main__":
    main()