# arya/agents/writer.py
import warnings
warnings.filterwarnings("ignore")

from config import get_full_personality
from utils import llm_strong, safe_invoke

WRITING_FORMATS = {
    "email":    {"structure": "Subject line, greeting, body paragraphs, professional sign-off",
                 "style": "clear and professional"},
    "linkedin": {"structure": "Hook, 3-4 short paragraphs, question, 3 hashtags",
                 "style": "professional but personal"},
    "report":   {"structure": "Executive summary, findings, recommendations",
                 "style": "formal and structured"},
    "message":  {"structure": "Direct, conversational, action-oriented",
                 "style": "casual and warm"},
    "article":  {"structure": "Headline, intro, 3-4 sections, conclusion",
                 "style": "engaging and informative"},
    "default":  {"structure": "Clear beginning, middle, end",
                 "style": "professional and clear"}
}


def detect_format(message: str) -> str:
    msg = message.lower()
    if "email" in msg:                    return "email"
    if "linkedin" in msg:                 return "linkedin"
    if "report" in msg:                   return "report"
    if "message" in msg or "text" in msg:  return "message"
    if "article" in msg or "blog" in msg:  return "article"
    return "default"


def writer_node(state: dict) -> dict:
    """Writing Specialist — emails, posts, articles, content."""
    message        = state["user_message"]
    memory_context = state.get("memory_context", "")
    profile        = state.get("user_profile", {})
    user_name      = profile.get("name", "")
    formality      = profile.get("preferences", {}).get("formality", "professional")

    print(f"\n[Writer] Processing: {message[:60]}")

    fmt_key = detect_format(message)
    fmt     = WRITING_FORMATS[fmt_key]
    print(f"  Format detected: {fmt_key}")

    prompt = f"""{get_full_personality()}

{f"Writing for: {user_name}" if user_name else ""}
User's preferred formality: {formality}

MEMORY CONTEXT:
{memory_context[:400]}

WRITING REQUEST: {message}

FORMAT: {fmt_key}
STRUCTURE: {fmt['structure']}
STYLE: {fmt['style']}

INSTRUCTIONS:
- Write exactly what was requested — complete, ready-to-use content
- Do NOT add instructions or commentary — just the written piece
- Match the format structure precisely
- Personalize based on any context from memory
- After the written piece, add one line: "Want me to adjust the tone, length, or format?"
"""

    response = safe_invoke(llm_strong, prompt)
    print(f"  Writing complete: {len(response)} chars")

    return {"agent_responses": [response]}