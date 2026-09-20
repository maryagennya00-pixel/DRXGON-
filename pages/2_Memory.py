# ==============================================================================
# # arya/pages/2_Memory.py
# ==============================================================================

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
from memory import long_term_store, recall, remember, forget, load_profile

st.set_page_config(page_title="DRXGON Memory", page_icon=None, layout="wide")

from theme import inject_theme
inject_theme()

st.markdown("## DRXGON Memory Manager")
st.caption("View, add, and remove what DRXGON remembers about you")
st.markdown("---")

count = long_term_store._collection.count()
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Memories", count)
with col2:
    profile = load_profile()
    st.metric("Sessions", profile.get("total_sessions", 1))

st.markdown("---")
st.markdown("### Search Memories")
search_query = st.text_input("Search for a memory...", placeholder="e.g. preferences, goals, work")
if search_query:
    results = recall(search_query, k=8)
    st.markdown("**Results:**")
    if "No relevant memories" in results:
        st.info("No memories found for that query.")
    else:
        for line in results.split("\n"):
            if line.strip():
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.03);border-left:2px solid rgba(255,255,255,0.35);'
                    f'padding:8px 12px;border-radius:0;margin:4px 0;font-size:0.85rem">{line}</div>',
                    unsafe_allow_html=True
                )

st.markdown("---")
st.markdown("### Add a Memory")
col_a, col_b = st.columns([3, 1])
with col_a:
    new_memory = st.text_input("What should DRXGON remember?", placeholder="I prefer responses in bullet points")
with col_b:
    category = st.selectbox("Category", ["preference", "goal", "fact", "person", "work", "event"])

if st.button("Save Memory", type="primary"):
    if new_memory.strip():
        remember(new_memory.strip(), category)
        st.success(f"Memory saved: {new_memory[:60]}")
        st.rerun()
    else:
        st.warning("Please enter something to remember.")

st.markdown("---")
st.markdown("### Remove a Memory")
forget_query = st.text_input("What should DRXGON forget?", placeholder="my old job")
if st.button("Forget This"):
    if forget_query.strip():
        st.info(forget(forget_query.strip()))
    else:
        st.warning("Please enter what to forget.")

st.markdown("---")
st.markdown("### Your Profile")
st.json({k: v for k, v in profile.items() if k not in ["created_at", "last_seen"]})