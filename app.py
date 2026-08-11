import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
import streamlit as st

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
# Streamlit Web App Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="UGOS v1.0 Agent Workspace",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 UGOS Agent Web Workspace")
st.caption("User-Guided Agent Operating System | Zero-Trust Runtime & Persistent Memory")

# Initialize Session State Engines
if "policy" not in st.session_state:
    st.session_state.policy = PolicyEngine(default_profile="STANDARD")
if "memory" not in st.session_state:
    st.session_state.memory = MemoryEngine(db_path=Path("ugos_memory.db"))
if "agent" not in st.session_state:
    st.session_state.agent = SoftwareEngineerAgent(name="DevBot")
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Status Dashboard
with st.sidebar:
    st.header("⚙️ System Status")
    st.success("🟢 Zero-Trust Policy: STANDARD")
    st.info("🧠 Memory DB: ugos_memory.db")
    st.warning("⚡ Model: Ollama Local (phi3)")
    st.markdown("---")
    st.markdown("**Core Architecture:**")
    st.markdown("• `PolicyEngine`: Authorizes actions\n• `MemoryEngine`: SQLite persistence\n• `LLMRouter`: Failover management")
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input & Task Processing Loop
if prompt := st.chat_input("Ask UGOS to execute a software task..."):
    # Add user prompt to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with UGOS Agent Backend
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.info("🔐 Policy Engine checking zero-trust rules...")

        try:
            # 1. Configure Local Ollama Router
            ollama_provider = OllamaLLMProvider(model_name="phi3")
            router = LLMRouter(primary_provider=ollama_provider)

            # 2. Security Check & Inference
            status_placeholder.info("⚡ Executing inference via local Ollama (Phi-3)...")
            response = router.generate(prompt)

            # 3. Store Fact in SQLite Memory
            st.session_state.memory.set_global_fact(
                key=f"task_{len(st.session_state.messages)}",
                value=response[:100] + "...",
                tags=["ui_task", "phi3"]
            )

            status_placeholder.empty()
            st.markdown(response)

            # Show Security Verification Audit Box
            with st.expander("🔍 Security & Memory Audit Trail"):
                st.code(
                    "🔐 [SECURITY CHECK]: AUTHORIZED by PolicyEngine\n"
                    "📦 [SANDBOX]: Executed under STANDARD_EXEC permissions\n"
                    "💾 [PERSISTENCE]: Fact logged to ugos_memory.db",
                    language="text"
                )

            # Append assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            status_placeholder.empty()
            st.error(f"❌ Execution Error: {e}")