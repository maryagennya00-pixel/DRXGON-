# arya/agents/analyst.py
import warnings
warnings.filterwarnings("ignore")

from config import get_full_personality
from utils import llm_strong, safe_invoke
import re, math


def safe_calculate(expression: str) -> str:
    """Safely evaluate mathematical expressions"""
    try:
        allowed = set("0123456789+-*/.()%, ")
        clean   = expression.strip()
        if not all(c in allowed for c in clean):
            clean = re.sub(r'[^0-9+\-*/().%]', '', clean)
        if clean:
            result = eval(clean, {"__builtins__": {}}, {"math": math})
            return str(round(result, 4))
        return "Could not evaluate"
    except Exception as e:
        return f"Calculation error: {e}"


def extract_calculations(text: str) -> list:
    """Extract mathematical expressions from text"""
    patterns = [
        r'\d+(?:\.\d+)?%\s+of\s+\d+(?:,\d{3})*(?:\.\d+)?',
        r'\d+(?:,\d{3})*(?:\.\d+)?\s*[+\-*/]\s*\d+(?:,\d{3})*(?:\.\d+)?',
    ]
    expressions = []
    for pattern in patterns:
        expressions.extend(re.findall(pattern, text, re.IGNORECASE))
    return expressions[:5]


def analyst_node(state: dict) -> dict:
    """Analysis Specialist — calculations, data analysis, comparisons."""
    message        = state["user_message"]
    memory_context = state.get("memory_context", "")
    profile        = state.get("user_profile", {})
    user_name      = profile.get("name", "")

    print(f"\n[Analyst] Processing: {message[:60]}")

    calcs = extract_calculations(message)
    calc_results = ""
    if calcs:
        results = []
        for expr in calcs:
            pct_match = re.match(r'(\d+(?:\.\d+)?)%\s+of\s+([\d,]+(?:\.\d+)?)', expr, re.I)
            if pct_match:
                pct = float(pct_match.group(1))
                val = float(pct_match.group(2).replace(',', ''))
                result = pct / 100 * val
                results.append(f"{expr} = {result:,.2f}")
            else:
                clean_expr = expr.replace(',', '')
                result = safe_calculate(clean_expr)
                results.append(f"{expr} = {result}")

        calc_results = "Pre-calculated: " + " | ".join(results)
        print(f"  {calc_results}")

    prompt = f"""{get_full_personality()}

{f"Analyzing for: {user_name}" if user_name else ""}

MEMORY CONTEXT:
{memory_context[:300]}

ANALYSIS REQUEST: {message}

{f"PRE-CALCULATED VALUES: {calc_results}" if calc_results else ""}

INSTRUCTIONS:
- Show ALL calculations explicitly — never just give a final number
- Format: "X × Y = Z" or "Formula: ..."
- Explain what each number means in context
- If comparing options — use a structured comparison table
- If the numbers reveal something important — highlight it
- Use PKR for Pakistani currency context
- End with a clear recommendation or conclusion based on the numbers

Structure your response with:
## Analysis
[Show the work]

## Key Insight
[What the numbers actually mean]

## Recommendation
[What to do based on the analysis]"""

    response = safe_invoke(llm_strong, prompt)
    print(f"  Analysis complete: {len(response)} chars")

    return {"agent_responses": [response]}