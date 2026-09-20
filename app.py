# ============================================
# arya/app.py
# DRXGON — Main Streamlit Chat Interface
# ============================================

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import os, tempfile, inspect

st.set_page_config(
    page_title="DRXGON — Personal AI Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

from theme import inject_theme, section_label
inject_theme()

IMAGE_EXT = ["jpg", "jpeg", "png", "webp"]
AUDIO_EXT = ["mp3", "mp4", "wav", "m4a", "webm", "ogg"]

# Attach (+) and mic buttons inside the chat bar need a recent Streamlit.
_CHAT_PARAMS = inspect.signature(st.chat_input).parameters
HAS_MEDIA_INPUT = "accept_file" in _CHAT_PARAMS and "accept_audio" in _CHAT_PARAMS


# ── LOAD DRXGON ───────────────────────────────
@st.cache_resource
def load_arya():
    """Initialize DRXGON once and cache across reruns"""
    from main import initialize_arya
    return initialize_arya()


try:
    arya_graph = load_arya()
    import router
    router._arya_graph = arya_graph
    ARYA_READY = True
except Exception as e:
    ARYA_READY = False
    st.error(f"DRXGON initialization failed: {e}")

from memory  import load_profile, update_profile, remember, get_memory_summary
from config  import AGENTS, ARYA_NAME, ARYA_VERSION, ARYA_DESCRIPTION
from main    import arya_multimodal
from voice   import voice_input_to_text


# ── SESSION STATE ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "arya_streamlit"


def _save_temp(filename: str, data: bytes) -> str:
    """Write bytes to a cross-platform temp path and return it."""
    path = os.path.join(tempfile.gettempdir(), f"arya_{filename.replace(' ', '_')}")
    with open(path, "wb") as f:
        f.write(data)
    return path


def _user_count() -> int:
    return len([m for m in st.session_state.messages if m["role"] == "user"])


# ── SIDEBAR ───────────────────────────────────
with st.sidebar:
    profile = load_profile()

    section_label("Profile")
    user_name = st.text_input("Your name", value=profile.get("name", ""), placeholder="Enter your name...")
    if user_name and user_name != profile.get("name"):
        update_profile("name", user_name)
        remember(f"User's name is {user_name}", "fact")

    section_label("Personality")
    PERSONALITY_PRESETS = [
        "Professional", "Friendly", "Mentor", "Direct", "Creative",
        "Analytical", "Supportive", "Custom"
    ]
    current_style = profile.get("preferences", {}).get("personality", "Professional")
    style_choice = st.selectbox(
        "Personality type", PERSONALITY_PRESETS,
        index=PERSONALITY_PRESETS.index(current_style) if current_style in PERSONALITY_PRESETS else 0,
        key="sidebar_personality_choice"
    )
    custom_personality_text = st.text_area(
        "Describe how DRXGON should behave (optional)",
        value=profile.get("preferences", {}).get("custom_personality", ""),
        placeholder="e.g. Be blunt, skip pleasantries, prioritize technical accuracy.",
        height=80,
        key="sidebar_personality_text"
    )
    if st.button("Save Personality", use_container_width=True):
        update_profile("preferences.personality", style_choice)
        update_profile("preferences.custom_personality", custom_personality_text.strip())
        st.success("Personality saved.")

    section_label("Memory")
    mem_summary = get_memory_summary()
    st.caption(mem_summary[:100] + "..." if len(mem_summary) > 100 else mem_summary)
    if st.button("View Full Memory", use_container_width=True):
        st.switch_page("pages/2_Memory.py")

    section_label("Voice")
    speak_replies = st.toggle("Speak replies", value=True, key="speak_replies")
    if not HAS_MEDIA_INPUT:
        st.warning("Attach and mic buttons need a newer Streamlit: pip install -U streamlit")

    section_label("Session")
    metric_slot = st.empty()
    metric_slot.metric("Messages this session", _user_count())

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    section_label("Pages")
    if st.button("Memory", use_container_width=True, key="nav_memory"):
        st.switch_page("pages/2_Memory.py")
    if st.button("Settings", use_container_width=True, key="nav_settings"):
        st.switch_page("pages/3_Settings.py")

    st.caption(f"DRXGON v{ARYA_VERSION} | MNE Enterprise")


# ── MAIN INTERFACE ────────────────────────────
st.markdown("""
<div class="arya-header">
    <div class="arya-hatch"></div>
    <div class="arya-name">DRXGON</div>
    <div class="arya-tagline">AGENTIC INTELLIGENCE — ENGINEERED FOR PRECISION</div>
</div>
""", unsafe_allow_html=True)

if not ARYA_READY:
    st.warning("DRXGON is not ready. Check your API keys and restart.")
    st.stop()

if not st.session_state.messages and not profile.get("name"):
    greeting = ("Good day. I am DRXGON, your personal AI assistant.\n\n"
                "I bring six specialist capabilities — Research, Writing, Planning, "
                "Analysis, News, and Code. Use the attach and mic buttons in the "
                "message bar to share an image, a file, or your voice.\n\n"
                "How may I assist you today?")
    with st.chat_message("assistant", avatar=None):
        st.markdown(greeting)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=None):
        st.markdown(msg["content"])
        if msg.get("agent"):
            agent_info = AGENTS.get(msg["agent"], {})
            st.markdown(f'<div class="agent-badge">{agent_info.get("name", msg["agent"])}</div>',
                        unsafe_allow_html=True)


