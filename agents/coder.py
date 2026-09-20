# arya/agents/coder.py
import warnings
warnings.filterwarnings("ignore")

from config import get_full_personality
from utils import llm_strong, safe_invoke


def detect_coding_task(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["debug", "error", "fix", "broken", "not working"]):
        return "debug"
    if any(w in msg for w in ["explain", "what does", "how does", "understand"]):
        return "explain"
    if any(w in msg for w in ["write", "create", "build", "make", "generate"]):
        return "generate"
    if any(w in msg for w in ["improve", "optimize", "refactor", "better"]):
        return "improve"
    return "general"


def coder_node(state: dict) -> dict:
    """Code Specialist — explain, debug, write, and improve code."""
    message        = state["user_message"]
    memory_context = state.get("memory_context", "")
    profile        = state.get("user_profile", {})
    user_name      = profile.get("name", "")

    print(f"\n[Coder] Processing: {message[:60]}")

    task_type = detect_coding_task(message)
    print(f"  Task type: {task_type}")

    task_instructions = {
        "debug": """Identify the bug, explain WHY it happens, provide the fixed code,
and explain what the fix does. Show before and after.""",
        "explain": """Explain the code line by line if short, or section by section if long.
Use simple analogies. End with 'The key concept here is...'""",
        "generate": """Write clean, well-commented code.
Include: imports, the main function/class, a usage example.
Follow Python best practices. Add docstrings.""",
        "improve": """Show the original, list specific problems,
then show the improved version with comments explaining each change.""",
        "general": """Help with the coding question clearly and specifically.
Always include runnable code examples."""
    }

    prompt = f"""{get_full_personality()}

{f"Helping: {user_name}" if user_name else ""}

MEMORY CONTEXT:
{memory_context[:300]}

CODING REQUEST: {message}

TASK TYPE: {task_type}

INSTRUCTIONS:
{task_instructions.get(task_type, task_instructions['general'])}

Additional rules:
- Always put code in ```python blocks
- Keep explanations clear and beginner-friendly unless profile says otherwise
- If there's an error — quote it exactly then explain it
- Test your logic mentally before providing code
- End with: "Want me to explain any part in more detail?"
"""

    response = safe_invoke(llm_strong, prompt)
    print(f"  Code response ready: {len(response)} chars")

    return {"agent_responses": [response]}