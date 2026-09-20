# ============================================
# arya/memory.py
# ARYA Memory System — Three Layers
# Layer 1: Conversation history (short-term)
# Layer 2: Long-term vector store (semantic)
# Layer 3: User profile JSON (structured)
# ============================================

import warnings
warnings.filterwarnings("ignore")

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

try:
    from langchain_community.chat_message_histories import ChatMessageHistory
except ImportError:
    from langchain_core.chat_history import InMemoryChatMessageHistory as ChatMessageHistory

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from config import (EMBEDDING_MODEL, VECTOR_STORE_DIR,
                     PROFILE_PATH, SESSION_DIR,
                     CONVERSATION_WINDOW, MEMORY_TOP_K)
from datetime import datetime
import json, os, copy

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

# ── EMBEDDINGS ────────────────────────────────
print("Loading embeddings...")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# ── LAYER 2: LONG-TERM VECTOR STORE ──────────
long_term_store = Chroma(
    embedding_function=embeddings,
    collection_name="arya_memory",
    persist_directory=VECTOR_STORE_DIR
)
print(f"Long-term memory: {long_term_store._collection.count()} memories")


# ── LAYER 1: CONVERSATION HISTORY ─────────────

def get_session_history(session_id: str = "arya_main") -> ChatMessageHistory:
    """Load or create conversation history for a session"""
    path = f"{SESSION_DIR}/{session_id}.json"
    history = ChatMessageHistory()

    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
        for msg in data[-CONVERSATION_WINDOW * 2:]:
            if msg["type"] == "human":
                history.add_user_message(msg["content"])
            else:
                history.add_ai_message(msg["content"])

    return history


def save_session(history: ChatMessageHistory, session_id: str = "arya_main"):
    """Save conversation history to JSON"""
    path = f"{SESSION_DIR}/{session_id}.json"
    messages = []

    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                messages = json.load(f)
            except Exception:
                messages = []

    for msg in history.messages:
        entry = {
            "type":      "human" if isinstance(msg, HumanMessage) else "ai",
            "content":   msg.content,
            "timestamp": datetime.now().isoformat()
        }
        if not any(m["content"] == entry["content"] for m in messages[-4:]):
            messages.append(entry)

    messages = messages[-200:]

    with open(path, 'w') as f:
        json.dump(messages, f, indent=2)


# ── LAYER 2: LONG-TERM MEMORY OPERATIONS ──────

def remember(fact: str, category: str = "general", session_id: str = "arya_main"):
    """
    Save a fact to long-term memory.
    Categories: preference, goal, fact, event, person, work
    """
    doc = Document(
        page_content=fact,
        metadata={
            "category":   category,
            "session_id": session_id,
            "timestamp":  datetime.now().isoformat(),
            "date":       datetime.now().strftime("%Y-%m-%d")
        }
    )
    long_term_store.add_documents([doc])
    return f"Remembered: {fact}"


def recall(query: str, k: int = MEMORY_TOP_K, category: str = None) -> str:
    """Retrieve relevant memories for a query. Optional category filter."""
    if category:
        try:
            results = long_term_store.similarity_search(query, k=k, filter={"category": category})
            if not results:
                results = long_term_store.similarity_search(query, k=k)
        except Exception:
            results = long_term_store.similarity_search(query, k=k)
    else:
        results = long_term_store.similarity_search(query, k=k)

    if not results:
        return "No relevant memories found."

    memories = []
    for doc in results:
        date = doc.metadata.get("date", "unknown date")
        cat  = doc.metadata.get("category", "general")
        memories.append(f"[{cat} • {date}] {doc.page_content}")

    return "\n".join(memories)


