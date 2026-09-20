# ============================================
# arya/config.py
# ARYA — Agentic Reasoning & Intelligence Assistant
# All configuration in one place
# ============================================

import os
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()

# ── ARYA IDENTITY ─────────────────────────────
ARYA_NAME        = "DRXGON"
ARYA_VERSION     = "1.0"
ARYA_DESCRIPTION = "Your personal AI assistant — always ready, always learning"

ARYA_PERSONALITY = """You are DRXGON, a professional AI assistant.

Core traits:
- Precise: give specific, well-reasoned answers — never vague filler
- Proactive: anticipate the user's next need and offer it briefly
- Honest: state uncertainty plainly instead of guessing
- Efficient: respect the user's time; concise by default, detailed on request
- Personal: address the user by name and use relevant history when it helps

Communication style:
- Formal, composed, business-appropriate tone by default
- Clear structure — markdown headers, bullet points, bold key terms
- No filler openers ("Certainly!", "Great question!") and no excessive exclamation
- Close with one relevant, concise follow-up offer where useful
"""

CORE_REASONING_PRINCIPLES = """
CRITICAL REASONING RULES — follow these before answering anything:

1. NEVER invent or describe an image, screenshot, file, or error that was not
   actually provided in this exact conversation. If the user references an
   image/error/file and none is present in the CURRENT INPUT or RECENT
   CONVERSATION below, say so plainly: "I don't see an image or error in our
   conversation — could you share it or describe it?" Do NOT fabricate a
   plausible-sounding analysis to fill the gap.

2. Before answering, silently verify your response against every literal
   requirement in the request (directions, exact wording, constraints).
   If ambiguous, state your interpretation in one line, then proceed —
   don't ask unless truly necessary.

3. If you are uncertain about something, say so directly rather than
   presenting a guess as fact.

4. Ground every claim in what was actually said or shared — never assume
   information exists that wasn't given to you.
"""

# ── MODELS ────────────────────────────────────
# Fast model: routing decisions, memory extraction, quick classification
# Strong model: specialist agents that produce user-facing content
# llama-3.1-8b-instant / llama-3.3-70b-versatile were shut down on Groq (Aug 16, 2026).
# Override without editing code: set LLM_MODEL_FAST / LLM_MODEL_STRONG in .env
LLM_MODEL_FAST   = os.getenv("LLM_MODEL_FAST",   "openai/gpt-oss-20b")
LLM_MODEL_STRONG = os.getenv("LLM_MODEL_STRONG", "openai/gpt-oss-120b")
VISION_MODEL     = "qwen/qwen3.6-27b"
WHISPER_MODEL    = "whisper-large-v3-turbo"
EMBEDDING_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"

# ── API KEYS — secrets-first pattern, same as previous projects ──
try:
    import streamlit as st
    GROQ_API_KEY      = st.secrets.get("GROQ_API_KEY",      os.getenv("GROQ_API_KEY", ""))
    TAVILY_API_KEY    = st.secrets.get("TAVILY_API_KEY",    os.getenv("TAVILY_API_KEY", ""))
    LANGCHAIN_API_KEY = st.secrets.get("LANGCHAIN_API_KEY", os.getenv("LANGCHAIN_API_KEY", ""))
except Exception:
    GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
    TAVILY_API_KEY    = os.getenv("TAVILY_API_KEY", "")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")

# ── PATHS ─────────────────────────────────────
# NOTE: these are relative to wherever app.py actually runs FROM.
# Since app.py lives inside the arya/ folder itself, paths stay "./memory"
# NOT "./arya/memory" — that would create a nested arya/arya/ folder.
MEMORY_DIR       = "./memory"
VECTOR_STORE_DIR = f"{MEMORY_DIR}/vector_store"
PROFILE_PATH     = f"{MEMORY_DIR}/user_profile.json"
SESSION_DIR      = f"{MEMORY_DIR}/sessions"

for _dir in [MEMORY_DIR, VECTOR_STORE_DIR, SESSION_DIR]:
    os.makedirs(_dir, exist_ok=True)