# ── CHAT INPUT (text + attach + mic in one bar) ──
if HAS_MEDIA_INPUT:
    submission = st.chat_input("Ask DRXGON anything...", accept_file=True,
                               file_type=IMAGE_EXT + AUDIO_EXT, accept_audio=True)
else:
    submission = st.chat_input("Ask DRXGON anything...")

user_input, image_path, audio_path = None, None, None

if submission:
    if isinstance(submission, str):
        user_input = submission.strip() or None
    else:
        user_input = (submission.text or "").strip() or None
        for f in (getattr(submission, "files", None) or []):
            ext  = f.name.rsplit(".", 1)[-1].lower()
            path = _save_temp(f.name, f.getvalue())
            if ext in IMAGE_EXT and not image_path:
                image_path = path
            elif ext in AUDIO_EXT and not audio_path:
                audio_path = path
        rec = getattr(submission, "audio", None)          # mic recording (wav)
        if rec is not None and not audio_path:
            audio_path = _save_temp("recorded.wav", rec.getvalue())

    # Voice / audio file -> text FIRST, so the transcript shows in the user bubble
    if audio_path:
        with st.spinner("Transcribing..."):
            heard = voice_input_to_text(audio_path=audio_path)
        spoken = heard.get("text", "")
        if spoken:
            user_input = f"{user_input} {spoken}".strip() if user_input else spoken
        else:
            st.warning(f"Could not transcribe the audio: {heard.get('error') or 'no speech detected'}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            audio_path = None

if user_input or image_path:
    display_text = user_input or "Image shared"

    with st.chat_message("user", avatar=None):
        st.markdown(display_text)
        if image_path:
            st.image(image_path, width=200)
        if audio_path:
            st.audio(audio_path)

    st.session_state.messages.append({"role": "user", "content": display_text})
    metric_slot.metric("Messages this session", _user_count())

    with st.chat_message("assistant", avatar=None):
        with st.spinner("DRXGON is thinking..."):
            result = arya_multimodal(
                text=user_input, image_path=image_path,
                session_id=st.session_state.session_id,
                speak=speak_replies
            )

        response   = result.get("final_response", "I couldn't process that.")
        agent_key  = result.get("agent", "")
        agent_info = AGENTS.get(agent_key, {})

        st.markdown(response)
        tts = result.get("tts")
        if tts and tts.get("success"):
            st.audio(tts["audio_bytes"], format="audio/wav", autoplay=True)
        st.markdown(
            f'<div class="agent-badge">{agent_info.get("name","DRXGON")} '
            f'| {result.get("routing_reason","")[:50]}</div>',
            unsafe_allow_html=True
        )

    st.session_state.messages.append({"role": "assistant", "content": response, "agent": agent_key})

    # Clean up temp files (no st.rerun(): it would cut off the autoplaying reply audio)
    for p in (image_path, audio_path):
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass