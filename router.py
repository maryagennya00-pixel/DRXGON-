# ============================================
# arya/router.py
# ARYA Supervisor — LangGraph routing brain
# ============================================

import warnings
warnings.filterwarnings("ignore")

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Annotated, Optional
import operator, json, re
from config import AGENTS, ARYA_PERSONALITY, MAX_ITERATIONS
from utils import llm_fast, safe_invoke
from memory import build_memory_context, remember, load_profile, get_session_history, save_session
from langchain_community.chat_message_histories import ChatMessageHistory

# ── ARYA STATE ────────────────────────────────

class ARYAState(TypedDict):
    user_message:      str
    session_id:         str
    user_profile:       dict
    memory_context:     str
    conversation_history_text: str
    selected_agent:     str
    last_agent:         str
    routing_reason:     str
    agent_responses:    Annotated[List[str], operator.add]
    final_response:     str
    memories_to_save:   List[dict]
    iteration:          int
    completed:          bool
    error:              Optional[str]


# ── SUPERVISOR NODE ───────────────────────────

SUPERVISOR_PROMPT = f"""{ARYA_PERSONALITY}

You are ARYA's routing supervisor. Your job: decide which specialist agent
should handle the user's request.

AVAILABLE AGENTS:
{json.dumps({k: {"name": v["name"], "description": v["description"]} for k, v in AGENTS.items()}, indent=2)}

RESPOND IN JSON ONLY:
{{
  "selected_agent": "agent_key",
  "routing_reason": "one sentence why this agent",
  "memories_to_extract": ["any facts from the message worth remembering"],
  "memory_categories":   ["category for each fact: preference/goal/fact/event/person/work"]
}}

Rules:
- researcher: for information lookup, research, factual questions
- writer: for any writing task — emails, posts, content
- planner: for tasks, scheduling, goals, step-by-step plans
- analyst: for math, calculations, data analysis, comparisons
- news: for current events, recent happenings, today's news
- coder: for code help, debugging, technical implementation

If request spans multiple agents — pick the PRIMARY one."""


def supervisor_node(state: ARYAState) -> dict:
    print(f"\n[ARYA Supervisor] Processing: {state['user_message'][:60]}")

    last_agent   = state.get("last_agent", "")
    history_text = state.get("conversation_history_text", "No conversation history yet.")
    preferred    = state.get("user_profile", {}).get("preferences", {}).get("preferred_agents", [])

    prompt = f"""USER MESSAGE: {state['user_message']}

MEMORY CONTEXT:
{state['memory_context']}

RECENT CONVERSATION:
{history_text}

LAST AGENT USED: {last_agent or 'none yet'}
If this message is a short, ambiguous follow-up (e.g. "what is the error?",
"why?", "fix it") with no clear new topic, STRONGLY prefer routing back to
the LAST AGENT USED rather than switching specialists.

PREFERRED AGENTS (favor these when a request could fit several): {', '.join(preferred) or 'none set'}

Decide which agent handles this."""

    try:
        response = safe_invoke(llm_fast, [
            {"role": "system", "content": SUPERVISOR_PROMPT},
            {"role": "user",   "content": prompt}
        ])

        clean  = re.sub(r'```json|```', '', response).strip()
        result = json.loads(clean)

        selected = result.get("selected_agent", "researcher")
        if selected not in AGENTS:
            selected = "researcher"
        reason   = result.get("routing_reason", "")
        memories = result.get("memories_to_extract", [])
        cats     = result.get("memory_categories", [])

        memories_to_save = []
        for i, memory in enumerate(memories):
            if memory.strip():
                cat = cats[i] if i < len(cats) else "fact"
                memories_to_save.append({"fact": memory, "category": cat})

        print(f"  -> {selected}: {reason}")

    except Exception as e:
        selected = "researcher"
        reason   = f"Fallback routing: {e}"
        memories_to_save = []

    return {
        "selected_agent":   selected,
        "routing_reason":   reason,
        "memories_to_save": memories_to_save,
        "iteration":        state["iteration"] + 1
    }


def route_to_agent(state: ARYAState) -> str:
    if state["iteration"] >= MAX_ITERATIONS:
        return "compose_response"
    return state["selected_agent"]


# ── RESPONSE COMPOSER ─────────────────────────

