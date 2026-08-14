"""
UGOS -- Local Web Interface
----------------------------
A type-in-a-box front end for UGOS. No command line needed after startup.

    python ugos_web.py

Opens http://localhost:8000 in your browser. Everything runs on this machine:
no internet, no accounts, no data leaves the computer.

Built only on Python's standard library -- nothing to pip install.
"""

import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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

HOST = "127.0.0.1"
PORT = 8000
MODEL_NAME = "phi3"
SESSION_ID = "sess_web_01"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UGOS</title>
<style>
  :root {
    --bg: #0f1216; --panel: #171b21; --line: #262c35;
    --text: #e6e9ee; --muted: #939ba7; --accent: #5b9dff;
    --ok: #3fb950; --warn: #d29922; --bad: #f85149;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font: 15px/1.55 -apple-system, "Segoe UI", Roboto, sans-serif;
    display: flex; justify-content: center; padding: 40px 20px;
  }
  .wrap { width: 100%; max-width: 780px; }
  h1 { font-size: 22px; margin: 0 0 4px; letter-spacing: -0.01em; }
  .sub { color: var(--muted); font-size: 13px; margin-bottom: 24px; }
  .status {
    display: flex; align-items: center; gap: 8px; padding: 10px 14px;
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 8px; font-size: 13px; margin-bottom: 18px;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); flex: none; }
  .dot.ok { background: var(--ok); } .dot.bad { background: var(--bad); }
  .dot.warn { background: var(--warn); }
  textarea {
    width: 100%; min-height: 110px; resize: vertical; padding: 14px;
    background: var(--panel); color: var(--text);
    border: 1px solid var(--line); border-radius: 8px;
    font: inherit; outline: none;
  }
  textarea:focus { border-color: var(--accent); }
  .row { display: flex; gap: 12px; align-items: center; margin-top: 12px; }
  button {
    background: var(--accent); color: #06101f; border: 0;
    padding: 11px 22px; border-radius: 8px;
    font: 600 14px inherit; cursor: pointer;
  }
  button:disabled { opacity: 0.5; cursor: default; }
  .hint { color: var(--muted); font-size: 12px; }
  .out {
    margin-top: 22px; background: var(--panel); border: 1px solid var(--line);
    border-radius: 8px; padding: 18px; display: none;
  }
  .out.show { display: block; }
  .meta {
    display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px;
    color: var(--muted); border-top: 1px solid var(--line);
    margin-top: 14px; padding-top: 12px;
  }
  pre {
    margin: 0; white-space: pre-wrap; word-wrap: break-word;
    font: 13.5px/1.6 "Cascadia Mono", Consolas, monospace;
  }
  .banner { padding: 10px 12px; border-radius: 6px; font-size: 13px; margin-bottom: 14px; }
  .banner.bad  { background: rgba(248,81,73,0.12);  color: #ff9a94; }
  .banner.warn { background: rgba(210,153,34,0.12); color: #e3b341; }
</style>
</head>
<body>
<div class="wrap">
  <h1>UGOS</h1>
  <div class="sub">Every request passes a security check, then goes to a model running on this machine.</div>

  <div class="status">
    <span class="dot" id="dot"></span>
    <span id="statusText">Checking...</span>
  </div>

  <textarea id="prompt" placeholder="Ask UGOS to do something. For example: write a Python function that reverses a list"></textarea>
  <div class="row">
    <button id="go">Run</button>
    <span class="hint">Ctrl+Enter also runs it</span>
  </div>

  <div class="out" id="out">
    <div id="banner"></div>
    <pre id="answer"></pre>
    <div class="meta" id="meta"></div>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);

async function refreshStatus() {
  try {
    const s = await (await fetch('/status')).json();
    if (!s.serverUp) {
      $('dot').className = 'dot bad';
      $('statusText').textContent = 'Ollama is not running. Open it from the Start menu, then reload.';
    } else if (!s.modelReady) {
      $('dot').className = 'dot warn';
      $('statusText').textContent = 'Ollama is running, but ' + s.model + ' is not downloaded. Run: ollama pull ' + s.model;
    } else {
      $('dot').className = 'dot ok';
      $('statusText').textContent = 'Ready \\u2014 ' + s.model + ' running locally, offline.';
    }
  } catch (e) {
    $('dot').className = 'dot bad';
    $('statusText').textContent = 'Cannot reach UGOS.';
  }
}

async function run() {
  const prompt = $('prompt').value.trim();
  if (!prompt) return;

  $('go').disabled = true;
  $('go').textContent = 'Working...';
  $('out').className = 'out show';
  $('banner').innerHTML = '';
  $('answer').textContent = 'Thinking. The first request takes longer while the model loads.';
  $('meta').textContent = '';

  try {
    const r = await fetch('/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt})
    });
    const d = await r.json();

    $('answer').textContent = d.answer || '(no answer)';

    if (d.blocked) {
      $('banner').className = 'banner bad';
      $('banner').textContent = 'Blocked by the security policy before anything ran.';
    } else if (!d.real) {
      $('banner').className = 'banner warn';
      $('banner').textContent = 'This came from a placeholder, not a real model. Not saved to memory.';
    } else {
      $('banner').className = '';
      $('banner').textContent = '';
    }

    const bits = [];
    if (d.provider) bits.push('Answered by: ' + d.provider);
    if (d.seconds)  bits.push(d.seconds + 's');
    bits.push(d.saved ? 'Saved to memory' : 'Not saved');
    $('meta').textContent = bits.join('   \\u00b7   ');
  } catch (e) {
    $('banner').className = 'banner bad';
    $('banner').textContent = 'Request failed: ' + e.message;
    $('answer').textContent = '';
  } finally {
    $('go').disabled = false;
    $('go').textContent = 'Run';
  }
}

