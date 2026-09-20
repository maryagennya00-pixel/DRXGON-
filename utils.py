# ============================================
# arya/utils.py
# Shared LLM instances + safe retry wrapper
# ============================================

import time, os, re, warnings
warnings.filterwarnings("ignore")

from langchain_groq import ChatGroq
from config import LLM_MODEL_FAST, LLM_MODEL_STRONG, GROQ_API_KEY

# Ensures ChatGroq() can find the key whether it came from .env locally
# or from st.secrets on Streamlit Cloud
os.environ["GROQ_API_KEY"] = GROQ_API_KEY


def _make_llm(model: str, temperature: float, effort: str) -> ChatGroq:
    """gpt-oss models reason before answering. 'low' keeps routing/short tasks fast;
    older langchain-groq versions without the field fall back to plain construction."""
    try:
        return ChatGroq(model=model, temperature=temperature, reasoning_effort=effort)
    except Exception:
        return ChatGroq(model=model, temperature=temperature)


llm_fast   = _make_llm(LLM_MODEL_FAST,   0.3, "low")
llm_strong = _make_llm(LLM_MODEL_STRONG, 0.5, "medium")

# Errors that will never succeed on retry — fail immediately instead of waiting.
_NON_RETRYABLE = ["404", "model_not_found", "401", "invalid_api_key", "400", "invalid_request"]


def safe_invoke(llm, messages, max_retries: int = 3, wait_seconds: int = 60) -> str:
    """
    Calls llm.invoke(messages) with automatic retry on rate limits / transient errors.
    Accepts either a plain string prompt or a list of message dicts.
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            text = llm.invoke(messages).content
            # Drop any <think> blocks a reasoning model may include in the content
            return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        except Exception as e:
            last_error = e
            msg = str(e).lower()
            if any(kw in msg for kw in _NON_RETRYABLE) and "rate limit" not in msg:
                raise
            is_rate_limit = any(kw in msg for kw in
                                 ["rate limit", "429", "quota", "too many requests"])
            wait = wait_seconds if is_rate_limit else 5
            if attempt < max_retries:
                time.sleep(wait)
                continue
            raise last_error
    raise last_error