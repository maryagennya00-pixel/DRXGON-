# arya/agents/planner.py
import warnings
warnings.filterwarnings("ignore")

from config import get_full_personality
from utils import llm_strong, safe_invoke
from datetime import datetime


def planner_node(state: dict) -> dict:
    """Planning Specialist — tasks, goals, schedules, step-by-step plans."""
    message        = state["user_message"]
    memory_context = state.get("memory_context", "")
    profile        = state.get("user_profile", {})
    user_name      = profile.get("name", "")
    user_goals     = profile.get("goals", [])
    today          = datetime.now().strftime("%A, %B %d, %Y")

    print(f"\n[Planner] Processing: {message[:60]}")

    goals_context = f"\nUser's known goals: {', '.join(user_goals[:3])}" if user_goals else ""

    prompt = f"""{get_full_personality()}

Today is: {today}
{f"Planning for: {user_name}" if user_name else ""}
{goals_context}

MEMORY CONTEXT:
{memory_context[:400]}

PLANNING REQUEST: {message}

Create a practical, actionable plan. Include:

## Goal
[One clear sentence stating what success looks like]

## Action Steps
[Numbered steps — specific, concrete, in order]
[Each step: what to do, how long it takes, any dependencies]

## Timeline
[Realistic timeline for the full plan]

## Potential Blockers
[2-3 things that could slow this down and how to handle them]

## First Step You Can Take Right Now
[One concrete immediate action]

Make it specific to their situation based on the memory context."""

    response = safe_invoke(llm_strong, prompt)
    print(f"  Plan created: {len(response)} chars")

    return {"agent_responses": [response]}