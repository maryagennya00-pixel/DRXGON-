# arya/agents/researcher.py
import warnings
warnings.filterwarnings("ignore")

from langchain_community.tools.tavily_search import TavilySearchResults
from config import get_full_personality
from utils import llm_fast, llm_strong, safe_invoke

search = TavilySearchResults(max_results=5)


def researcher_node(state: dict) -> dict:
    """Research Specialist — web search + synthesis."""
    message        = state["user_message"]
    memory_context = state.get("memory_context", "")
    profile        = state.get("user_profile", {})
    user_name      = profile.get("name", "")

    print(f"\n[Researcher] Processing: {message[:60]}")

    query_prompt = f"""Convert this request into the best web search query.
Request: {message}
Return ONLY the search query — nothing else. 5-8 words."""

    search_query = safe_invoke(llm_fast, query_prompt).strip().strip('"')
    print(f"  Search query: {search_query}")

    try:
        results = search.invoke(search_query)
        raw_results = "\n\n".join([
            f"[Source: {r.get('url','unknown')}]\n{r.get('content','')[:400]}"
            for r in results if isinstance(r, dict)
        ])
    except Exception as e:
        raw_results = f"Search unavailable: {e}. Using knowledge only."

    synthesis_prompt = f"""{get_full_personality()}

{f"User: {user_name}" if user_name else ""}

MEMORY CONTEXT:
{memory_context[:500]}

USER REQUEST: {message}

WEB SEARCH RESULTS:
{raw_results[:2500]}

INSTRUCTIONS:
- Answer the request using the search results above
- Be specific — include actual facts, numbers, dates from the results
- Cite sources naturally in the text
- If search results are limited — supplement with your knowledge but say so
- Format with markdown for readability
- End with one relevant follow-up suggestion"""

    response = safe_invoke(llm_strong, synthesis_prompt)
    print(f"  Research complete: {len(response)} chars")

    return {"agent_responses": [response]}