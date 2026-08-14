"""
UGOS Configuration -- CHOOSE YOUR BRAIN HERE
============================================

This is the only file you need to edit to change which AI UGOS uses.
No API keys live in this file -- see "WHERE KEYS GO" at the bottom.

QUICK START
-----------
Offline, private, free  ->  PRIMARY = "ollama"      (needs Ollama running)
Best answers, no download ->  PRIMARY = "gemini"    (needs a free Google key)
Fastest answers          ->  PRIMARY = "groq"       (needs a free Groq key)
Many models, one key     ->  PRIMARY = "openrouter" (needs an OpenRouter key)
Friendlier local app     ->  PRIMARY = "lmstudio"   (needs LM Studio running)

The recommended setup is a cloud brain with a local fallback:
    PRIMARY  = "gemini"
    FALLBACK = "ollama"
Internet up, you get the good answers. Internet down, UGOS keeps working.
"""

# ---------------------------------------------------------------------------
# 1. WHICH BRAIN
# ---------------------------------------------------------------------------

PRIMARY = "gemini"

# Tried only if PRIMARY fails. Set to None for no fallback.
FALLBACK = "ollama"

# If every real provider fails, answer with the built-in fake provider?
# Replies are clearly labelled as placeholders and are never saved to memory.
# False = UGOS reports the failure honestly instead. Recommended: False.
ALLOW_MOCK_FALLBACK = True


# ---------------------------------------------------------------------------
# 2. WHICH MODEL FOR EACH BRAIN
# ---------------------------------------------------------------------------

MODELS = {
    "ollama":     "phi3",                       # ollama pull phi3
    "gemini":     "gemini-3.5-flash",           # or gemini-3.5-flash-lite (faster)
    "groq":       "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.3-70b-instruct",
    "openai":     "gpt-4o-mini",
    "lmstudio":   "local-model",                # LM Studio ignores this
    "jan":        "local-model",
    "together":   "meta-llama/Llama-3.3-70B-Instruct-Turbo",
}


# ---------------------------------------------------------------------------
# 3. WHERE EACH BRAIN LIVES
#
# Everything except Ollama and Gemini speaks the same "OpenAI-compatible"
# language, so they all share one provider class. To add a service that is
# not listed, add its address here -- no new code needed.
# ---------------------------------------------------------------------------

ENDPOINTS = {
    "groq":       "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "openai":     "https://api.openai.com/v1",
    "together":   "https://api.together.xyz/v1",
    "lmstudio":   "http://localhost:1234/v1",   # LM Studio: Developer tab -> Start Server
    "jan":        "http://localhost:1337/v1",   # Jan: Settings -> Local API Server
}

OLLAMA_HOST = "http://localhost:11434"

# How long to wait for a LOCAL model before giving up, and how many tokens to
# let it produce. Local models on CPU are slow: phi3 driving the agent loop
# regularly needs more than two minutes. Cloud brains ignore these.
LOCAL_TIMEOUT_SECONDS = 300
LOCAL_MAX_TOKENS = 800

# Local services need no key. Cloud ones do.
NEEDS_KEY = {"gemini", "groq", "openrouter", "openai", "together"}


# ---------------------------------------------------------------------------
# 4. WHERE KEYS GO  --  READ THIS
#
# NEVER put an API key in this file. This file is committed to GitHub, and a
# key pushed to a public repository is a leaked key: scanners find them within
# minutes, and you get the bill.
#
# Instead, create a file called ".env" next to this one:
#
#     GEMINI_API_KEY=your-key-here
#     GROQ_API_KEY=your-key-here
#
# .env is listed in .gitignore, so it stays on your machine only.
# Copy .env.example to .env to get started.
#
# Get a free Gemini key: https://aistudio.google.com/apikey
# Get a free Groq key:   https://console.groq.com/keys
# ---------------------------------------------------------------------------

KEY_NAMES = {
    "gemini":     "GEMINI_API_KEY",
    "groq":       "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "openai":     "OPENAI_API_KEY",
    "together":   "TOGETHER_API_KEY",
}
