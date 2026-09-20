# ==============================================================================
# # arya/pages/3_Settings.py
# ==============================================================================

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
from memory import load_profile, update_profile, remember
from config import AGENTS


def safe_index(options: list, value, default=0) -> int:
    """Avoids crashing if a saved preference isn't in the current options list."""
    try:
        return options.index(value)
    except ValueError:
        return default


st.set_page_config(page_title="DRXGON Settings", page_icon=None, layout="wide")

from theme import inject_theme
inject_theme()

st.markdown("## DRXGON Settings")
st.caption("Customize DRXGON's personality and behavior")
st.markdown("---")

profile = load_profile()
prefs = profile.get("preferences", {})

st.markdown("### Personal Information")
col1, col2 = st.columns(2)
with col1:
    name       = st.text_input("Your name", value=profile.get("name", ""))
    profession = st.text_input("Your profession", value=profile.get("profession", ""))
with col2:
    location = st.text_input("Your location", value=profile.get("location", ""))
    lang_options = ["English", "Urdu", "Hindi", "Arabic", "Turkish", "Kurdish Kurmanji", "Mixed (Urdu/English)"]
    language = st.selectbox("Preferred language", lang_options,
                            index=safe_index(lang_options, profile.get("language", "English")))

goals_text = st.text_area(
    "Your current goals (one per line)",
    value="\n".join(profile.get("goals", [])),
    height=100,
    placeholder="Learn AI development\nStart freelancing\nBuild a SaaS product"
)

st.markdown("---")
st.markdown("### DRXGON Behavior")
col3, col4 = st.columns(2)
with col3:
    length_options = ["concise", "balanced", "detailed"]
    response_length = st.selectbox("Response length", length_options,
                                   index=safe_index(length_options, prefs.get("response_length", "balanced")))
    formality_options = ["casual", "professional", "formal"]
    formality = st.selectbox("Communication style", formality_options,
                             index=safe_index(formality_options, prefs.get("formality", "professional")))
with col4:
    voice_enabled = st.toggle("Enable voice output (TTS)", value=prefs.get("voice_enabled", False))
    show_agent = st.toggle("Show which agent responded", value=True)

st.markdown("**Preferred specialists (DRXGON prioritizes these):**")
all_agent_keys = list(AGENTS.keys())
preferred = st.multiselect(
    "Select preferred agents", options=all_agent_keys,
    default=[k for k in prefs.get("preferred_agents", []) if k in all_agent_keys],
    format_func=lambda k: AGENTS[k]['name']
)

st.markdown("---")
st.markdown("### DRXGON Personality")
personality_options = {
    "Professional": "Formal, precise, business-focused. No jokes.",
    "Friendly":     "Warm, conversational, uses humor occasionally.",
    "Mentor":       "Teaches and explains. Patient and encouraging.",
    "Direct":       "Minimal words. Gets straight to the point.",
    "Creative":     "Imaginative, uses metaphors, thinks outside the box.",
    "Analytical":   "Data-driven and rigorous. Shows reasoning and assumptions.",
    "Supportive":   "Encouraging and empathetic, still accurate and practical.",
    "Custom":       "Follows the custom behavior note from the sidebar."
}
personality_keys = list(personality_options.keys())
current_personality = prefs.get("personality", "Professional")
personality_choice = st.selectbox(
    "DRXGON's personality style", options=personality_keys,
    index=safe_index(personality_keys, current_personality)
)
st.caption(personality_options[personality_choice])

st.markdown("---")

if st.button("Save All Settings", type="primary", use_container_width=True):
    if name:
        update_profile("name", name)
        remember(f"User's name is {name}", "fact")
    if profession:
        update_profile("profession", profession)
        remember(f"User works as {profession}", "fact")
    if location:
        update_profile("location", location)
    update_profile("language", language)

    goals_list = [g.strip() for g in goals_text.split("\n") if g.strip()]
    update_profile("goals", goals_list)
    if goals_list:
        remember(f"User's goals: {', '.join(goals_list[:3])}", "goal")

    update_profile("preferences.response_length", response_length)
    update_profile("preferences.formality", formality)
    update_profile("preferences.voice_enabled", voice_enabled)
    update_profile("preferences.preferred_agents", preferred)
    update_profile("preferences.personality", personality_choice)

    st.success("Settings saved! DRXGON will adapt to your preferences.")
    st.balloons()