def compose_response(state: ARYAState) -> dict:
    print(f"\n[ARYA] Composing final response...")

    agent_output = "\n\n".join(state["agent_responses"]) if state["agent_responses"] else ""

    if not agent_output:
        agent_output = "I wasn't able to process that request. Could you rephrase?"

    for mem in state.get("memories_to_save", []):
        try:
            remember(mem["fact"], mem["category"], state["session_id"])
        except Exception:
            pass

    final = agent_output

    return {"final_response": final, "completed": True}


# ── HELPER FUNCTIONS ──────────────────────────

def _format_history(session_id: str) -> str:
    try:
        history = get_session_history(session_id)
        if not history.messages:
            return "No conversation history yet."
        from langchain_core.messages import HumanMessage
        recent = history.messages[-8:]
        lines = [f"{'User' if isinstance(m, HumanMessage) else 'ARYA'}: {m.content[:100]}" for m in recent]
        return "\n".join(lines)
    except Exception:
        return "History unavailable."


# ── BUILD ARYA GRAPH ──────────────────────────

def build_arya_graph(agent_nodes: dict) -> object:
    builder = StateGraph(ARYAState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("compose_response", compose_response)

    for name, fn in agent_nodes.items():
        builder.add_node(name, fn)

    builder.add_edge(START, "supervisor")

    for name in agent_nodes.keys():
        builder.add_edge(name, "compose_response")

    builder.add_edge("compose_response", END)

    routes = {name: name for name in agent_nodes.keys()}
    routes["compose_response"] = "compose_response"

    builder.add_conditional_edges("supervisor", route_to_agent, routes)

    return builder.compile()


# ── ARYA CHAT FUNCTION ────────────────────────

_arya_graph = None
_last_agent_by_session: dict = {}


def arya_chat(message: str, session_id: str = "arya_main", graph=None) -> dict:
    global _arya_graph
    if graph:
        _arya_graph = graph

    if _arya_graph is None:
        return {
            "final_response": "ARYA is not fully initialized yet. Build the agent graph first.",
            "selected_agent": "none",
            "routing_reason": "Not initialized"
        }

    profile        = load_profile()
    memory_context = build_memory_context(message, profile)

    initial_state = {
        "user_message":    message,
        "session_id":      session_id,
        "user_profile":    profile,
        "memory_context":  memory_context,
        "conversation_history_text": _format_history(session_id),
        "last_agent":     _last_agent_by_session.get(session_id, ""),
        "selected_agent":  "",
        "routing_reason":  "",
        "agent_responses": [],
        "final_response":  "",
        "memories_to_save":[],
        "iteration":       0,
        "completed":       False,
        "error":           None
    }

    try:
        result = _arya_graph.invoke(initial_state)
        _last_agent_by_session[session_id] = result.get("selected_agent", "")
        turn = ChatMessageHistory()
        turn.add_user_message(message)
        turn.add_ai_message(result.get("final_response", ""))
        save_session(turn, session_id)
        return result
    except Exception as e:
        return {
            "final_response": f"I encountered an error: {str(e)}. Please try again.",
            "selected_agent": "error",
            "routing_reason": str(e),
            "error": str(e)
        }


# ── TEST THE ROUTER ───────────────────────────
if __name__ == "__main__":
    print("\n=== ROUTER TEST ===")

    def mock_researcher(state): return {"agent_responses": ["Research result: test"]}
    def mock_writer(state):     return {"agent_responses": ["Written content: test"]}
    def mock_planner(state):    return {"agent_responses": ["Plan: test"]}
    def mock_analyst(state):    return {"agent_responses": ["Analysis: test"]}
    def mock_news(state):       return {"agent_responses": ["News: test"]}
    def mock_coder(state):      return {"agent_responses": ["Code: test"]}

    mock_agents = {
        "researcher": mock_researcher, "writer": mock_writer, "planner": mock_planner,
        "analyst": mock_analyst, "news": mock_news, "coder": mock_coder,
    }

    test_graph = build_arya_graph(mock_agents)

    test_messages = [
        "Research the latest developments in AI agents",
        "Write me a professional email to my manager",
        "Calculate 15% of PKR 85,000",
        "What's happening in the news today?",
        "Help me debug this Python function",
    ]

    for msg in test_messages:
        result = arya_chat(msg, graph=test_graph)
        agent = result.get("selected_agent", "unknown")
        print(f"\n'{msg[:50]}...'")
        print(f"  -> {agent}: {result.get('routing_reason', '')[:60]}")