$('go').onclick = run;
$('prompt').addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'Enter') run();
});
refreshStatus();
</script>
</body>
</html>
"""


class UGOS:
    """Holds the engines once, so they are not rebuilt on every request."""

    def __init__(self):
        self.memory = MemoryEngine(db_path=BASE_DIR / "ugos_memory.db")
        self.session = self.memory.get_or_create_session(SESSION_ID)
        self.agent = SoftwareEngineerAgent(name="WebBot")
        self.ollama = OllamaLLMProvider(model_id=MODEL_NAME)
        self.router = LLMRouter(
            primary_provider=self.ollama,
            fallback_providers=[MockLLMProvider()],
        )

    def status(self) -> dict:
        up = self.ollama.is_available()
        models = self.ollama.installed_models() if up else []
        ready = any(m.split(":")[0] == MODEL_NAME for m in models) if models else False
        return {"serverUp": up, "modelReady": ready, "model": MODEL_NAME, "installed": models}

    def ask(self, prompt: str) -> dict:
        import time

        verdict = self.agent.evaluate_and_act(
            action=SecurityAction.NETWORK_CALL,
            target=f"ollama://{MODEL_NAME}",
        )
        if verdict.get("status") != "SUCCESS":
            self.session.log_event(self.agent.agent_id, "llm_request_blocked", {"prompt": prompt})
            return {
                "blocked": True, "real": False, "saved": False,
                "answer": verdict.get("reason", "Denied by security policy."),
                "provider": None, "seconds": 0,
            }

        started = time.time()
        result = self.router.generate(prompt)
        elapsed = round(time.time() - started, 1)

        real = is_real_answer(result)
        answer = result.get("content", "")

        if real:
            self.memory.set_global_fact(
                key=f"answer::{prompt[:60]}",
                value=answer,
                tags=[result.get("provider", "unknown"), result.get("model", MODEL_NAME)],
            )
            self.session.log_event(
                self.agent.agent_id, "llm_request",
                {"prompt": prompt, "provider": result.get("provider")},
            )

        return {
            "blocked": False, "real": real, "saved": real,
            "answer": answer, "provider": result.get("provider"), "seconds": elapsed,
        }


class Handler(BaseHTTPRequestHandler):
    ugos: UGOS = None  # set in main()

    def log_message(self, fmt, *args):
        pass  # keep the console clean

    def _send(self, code, body, content_type):
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif self.path == "/status":
            self._send(200, json.dumps(self.ugos.status()), "application/json")
        else:
            self._send(404, "Not found", "text/plain")

    def do_POST(self):
        if self.path != "/ask":
            self._send(404, "Not found", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            prompt = (data.get("prompt") or "").strip()
            if not prompt:
                self._send(400, json.dumps({"error": "empty prompt"}), "application/json")
                return
            self._send(200, json.dumps(self.ugos.ask(prompt)), "application/json")
        except Exception as exc:  # never kill the server on one bad request
            self._send(500, json.dumps({"error": str(exc)}), "application/json")


def main() -> int:
    print("\n" + "=" * 62)
    print(" UGOS -- Local Web Interface")
    print("=" * 62)

    Handler.ugos = UGOS()
    status = Handler.ugos.status()

    if not status["serverUp"]:
        print("\n  [!] Ollama is not running. The page will open, but nothing")
        print("      can be answered until you start it from the Start menu.")
    elif not status["modelReady"]:
        print(f"\n  [!] Model '{MODEL_NAME}' is not downloaded. Run: ollama pull {MODEL_NAME}")

    url = f"http://{HOST}:{PORT}"
    print(f"\n  Open: {url}")
    print("  Close this window to stop UGOS.\n")

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.\n")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as exc:
        print(f"\n  Could not start on port {PORT}: {exc}")
        print("  Another program may be using it, or UGOS may already be running.\n")
        sys.exit(1)