def forget(query: str) -> str:
    """
    Remove memories matching a query.
    NOTE: similarity_search() results don't reliably expose stable document IDs
    in all Chroma versions, so this queries the underlying collection directly
    instead — more reliable than relying on doc.id from search results.
    """
    matches = long_term_store.similarity_search(query, k=5)
    if not matches:
        return "No matching memories found to remove."

    # Query the raw collection to get real IDs matching this content
    raw = long_term_store._collection.get(
        where_document={"$contains": query} if query else None
    )
    ids_to_delete = raw.get("ids", [])[:5] if raw else []

    if ids_to_delete:
        long_term_store._collection.delete(ids=ids_to_delete)
        return f"Removed {len(ids_to_delete)} memories related to '{query}'"

    return "Could not confidently identify memories to remove — try being more specific."


def get_memory_summary() -> str:
    """Get a summary of what ARYA remembers about the user"""
    count = long_term_store._collection.count()
    if count == 0:
        return "No long-term memories yet."

    try:
        all_docs = long_term_store.similarity_search("user preferences goals", k=8)
        if all_docs:
            summary = f"I have {count} memories stored. Recent examples:\n"
            for doc in all_docs[:5]:
                cat = doc.metadata.get("category", "general")
                summary += f"• [{cat}] {doc.page_content[:80]}\n"
            return summary
    except Exception:
        pass

    return f"I have {count} memories stored."


# ── LAYER 3: USER PROFILE ─────────────────────

DEFAULT_PROFILE = {
    "name":           "",
    "profession":     "",
    "location":       "",
    "language":       "English",
    "goals":          [],
    "preferences": {
        "response_length":  "balanced",
        "formality":        "professional",
        "voice_enabled":    False,
        "preferred_agents": []
    },
    "created_at":     datetime.now().isoformat(),
    "last_seen":      datetime.now().isoformat(),
    "total_sessions": 0
}


def load_profile() -> dict:
    """Read-only load. (Previously this bumped total_sessions on EVERY call,
    which inflated the count on each Streamlit rerun.)"""
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, 'r') as f:
            return json.load(f)
    return copy.deepcopy(DEFAULT_PROFILE)


def start_session():
    """Call once per app start: bumps session count and last_seen."""
    profile = load_profile()
    profile["last_seen"]      = datetime.now().isoformat()
    profile["total_sessions"] = profile.get("total_sessions", 0) + 1
    save_profile(profile)


def save_profile(profile: dict):
    with open(PROFILE_PATH, 'w') as f:
        json.dump(profile, f, indent=2)


def update_profile(key: str, value) -> str:
    profile = load_profile()
    keys = key.split(".")

    if len(keys) == 1:
        profile[keys[0]] = value
    elif len(keys) == 2:
        if keys[0] not in profile:
            profile[keys[0]] = {}
        profile[keys[0]][keys[1]] = value

    save_profile(profile)
    return f"Profile updated: {key} = {value}"


def get_profile_context(profile: dict) -> str:
    if not profile.get("name"):
        return "New user — no profile yet."

    ctx = f"User: {profile['name']}"
    if profile.get("profession"):
        ctx += f" | {profile['profession']}"
    if profile.get("location"):
        ctx += f" | {profile['location']}"
    if profile.get("goals"):
        ctx += f"\nGoals: {', '.join(profile['goals'][:3])}"
    if profile.get("preferences", {}).get("response_length"):
        ctx += f"\nPrefers: {profile['preferences']['response_length']} responses"
    ctx += f"\nSessions: {profile.get('total_sessions', 1)}"
    return ctx


# ── COMBINED MEMORY CONTEXT ───────────────────

def build_memory_context(query: str, profile: dict) -> str:
    profile_ctx = get_profile_context(profile)
    long_term   = recall(query)

    return f"""USER PROFILE:
{profile_ctx}

RELEVANT MEMORIES:
{long_term}"""


def format_recent_history(history: ChatMessageHistory, max_turns: int = 6) -> str:
    """Format recent conversation turns as readable text for agent prompts."""
    if not history.messages:
        return "No conversation history yet — this is the first message."
    recent = history.messages[-(max_turns * 2):]
    lines = [f"{'User' if isinstance(m, HumanMessage) else 'ARYA'}: {m.content[:300]}" for m in recent]
    return "\n".join(lines)