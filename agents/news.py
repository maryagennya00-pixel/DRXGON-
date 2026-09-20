# arya/agents/news.py
import warnings
warnings.filterwarnings("ignore")

from langchain_community.tools.tavily_search import TavilySearchResults
from config import get_full_personality
from utils import llm_fast, llm_strong, safe_invoke
from datetime import datetime

search = TavilySearchResults(max_results=6)


def news_node(state: dict) -> dict:
    """News Specialist — current events, recent news, updates."""
    message        = state["user_message"]
    memory_context = state.get("memory_context", "")
    today          = datetime.now().strftime("%B %d, %Y")

    print(f"\n[News] Processing: {message[:60]}")

    query_prompt = f"""Convert to a news search query for today {today}:
Request: {message}
Return ONLY the search query. Include "2026" or "latest" for recency."""

    search_query = safe_invoke(llm_fast, query_prompt).strip().strip('"')
    print(f"  News query: {search_query}")

    try:
        results = search.invoke(search_query)
        news_content = "\n\n".join([
            f"[{r.get('url','').split('/')[2] if r.get('url') else 'source'}]\n"
            f"{r.get('content','')[:350]}"
            for r in results if isinstance(r, dict)
        ])
    except Exception as e:
        news_content = f"News search unavailable: {e}"

    prompt = f"""{get_full_personality()}

Today's date: {today}

MEMORY CONTEXT:
{memory_context[:300]}

NEWS REQUEST: {message}

CURRENT NEWS AND INFORMATION:
{news_content[:2500]}

Write a news briefing:

## Today's Briefing — {today}

### Key Stories
[3-5 bullet points of main developments]

### What This Means
[2-3 sentences on significance and context]

### Sources
[Brief source attribution]

Keep it concise — this is a briefing, not an essay."""

    response = safe_invoke(llm_strong, prompt)
    print(f"  News briefing ready: {len(response)} chars")

    return {"agent_responses": [response]}