# ── LANGSMITH — only enable tracing if a real key exists ──
if LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]    = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"]    = "arya-personal-assistant"
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

# ── AGENT SETTINGS ────────────────────────────
MAX_ITERATIONS       = 6
MEMORY_TOP_K         = 5     # how many long-term memories to retrieve
CONVERSATION_WINDOW  = 10    # last N messages to keep in short-term

# ── SPECIALIST AGENTS ─────────────────────────
AGENTS = {
    "researcher": {
        "name":        "Research Specialist",
        "description": "Web search and information synthesis",
        "triggers":    ["research", "find", "search", "what is", "tell me about",
                        "latest", "current", "information on"]
    },
    "writer": {
        "name":        "Writing Specialist",
        "description": "Emails, posts, articles, and content",
        "triggers":    ["write", "draft", "compose", "create", "email",
                        "post", "article", "letter", "message"]
    },
    "planner": {
        "name":        "Planning Specialist",
        "description": "Tasks, goals, schedules, and organization",
        "triggers":    ["plan", "schedule", "task", "goal", "organize",
                        "remind", "deadline", "steps", "how to achieve"]
    },
    "analyst": {
        "name":        "Analysis Specialist",
        "description": "Calculations, data analysis, and numbers",
        "triggers":    ["calculate", "analyze", "compare", "percentage",
                        "how much", "statistics", "data", "numbers", "cost"]
    },
    "news": {
        "name":        "News Specialist",
        "description": "Current events and news summaries",
        "triggers":    ["news", "today", "latest", "happening", "current events",
                        "update", "recent", "breaking"]
    },
    "coder": {
        "name":        "Code Specialist",
        "description": "Code explanation, debugging, and generation",
        "triggers":    ["code", "python", "debug", "error", "function",
                        "script", "program", "fix this", "explain this code"]
    },
}

print(f"DRXGON {ARYA_VERSION} config loaded.")
print(f"Fast model: {LLM_MODEL_FAST} | Strong model: {LLM_MODEL_STRONG} | Agents: {len(AGENTS)}")


PERSONALITY_STYLES = {
    "Professional": "Be formal, precise, and business-focused. Use structured responses. No casual language or humor.",
    "Friendly":     "Be warm, conversational, and approachable. Occasional light humor is welcome.",
    "Mentor":       "Teach and explain as you answer. Add a 'Why this matters' note. Be patient and encouraging.",
    "Direct":       "Minimal words. Get to the point immediately. No preamble.",
    "Creative":     "Think outside the box. Use vivid analogies and make connections between domains.",
    "Analytical":   "Be data-driven and rigorous. Show reasoning, quantify where possible, and state assumptions.",
    "Supportive":   "Be encouraging and empathetic while staying accurate and practical.",
    "Custom":       "Follow the USER-SPECIFIED BEHAVIOR NOTE below as the primary style guide; otherwise stay clear and professional."
}


def get_active_personality() -> str:
    """Reads the saved personality preference from the profile file directly
    (can't import from memory.py here — that would create a circular import,
    since memory.py imports from config.py)."""
    try:
        import json
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, 'r') as f:
                profile = json.load(f)
            style = profile.get("preferences", {}).get("personality", "Professional")
            return PERSONALITY_STYLES.get(style, PERSONALITY_STYLES["Professional"])
    except Exception:
        pass
    return PERSONALITY_STYLES["Professional"]


def get_custom_personality_note() -> str:
    """Reads the user's free-text personality instructions, if any."""
    try:
        import json
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, 'r') as f:
                profile = json.load(f)
            note = profile.get("preferences", {}).get("custom_personality", "").strip()
            return f"\nUSER-SPECIFIED BEHAVIOR NOTE:\n{note}" if note else ""
    except Exception:
        pass
    return ""


def get_full_personality() -> str:
    """Base DRXGON personality + the user's chosen style overlay + any
    free-text personality note the user saved in the sidebar/Settings."""
    return (f"{ARYA_PERSONALITY}\n\n{CORE_REASONING_PRINCIPLES}\n\n"
            f"CURRENT STYLE OVERLAY:\n{get_active_personality()}"
            f"{get_custom_personality_note()}")