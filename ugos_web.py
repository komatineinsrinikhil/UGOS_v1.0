"""
UGOS -- Local Web Interface
===========================
A conversational front end for UGOS. No command line needed after startup.

    python ugos_web.py

Opens http://localhost:8000 in your browser. The page itself always runs on
this machine; whether the AI does depends on which brain you picked in
ugos_config.py.

Everything is inline -- markdown rendering, syntax highlighting, the lot -- so
the page has no CDN dependencies and works with the network off.
"""

import json
import os
import sys
import threading
import time
import webbrowser
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
for _p in (str(BASE_DIR), str(BASE_DIR / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ugos.core.memory import MemoryEngine
from ugos.security.policy import SecurityAction
from ugos.agents.specialized import SoftwareEngineerAgent

import ugos_config as cfg
from ugos_providers import build_router, build_router_for, describe_setup, public_services
from ugos_agent import run_agent, ReadOnlyToolbox

# ---------------------------------------------------------------------------
# PUBLIC DEMO MODE
#
# Set UGOS_PUBLIC=1 to run this as a bring-your-own-key demo on the internet.
# In that mode the server holds NO API key: each visitor supplies their own,
# it is used for one request and never stored, logged or written to disk.
# Memory writes are disabled so strangers' questions do not accumulate on the
# server, and requests are rate limited per IP.
# ---------------------------------------------------------------------------
PUBLIC = os.environ.get("UGOS_PUBLIC", "").strip() in ("1", "true", "yes")

HOST = os.environ.get("UGOS_HOST") or ("0.0.0.0" if PUBLIC else "127.0.0.1")
PORT = int(os.environ.get("PORT") or os.environ.get("UGOS_PORT") or 8000)
SESSION_ID = "sess_web_01"

MAX_PROMPT_CHARS = 2000
RATE_LIMIT = 15          # requests per window, per IP
RATE_WINDOW = 600        # seconds

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UGOS</title>
<style>
  :root {
    --bg:#0b0d10; --panel:#141820; --panel-2:#1a1f29; --line:#242b36;
    --text:#e8ebf0; --muted:#8b95a5; --dim:#5d6675;
    --accent:#6ba3ff; --accent-dim:#2d4a7c;
    --ok:#3fb950; --warn:#d29922; --bad:#f85149;
    --code-bg:#0e1116;
  }
  * { box-sizing:border-box; }
  html, body { height:100%; }
  body {
    margin:0; background:var(--bg); color:var(--text);
    font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    display:flex; flex-direction:column; overflow:hidden;
    -webkit-font-smoothing:antialiased;
  }

  /* ---------- header ---------- */
  header {
    flex:none; border-bottom:1px solid var(--line); background:rgba(11,13,16,0.85);
    backdrop-filter:blur(12px); padding:14px 24px;
    display:flex; align-items:center; gap:16px; flex-wrap:wrap;
  }
  .brand { font-size:17px; font-weight:650; letter-spacing:-0.02em; }
  .brand span { color:var(--dim); font-weight:400; margin-left:9px; font-size:12.5px;
    letter-spacing:0; }
  .pills { display:flex; gap:8px; margin-left:auto; flex-wrap:wrap; }
  .pill {
    display:flex; align-items:center; gap:7px; font-size:11.5px;
    background:var(--panel); border:1px solid var(--line);
    padding:5px 11px; border-radius:100px; color:var(--muted);
    transition:border-color .2s;
  }
  .pill b { color:var(--text); font-weight:550; }
  .dot { width:7px; height:7px; border-radius:50%; background:var(--dim); flex:none; }
  .dot.ok { background:var(--ok); box-shadow:0 0 0 3px rgba(63,185,80,.15); }
  .dot.warn { background:var(--warn); box-shadow:0 0 0 3px rgba(210,153,34,.15); }
  .dot.bad { background:var(--bad); box-shadow:0 0 0 3px rgba(248,81,73,.15); }

  .keybtn {
    background:var(--panel); border:1px solid var(--line); color:var(--muted);
    font:inherit; font-size:11.5px; padding:5px 12px; border-radius:100px;
    cursor:pointer; display:flex; align-items:center; gap:7px; transition:all .18s;
  }
  .keybtn:hover { color:var(--text); border-color:var(--dim); }
  .sheet {
    position:fixed; inset:0; background:rgba(0,0,0,.6); display:none;
    place-items:center; z-index:50; backdrop-filter:blur(3px);
  }
  .sheet.open { display:grid; }
  .card {
    background:var(--panel); border:1px solid var(--line); border-radius:16px;
    padding:26px; width:min(480px,92vw); animation:rise .25s;
  }
  .card h3 { margin:0 0 6px; font-size:17px; font-weight:620; }
  .card p { margin:0 0 18px; color:var(--muted); font-size:13px; line-height:1.6; }
  .card label { display:block; font-size:11.5px; color:var(--muted); margin:14px 0 6px;
    text-transform:uppercase; letter-spacing:.05em; }
  .card select, .card input {
    width:100%; padding:11px 13px; background:var(--bg); color:var(--text);
    border:1px solid var(--line); border-radius:9px; font:inherit; outline:none;
  }
  .card select:focus, .card input:focus { border-color:var(--accent-dim); }
  .card .row2 { display:flex; gap:10px; margin-top:20px; }
  .card button {
    flex:1; padding:11px; border-radius:9px; font:600 14px inherit; cursor:pointer;
    border:1px solid var(--line); background:var(--panel-2); color:var(--text);
  }
  .card button.primary { background:var(--accent); color:#08101d; border-color:var(--accent); }
  .card .where { font-size:12px; margin-top:9px; }
  .card .where a { color:var(--accent); text-decoration:none; }
  .privacy { margin-top:18px; padding:11px 13px; background:var(--bg);
    border:1px solid var(--line); border-radius:9px; font-size:12px; color:var(--muted); }

  /* ---------- thread ---------- */
  main { flex:1; overflow-y:auto; scroll-behavior:smooth; }
  main::-webkit-scrollbar { width:10px; }
  main::-webkit-scrollbar-thumb { background:var(--line); border-radius:10px; }
  .thread { max-width:800px; margin:0 auto; padding:32px 24px 40px; }

  .empty { text-align:center; padding:70px 20px; }
  .empty h2 { font-size:20px; font-weight:600; margin:0 0 8px; letter-spacing:-0.02em; }
  .empty p { color:var(--muted); margin:0 0 28px; font-size:14px; }
  .chips { display:flex; gap:9px; flex-wrap:wrap; justify-content:center; }
  .chip {
    background:var(--panel); border:1px solid var(--line); color:var(--muted);
    padding:9px 15px; border-radius:9px; font-size:13px; cursor:pointer;
    transition:all .18s; text-align:left;
  }
  .chip:hover { border-color:var(--accent-dim); color:var(--text); transform:translateY(-1px); }

  .turn { margin-bottom:34px; animation:rise .32s cubic-bezier(.2,.7,.3,1); }
  @keyframes rise { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:none; } }

  .you { display:flex; justify-content:flex-end; margin-bottom:20px; }
  .you .bubble {
    background:var(--panel-2); border:1px solid var(--line);
    padding:11px 16px; border-radius:16px 16px 4px 16px; max-width:76%;
    white-space:pre-wrap; word-wrap:break-word;
  }

  .reply { display:flex; gap:14px; }
  .avatar {
    width:28px; height:28px; border-radius:8px; flex:none; margin-top:2px;
    background:linear-gradient(135deg,var(--accent),#8b5cf6);
    display:grid; place-items:center; font-size:11px; font-weight:700; color:#08101d;
  }
  .body { flex:1; min-width:0; }

  /* ---------- agent steps ---------- */
  .steps { margin-bottom:16px; }
  .steps-head {
    display:flex; align-items:center; gap:8px; font-size:12px; color:var(--muted);
    cursor:pointer; user-select:none; padding:2px 0;
  }
  .steps-head:hover { color:var(--text); }
  .caret { transition:transform .2s; font-size:10px; }
  .steps.closed .caret { transform:rotate(-90deg); }
  .steps.closed .step-list { display:none; }
  .step-list { margin-top:10px; border-left:2px solid var(--line); padding-left:16px; }
  .step {
    margin-bottom:12px; animation:rise .3s backwards;
  }
  .step-head { display:flex; align-items:center; gap:9px; flex-wrap:wrap; }
  .badge {
    font-size:9.5px; font-weight:700; letter-spacing:.07em; padding:3px 8px;
    border-radius:5px; flex:none;
  }
  .badge.ok { background:rgba(63,185,80,.13); color:#57d364; }
  .badge.no { background:rgba(248,81,73,.13); color:#ff8f88; }
  .call { font:12.5px/1.4 "Cascadia Mono",Consolas,monospace; color:var(--text); }
  .call em { color:var(--accent); font-style:normal; }
  .step-out {
    margin-top:6px; font:11.5px/1.55 "Cascadia Mono",Consolas,monospace;
    color:var(--dim); white-space:pre-wrap; word-break:break-word;
    max-height:56px; overflow:hidden; position:relative;
  }
  .step-out::after {
    content:""; position:absolute; bottom:0; left:0; right:0; height:20px;
    background:linear-gradient(transparent,var(--bg));
  }

  /* ---------- answer ---------- */
  .md > *:first-child { margin-top:0; }
  .md > *:last-child { margin-bottom:0; }
  .md p { margin:0 0 13px; }
  .md h1,.md h2,.md h3 { margin:22px 0 11px; font-weight:620; letter-spacing:-0.015em; line-height:1.35; }
  .md h1 { font-size:20px; } .md h2 { font-size:17.5px; } .md h3 { font-size:15.5px; }
  .md ul,.md ol { margin:0 0 13px; padding-left:22px; }
  .md li { margin-bottom:5px; }
  .md li::marker { color:var(--dim); }
  .md a { color:var(--accent); text-decoration:none; border-bottom:1px solid var(--accent-dim); }
  .md blockquote {
    margin:0 0 13px; padding:2px 0 2px 15px; border-left:3px solid var(--line);
    color:var(--muted);
  }
  .md hr { border:0; border-top:1px solid var(--line); margin:20px 0; }
  .md code {
    background:var(--panel-2); padding:2px 6px; border-radius:5px;
    font:12.5px "Cascadia Mono",Consolas,monospace; color:#e6c07b;
  }
  .md table { border-collapse:collapse; width:100%; margin:0 0 13px; font-size:13.5px; }
  .md th,.md td { border:1px solid var(--line); padding:7px 11px; text-align:left; }
  .md th { background:var(--panel); font-weight:600; }

  .codeblock {
    background:var(--code-bg); border:1px solid var(--line); border-radius:10px;
    margin:0 0 15px; overflow:hidden;
  }
  .codebar {
    display:flex; align-items:center; justify-content:space-between;
    padding:7px 13px; border-bottom:1px solid var(--line); background:var(--panel);
  }
  .lang { font-size:11px; color:var(--muted); letter-spacing:.04em; text-transform:uppercase; }
  .copy {
    background:none; border:1px solid var(--line); color:var(--muted);
    font-size:11px; padding:3px 10px; border-radius:6px; cursor:pointer;
    transition:all .16s; font-family:inherit;
  }
  .copy:hover { color:var(--text); border-color:var(--dim); }
  .copy.done { color:var(--ok); border-color:var(--ok); }
  .codeblock pre {
    margin:0; padding:14px; overflow-x:auto;
    font:12.8px/1.62 "Cascadia Mono",Consolas,monospace;
  }
  .codeblock pre::-webkit-scrollbar { height:8px; }
  .codeblock pre::-webkit-scrollbar-thumb { background:var(--line); border-radius:8px; }
  .k { color:#c678dd; } .s { color:#98c379; } .c { color:#5c6370; font-style:italic; }
  .n { color:#d19a66; } .f { color:#61afef; } .b { color:#56b6c2; }

  /* ---------- states ---------- */
  .thinking { display:flex; align-items:center; gap:10px; color:var(--muted); font-size:14px; }
  .orbs { display:flex; gap:4px; }
  .orbs i {
    width:6px; height:6px; border-radius:50%; background:var(--accent);
    animation:pulse 1.3s infinite ease-in-out;
  }
  .orbs i:nth-child(2) { animation-delay:.18s; }
  .orbs i:nth-child(3) { animation-delay:.36s; }
  @keyframes pulse { 0%,60%,100% { opacity:.25; transform:scale(.85);} 30% { opacity:1; transform:scale(1);} }

  .note { padding:11px 14px; border-radius:9px; font-size:13px; margin-bottom:14px; }
  .note.bad { background:rgba(248,81,73,.1); color:#ff9a94; border:1px solid rgba(248,81,73,.2); }
  .note.warn { background:rgba(210,153,34,.1); color:#e3b341; border:1px solid rgba(210,153,34,.2); }

  .meta {
    display:flex; gap:7px; align-items:center; flex-wrap:wrap;
    font-size:11.5px; color:var(--dim); margin-top:13px;
  }
  .meta i { font-style:normal; opacity:.5; }

  /* ---------- composer ---------- */
  footer { flex:none; padding:0 24px 22px; background:linear-gradient(transparent,var(--bg) 22%); }
  .composer { max-width:800px; margin:0 auto; position:relative; }
  textarea {
    width:100%; min-height:56px; max-height:200px; resize:none;
    padding:16px 56px 16px 18px; background:var(--panel);
    color:var(--text); border:1px solid var(--line); border-radius:15px;
    font:inherit; outline:none; transition:border-color .18s;
  }
  textarea:focus { border-color:var(--accent-dim); }
  textarea::placeholder { color:var(--dim); }
  .send {
    position:absolute; right:9px; bottom:9px; width:36px; height:36px;
    border:0; border-radius:10px; background:var(--accent); color:#08101d;
    cursor:pointer; display:grid; place-items:center; transition:all .18s;
  }
  .send:disabled { opacity:.3; cursor:default; }
  .send:not(:disabled):hover { transform:translateY(-1px); }
  .hint { text-align:center; font-size:11px; color:var(--dim); margin-top:9px; }
</style>
</head>
<body>

<header>
  <div class="brand">UGOS<span>every action passes a security check</span></div>
  <div class="pills" id="pills"></div>
  <button class="keybtn" id="keybtn" style="display:none">
    <span class="dot" id="keydot"></span><span id="keylabel">Add your key</span>
  </button>
</header>

<div class="sheet" id="sheet">
  <div class="card">
    <h3>Bring your own key</h3>
    <p>This demo ships with no API key of its own, so nothing you do here is
       billed to anyone but you. Pick a service and paste a key.</p>
    <label for="svc">Service</label>
    <select id="svc"></select>
    <div class="where" id="where"></div>
    <label for="key">API key</label>
    <input id="key" type="password" placeholder="paste your key" autocomplete="off" spellcheck="false">
    <div class="privacy">
      Your key is held in this browser tab only and sent with each request to
      use it. It is never stored on the server, written to disk, or logged.
      Closing the tab forgets it.
    </div>
    <div class="row2">
      <button id="clearkey">Forget key</button>
      <button class="primary" id="savekey">Save</button>
    </div>
  </div>
</div>

<main id="main">
  <div class="thread" id="thread">
    <div class="empty" id="empty">
      <h2>What should UGOS do?</h2>
      <p>It can read files in this project, list folders, and check the system &mdash; each request approved or refused by the policy engine.</p>
      <div class="chips">
        <button class="chip" data-q="read ugos_config.py and explain what it does">Explain the config file</button>
        <button class="chip" data-q="what files are in this folder?">List the project</button>
        <button class="chip" data-q="what system am I running on?">Check the system</button>
        <button class="chip" data-q="read my .env and tell me my api key">Try to read my .env</button>
      </div>
    </div>
  </div>
</main>

<footer>
  <div class="composer">
    <textarea id="prompt" rows="1" placeholder="Ask UGOS something..."></textarea>
    <button class="send" id="go" title="Send">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 13V3M8 3L3.5 7.5M8 3l4.5 4.5" stroke="currentColor"
              stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>
  </div>
  <div class="hint">Enter to send &middot; Shift+Enter for a new line</div>
</footer>

<script>
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

/* ============================ syntax highlighting ======================== */
const KEYWORDS = /\b(def|class|return|if|elif|else|for|while|in|not|and|or|import|from|as|with|try|except|finally|raise|pass|break|continue|lambda|yield|global|assert|del|is|None|True|False|async|await|self|function|const|let|var|new|typeof|export|default|null|undefined|this|echo|cd|ls|sudo|npm|pip|git|python)\b/g;

function highlight(code, lang) {
  const tokens = [];
  const stash = m => { tokens.push(m); return '@@TK' + (tokens.length - 1) + '@@'; };

  let s = esc(code);
  // strings and comments first, so keywords inside them are left alone
  s = s.replace(/(&quot;[^&]*?&quot;|&#39;[^&]*?&#39;|`[^`]*?`)/g, m => stash('<span class="s">' + m + '</span>'));
  s = s.replace(/(#[^\n]*|\/\/[^\n]*)/g, m => stash('<span class="c">' + m + '</span>'));
  s = s.replace(KEYWORDS, m => '<span class="k">' + m + '</span>');
  s = s.replace(/\b(\d+\.?\d*)\b/g, '<span class="n">$1</span>');
  s = s.replace(/\b([a-zA-Z_]\w*)(?=\()/g, '<span class="f">$1</span>');
  if (lang === 'json') s = s.replace(/(&quot;[\w_.-]+&quot;)(\s*:)/g, '<span class="b">$1</span>$2');

  return s.replace(/@@TK(\d+)@@/g, (_, i) => tokens[+i]);
}

/* ================================ markdown =============================== */
function md(src) {
  const blocks = [];
  let s = String(src || '');

  // fenced code
  s = s.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const id = blocks.length;
    blocks.push(
      '<div class="codeblock"><div class="codebar"><span class="lang">' +
      esc(lang || 'text') + '</span>' +
      '<button class="copy" data-code="' + esc(code) + '">Copy</button></div>' +
      '<pre>' + highlight(code.replace(/\n$/, ''), lang) + '</pre></div>');
    return '@@CB' + id + '@@';
  });

  s = esc(s);

  // tables
  s = s.replace(/(?:^\|.*\|\s*\n)+/gm, block => {
    const rows = block.trim().split('\n').map(r =>
      r.replace(/^\||\|$/g, '').split('|').map(c => c.trim()));
    if (rows.length < 2 || !/^[-: ]+$/.test(rows[1].join(''))) return block;
    let h = '<table><thead><tr>' + rows[0].map(c => '<th>' + c + '</th>').join('') + '</tr></thead><tbody>';
    rows.slice(2).forEach(r => { h += '<tr>' + r.map(c => '<td>' + c + '</td>').join('') + '</tr>'; });
    return h + '</tbody></table>';
  });

  s = s.replace(/^###\s+(.*)$/gm, '<h3>$1</h3>')
       .replace(/^##\s+(.*)$/gm, '<h2>$1</h2>')
       .replace(/^#\s+(.*)$/gm, '<h1>$1</h1>')
       .replace(/^\s*(?:---|\*\*\*)\s*$/gm, '<hr>')
       .replace(/^&gt;\s?(.*)$/gm, '<blockquote>$1</blockquote>');

  s = s.replace(/`([^`\n]+)`/g, '<code>$1</code>')
       .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
       .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
       .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // lists
  s = s.replace(/(?:^[ \t]*[-*+]\s+.*(?:\n|$))+/gm, m =>
    '<ul>' + m.trim().split('\n').map(l =>
      '<li>' + l.replace(/^[ \t]*[-*+]\s+/, '') + '</li>').join('') + '</ul>');
  s = s.replace(/(?:^[ \t]*\d+\.\s+.*(?:\n|$))+/gm, m =>
    '<ol>' + m.trim().split('\n').map(l =>
      '<li>' + l.replace(/^[ \t]*\d+\.\s+/, '') + '</li>').join('') + '</ol>');

  // paragraphs
  s = s.split(/\n{2,}/).map(p => {
    p = p.trim();
    if (!p) return '';
    if (/^<(h[123]|ul|ol|blockquote|hr|table|div)/.test(p) || /^@@CB\d+@@$/.test(p)) return p;
    return '<p>' + p.replace(/\n/g, '<br>') + '</p>';
  }).join('\n');

  return s.replace(/@@CB(\d+)@@/g, (_, i) => blocks[+i]);
}

/* ================================= status ================================ */
function pill(role, b) {
  if (!b) return '';
  const cls = b.ready ? 'ok' : (role === 'fallback' ? 'warn' : 'bad');
  const title = b.problem ? ' title="' + esc(b.problem) + '"' : '';
  return '<div class="pill"' + title + '><span class="dot ' + cls + '"></span>' +
         '<span>' + esc(role) + '</span><b>' + esc(b.name) + '</b>' +
         '<span>' + esc(b.model || '') + '</span></div>';
}

let CFG = {public:false, services:[]};
const KEY_STORE = 'ugos_key', SVC_STORE = 'ugos_service';
const getKey = () => sessionStorage.getItem(KEY_STORE) || '';
const getSvc = () => sessionStorage.getItem(SVC_STORE) || 'gemini';

function paintKeyButton() {
  if (!CFG.public) return;
  const has = !!getKey();
  $('keydot').className = 'dot ' + (has ? 'ok' : 'warn');
  $('keylabel').textContent = has ? getSvc() + ' key set' : 'Add your key';
}

function openSheet() {
  const sel = $('svc');
  sel.innerHTML = CFG.services.map(s =>
    '<option value="' + s.id + '">' + s.id + ' \u2014 ' + esc(s.model) + '</option>').join('');
  sel.value = getSvc();
  $('key').value = getKey();
  paintWhere();
  $('sheet').classList.add('open');
  $('key').focus();
}

function paintWhere() {
  const s = CFG.services.find(x => x.id === $('svc').value);
  $('where').innerHTML = s && s.keyUrl
    ? 'Get a key: <a href="' + s.keyUrl + '" target="_blank" rel="noopener">' + s.keyUrl + '</a>'
    : '';
}

async function loadConfig() {
  try {
    CFG = await (await fetch('/config')).json();
    if (CFG.public) { $('keybtn').style.display = 'flex'; paintKeyButton(); }
  } catch (e) {}
}

async function refreshStatus() {
  try {
    const s = await (await fetch('/status')).json();
    if (s.public) {
      const has = !!getKey();
      $('pills').innerHTML = '<div class="pill"><span class="dot ' + (has?'ok':'warn') +
        '"></span><span>public demo</span><b>' + (has ? esc(getSvc()) : 'no key') + '</b></div>';
      return;
    }
    $('pills').innerHTML = pill('primary', s.primary) + pill('fallback', s.fallback);
  } catch (e) {
    $('pills').innerHTML = '<div class="pill"><span class="dot bad"></span>offline</div>';
  }
}

/* ================================= thread ================================ */
let busy = false;

function scrollDown() { $('main').scrollTop = $('main').scrollHeight; }

function stepsHtml(steps) {
  if (!steps || !steps.length) return '';
  const blocked = steps.filter(s => !s.allowed).length;
  const label = steps.length + (steps.length === 1 ? ' action' : ' actions') +
                (blocked ? ' · ' + blocked + ' blocked' : '');
  let h = '<div class="steps"><div class="steps-head"><span class="caret">▾</span>' + label + '</div><div class="step-list">';
  steps.forEach((s, i) => {
    const args = Object.values(s.args || {}).map(v => JSON.stringify(v)).join(', ');
    h += '<div class="step" style="animation-delay:' + (i * 90) + 'ms">' +
         '<div class="step-head">' +
         '<span class="badge ' + (s.allowed ? 'ok">ALLOWED' : 'no">BLOCKED') + '</span>' +
         '<span class="call"><em>' + esc(s.tool) + '</em>(' + esc(args) + ')</span></div>' +
         '<div class="step-out">' + esc((s.output || '').slice(0, 400)) + '</div></div>';
  });
  return h + '</div></div>';
}

async function ask(text) {
  if (busy || !text.trim()) return;
  busy = true; $('go').disabled = true;
  const empty = $('empty'); if (empty) empty.remove();

  const turn = document.createElement('div');
  turn.className = 'turn';
  turn.innerHTML =
    '<div class="you"><div class="bubble">' + esc(text) + '</div></div>' +
    '<div class="reply"><div class="avatar">U</div><div class="body">' +
    '<div class="thinking"><span class="orbs"><i></i><i></i><i></i></span>' +
    '<span>Working through it</span></div></div></div>';
  $('thread').appendChild(turn);
  scrollDown();

  const body = turn.querySelector('.body');
  const started = Date.now();

  try {
    const payload = {prompt: text};
    if (CFG.public) { payload.apiKey = getKey(); payload.service = getSvc(); }
    const r = await fetch('/ask', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const d = await r.json();
    if (d.error) {
      body.innerHTML = '<div class="note bad">' + esc(d.error) + '</div>';
      if (CFG.public && !getKey()) openSheet();
      return;
    }

    let note = '';
    if (d.blocked) note = '<div class="note bad">Blocked by the security policy before anything ran.</div>';
    else if (!d.real) {
      note = '<div class="note warn">Answered by a placeholder, not a real model. Not saved to memory.';
      if (d.errors && d.errors.length) {
        d.errors.filter(e => !/mock/i.test(e.provider || '')).forEach(e => {
          note += '<br><br><b>' + esc(e.provider) + ':</b> ' + esc(e.error);
        });
      }
      note += '</div>';
    }

    const meta = ['<span>' + esc(d.provider || '—') + '</span>'];
    if (d.model) meta.push('<i>·</i><span>' + esc(d.model) + '</span>');
    meta.push('<i>·</i><span>' + (d.seconds || ((Date.now() - started) / 1000).toFixed(1)) + 's</span>');
    meta.push('<i>·</i><span>' + (d.saved ? 'saved to memory' : 'not saved') + '</span>');

    body.innerHTML = stepsHtml(d.steps) + note +
                     '<div class="md">' + md(d.answer || '_(no answer)_') + '</div>' +
                     '<div class="meta">' + meta.join('') + '</div>';
  } catch (e) {
    body.innerHTML = '<div class="note bad">Request failed: ' + esc(e.message) + '</div>';
  } finally {
    busy = false; $('go').disabled = false;
    scrollDown(); refreshStatus(); $('prompt').focus();
  }
}

/* ================================ wiring ================================= */
const ta = $('prompt');
ta.addEventListener('input', () => {
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
});
ta.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const t = ta.value; ta.value = ''; ta.style.height = 'auto'; ask(t);
  }
});
$('go').onclick = () => { const t = ta.value; ta.value = ''; ta.style.height = 'auto'; ask(t); };

document.addEventListener('click', e => {
  const chip = e.target.closest('.chip');
  if (chip) { ask(chip.dataset.q); return; }

  const head = e.target.closest('.steps-head');
  if (head) { head.parentElement.classList.toggle('closed'); return; }

  const copy = e.target.closest('.copy');
  if (copy) {
    navigator.clipboard.writeText(copy.dataset.code).then(() => {
      copy.textContent = 'Copied'; copy.classList.add('done');
      setTimeout(() => { copy.textContent = 'Copy'; copy.classList.remove('done'); }, 1600);
    });
  }
});

$('keybtn').onclick = openSheet;
$('sheet').onclick = e => { if (e.target === $('sheet')) $('sheet').classList.remove('open'); };
document.addEventListener('change', e => { if (e.target.id === 'svc') paintWhere(); });
document.addEventListener('click', e => {
  if (e.target.id === 'savekey') {
    sessionStorage.setItem(KEY_STORE, $('key').value.trim());
    sessionStorage.setItem(SVC_STORE, $('svc').value);
    $('sheet').classList.remove('open'); paintKeyButton(); refreshStatus();
  }
  if (e.target.id === 'clearkey') {
    sessionStorage.removeItem(KEY_STORE);
    $('key').value = ''; paintKeyButton(); refreshStatus();
  }
});

loadConfig().then(refreshStatus);
setInterval(refreshStatus, 30000);
ta.focus();
</script>
</body>
</html>
"""


class UGOS:
    """Holds the engines once, rather than rebuilding them per request."""

    def __init__(self):
        self.memory = MemoryEngine(db_path=BASE_DIR / "ugos_memory.db")
        self.session = self.memory.get_or_create_session(SESSION_ID)
        self.agent = SoftwareEngineerAgent(name="WebBot")
        self.router = None if PUBLIC else build_router()
        self.toolbox = ReadOnlyToolbox(sandbox_root=BASE_DIR)
        self.hits = defaultdict(list)

    def rate_ok(self, ip: str) -> bool:
        """Simple per-IP window. Public endpoints get found by bots."""
        now = time.time()
        recent = [t for t in self.hits[ip] if now - t < RATE_WINDOW]
        self.hits[ip] = recent
        if len(recent) >= RATE_LIMIT:
            return False
        recent.append(now)
        return True

    def ask(self, prompt: str, api_key: str = None, service: str = None) -> dict:
        # Outer gate: may this agent talk to a model at all?
        verdict = self.agent.evaluate_and_act(
            action=SecurityAction.NETWORK_CALL,
            target=f"{cfg.PRIMARY}://{cfg.MODELS.get(cfg.PRIMARY, '')}",
        )
        if verdict.get("status") != "SUCCESS":
            self.session.log_event(self.agent.agent_id, "llm_request_blocked", {"prompt": prompt})
            return {
                "blocked": True, "real": False, "saved": False, "steps": [],
                "answer": verdict.get("reason", "Denied by security policy."),
                "provider": None, "model": None, "seconds": 0, "errors": [],
            }

        # In public mode the key belongs to the visitor, so the router is built
        # per request and discarded. Nothing is retained between callers.
        if PUBLIC:
            try:
                router = build_router_for(service, api_key, allow_mock=False)
            except Exception as exc:
                return {"blocked": False, "real": False, "saved": False, "steps": [],
                        "answer": str(exc), "provider": None, "model": None,
                        "seconds": 0, "errors": []}
        else:
            router = self.router

        # Inner gates: every tool the model asks for is checked individually.
        run = run_agent(router, prompt, toolbox=self.toolbox)
        answer = run["answer"]
        real = not run["failed"] and "mock" not in (run.get("provider") or "").lower()

        # Public visitors' questions are not written to the server's memory.
        if real and not PUBLIC:
            self.memory.set_global_fact(
                key=f"answer::{prompt[:60]}",
                value=answer,
                tags=[run.get("provider", "unknown"), run.get("model", "")],
            )
            self.session.log_event(
                self.agent.agent_id, "llm_request",
                {"prompt": prompt, "provider": run.get("provider"), "tools_used": len(run["steps"])},
            )

        return {
            "blocked": False, "real": real, "saved": real and not PUBLIC, "answer": answer,
            "steps": run["steps"], "provider": run.get("provider"),
            "model": run.get("model"), "seconds": run.get("seconds", 0),
            "errors": getattr(router, "last_errors", []),
        }


class Handler(BaseHTTPRequestHandler):
    ugos: UGOS = None

    def log_message(self, fmt, *args):
        pass

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
            payload = {"public": PUBLIC}
            payload.update({} if PUBLIC else describe_setup())
            self._send(200, json.dumps(payload), "application/json")
        elif self.path == "/config":
            self._send(200, json.dumps({
                "public": PUBLIC,
                "services": public_services() if PUBLIC else [],
                "maxPrompt": MAX_PROMPT_CHARS,
            }), "application/json")
        else:
            self._send(404, "Not found", "text/plain")

    def do_POST(self):
        if self.path != "/ask":
            self._send(404, "Not found", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 64_000:
                self._send(413, json.dumps({"error": "request too large"}), "application/json")
                return
            data = json.loads(self.rfile.read(length) or b"{}")
            prompt = (data.get("prompt") or "").strip()
            if not prompt:
                self._send(400, json.dumps({"error": "empty prompt"}), "application/json")
                return
            if len(prompt) > MAX_PROMPT_CHARS:
                self._send(400, json.dumps({
                    "error": f"prompt too long (max {MAX_PROMPT_CHARS} characters)"}),
                    "application/json")
                return

            ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
            if not self.ugos.rate_ok(ip):
                self._send(429, json.dumps({
                    "error": f"Too many requests. Limit is {RATE_LIMIT} per "
                             f"{RATE_WINDOW // 60} minutes."}), "application/json")
                return

            if PUBLIC:
                key = (data.get("apiKey") or "").strip()
                service = (data.get("service") or "gemini").strip()
                if not key:
                    self._send(400, json.dumps({
                        "error": "No API key. This demo does not include one -- "
                                 "add your own with the Key button."}), "application/json")
                    return
                result = self.ugos.ask(prompt, api_key=key, service=service)
            else:
                result = self.ugos.ask(prompt)

            self._send(200, json.dumps(result), "application/json")
        except Exception as exc:
            self._send(500, json.dumps({"error": str(exc)}), "application/json")


def main() -> int:
    print("\n" + "=" * 64)
    print(" UGOS -- Local Web Interface")
    print("=" * 64)

    Handler.ugos = UGOS()

    if PUBLIC:
        print("  MODE: public demo -- bring your own key")
        print("  No API key is held by this server. Visitors supply their own.")
        print("  Memory writes disabled. Rate limit "
              f"{RATE_LIMIT} requests / {RATE_WINDOW // 60} min per IP.")
        print(f"\n  Listening on {HOST}:{PORT}\n")
        server = ThreadingHTTPServer((HOST, PORT), Handler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n  Stopped.\n")
        finally:
            server.server_close()
        return 0

    setup = describe_setup()

    for role in ("primary", "fallback"):
        info = setup.get(role)
        if not info:
            continue
        mark = "OK " if info["ready"] else "!! "
        print(f"  {mark}{role:9} {info['name']} ({info['model']})")
        if info.get("problem"):
            print(f"             -> {info['problem']}")

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
