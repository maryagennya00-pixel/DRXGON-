# ============================================
# arya/theme.py
# Shared visual theme (Bklit UI style): near-black canvas, hairline grid with
# node markers at the intersections, ruler ticks on borders, hatched cells.
# Import inject_theme() at the top of app.py and every page.
# ============================================

import urllib.parse
import streamlit as st

CELL = 240  # grid cell size in px — keep in sync with the CSS below



def _ruler_data_uri(vertical: bool, length: int) -> str:
    """SVG ruler: minor tick /10px, major tick /50px, number /100px (rotated on the vertical one)."""
    W = 24 if vertical else length
    H = length if vertical else 22
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">']
    for i in range(0, length + 1, 10):
        major = i % 50 == 0
        size, op = (10, 0.6) if major else (5, 0.3)
        a = i + 0.5
        p.append(f'<line x1="0" y1="{a}" x2="{size}" y2="{a}" stroke="white" stroke-opacity="{op}"/>' if vertical
                 else f'<line x1="{a}" y1="0" x2="{a}" y2="{size}" stroke="white" stroke-opacity="{op}"/>')
    for i in range(100, length + 1, 100):
        style = 'font-family="monospace" font-size="8" fill="white" fill-opacity="0.5"'
        p.append(f'<text transform="translate(21 {i}) rotate(-90)" text-anchor="middle" {style}>{i}</text>' if vertical
                 else f'<text x="{i + 3}" y="19" {style}>{i}</text>')
    p.append('</svg>')
    return "data:image/svg+xml;utf8," + urllib.parse.quote("".join(p))

THEME_CSS = """
<style>
:root {
    --bg: #0a0b0d;
    --line: rgba(255,255,255,0.06);
    --line-strong: rgba(255,255,255,0.14);
    --text: #f2f2f2;
    --muted: #8a8f98;
}

/* Canvas: hairline grid + hollow node at every intersection.
   Same layers on the bottom bar (fixed) so lines stay aligned. */
.stApp,
[data-testid="stBottom"] {
    background-color: var(--bg) !important;
    background-image:
        radial-gradient(circle at 50% 50%, var(--bg) 0, var(--bg) 2.5px,
            rgba(255,255,255,0.32) 3px, rgba(255,255,255,0.32) 3.6px, transparent 4px),
        linear-gradient(var(--line) 1px, transparent 1px),
        linear-gradient(90deg, var(--line) 1px, transparent 1px) !important;
    background-size: 240px 240px !important;
    background-position: -120px -120px, 0 0, 0 0 !important;
    background-attachment: fixed !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"],
[data-testid="stChatInputContainer"],
.stChatInput { background: transparent !important; background-image: none !important; }

section[data-testid="stSidebar"] {
    background-color: #000 !important;
    border-right: 1px solid var(--line-strong);
}

/* Header block with ruler ticks drawn on its border */
.arya-header {
    position: relative;
    overflow: hidden;
    min-height: 240px;
    background: rgba(10,11,13,0.88);
    border: 1px solid var(--line-strong);
    border-radius: 2px;
    padding: 3.4rem 2rem 3rem 3.2rem;
    margin-bottom: 1.5rem;
}
.arya-header::before,
.arya-header::after { content: ""; position: absolute; pointer-events: none; z-index: 2; }
/* Numbered ruler on the border (top + left). Ticks start at the border edge. */
.arya-header::before {
    top: 0; left: 0; right: 0; height: 22px;
    background: url("__RULER_H__") 0 0 / auto 22px no-repeat;
}
.arya-header::after {
    top: 0; bottom: 0; left: 0; width: 24px;
    background: url("__RULER_V__") 0 0 / 24px auto no-repeat;
}
/* hatched cell */
.arya-hatch {
    position: absolute; top: 0; bottom: 0; right: 240px; width: 240px;
    border-left: 1px solid var(--line-strong);
    border-right: 1px solid var(--line-strong);
    background-image: repeating-linear-gradient(135deg,
        rgba(255,255,255,0.09) 0 1px, transparent 1px 7px);
}
@media (max-width: 1000px) { .arya-hatch { display: none; } }

.arya-name {
    position: relative; z-index: 1;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 5rem; font-weight: 800; color: #fff;
    letter-spacing: -1px; line-height: 1;
}
.arya-tagline {
    position: relative; z-index: 1;
    font-family: monospace; color: var(--muted);
    font-size: 1rem; margin-top: 0.8rem;
    text-transform: uppercase; letter-spacing: 1px;
}

/* Blocks: hairline borders, near-square corners */
.stChatMessage {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid var(--line) !important;
    border-radius: 2px !important;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--line-strong);
    border-radius: 2px;
    padding: 0.6rem 0.8rem;
}
.sidebar-label {
    font-family: monospace; font-size: 0.75rem; letter-spacing: 1px;
    color: var(--muted); border-bottom: 1px solid var(--line-strong);
    padding: 0.5rem 0 0.35rem 0; margin: 0.6rem 0 0.5rem 0;
}
.agent-badge {
    display: inline-block; margin-top: 6px; padding: 2px 10px;
    font-family: monospace; font-size: 0.72rem; color: var(--muted);
    border: 1px solid var(--line-strong); border-radius: 2px;
    background: rgba(255,255,255,0.03);
}

/* Chat input: ONE outer block; every inner layer transparent (no double box, no red focus line) */
[data-testid="stChatInput"] {
    background: #050505 !important;
    border: 1px solid var(--line-strong) !important;
    border-radius: 2px !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stChatInput"]:focus-within { border-color: rgba(255,255,255,0.45) !important; }
[data-testid="stChatInput"] div,
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    border-radius: 0 !important;
    color: var(--text) !important;
}
[data-testid="stChatInputFileUploadButton"],
[data-testid="stChatInputMicButton"],
[data-testid="stChatInputStopButton"],
[data-testid="stChatInputApproveButton"],
[data-testid="stChatInputCancelButton"] {
    background: transparent !important;
    border: none !important;
    border-radius: 2px !important;
    color: var(--text) !important;
}
[data-testid="stChatInputFileUploadButton"]:hover,
[data-testid="stChatInputMicButton"]:hover { background: rgba(255,255,255,0.08) !important; }
[data-testid="stChatInputSubmitButton"] {
    background: transparent !important;
    border: 1px solid var(--line-strong) !important;
    border-radius: 2px !important;
}
[data-testid="stChatInputSubmitButton"] svg { fill: #fff !important; }

/* Other inputs */
div[data-baseweb="textarea"],
div[data-baseweb="base-input"],
div[data-baseweb="input"],
div[data-baseweb="select"] > div {
    background-color: #050505 !important;
    border: 1px solid var(--line-strong) !important;
    border-radius: 2px !important;
}
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="base-input"]:focus-within,
div[data-baseweb="input"]:focus-within { border-color: rgba(255,255,255,0.45) !important; }

div[data-testid="stButton"] button,
button[kind="secondary"],
[data-testid="stFileUploader"] button {
    background-color: #0a0a0a !important;
    color: var(--text) !important;
    border: 1px solid var(--line-strong) !important;
    border-radius: 2px !important;
    white-space: nowrap;
}
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] {
    background-color: #f2f2f2 !important;
    color: #0a0a0a !important;
    border-color: #f2f2f2 !important;
}
div[data-testid="stButton"] button:hover { border-color: rgba(255,255,255,0.4) !important; }
[data-testid="stFileUploaderDropzone"] {
    background-color: #050505 !important;
    border: 1px dashed var(--line-strong) !important;
    border-radius: 2px !important;
}

/* No avatars in chat */
[data-testid^="stChatMessageAvatar"],
[data-testid^="chatAvatarIcon"] { display: none !important; }

iframe[title*="paste"] { background: transparent !important; }
</style>
"""


def inject_theme():
    """Apply the DRXGON theme. Call once per page, right after set_page_config."""
    css = (THEME_CSS
           .replace("__RULER_H__", _ruler_data_uri(False, 3200))
           .replace("__RULER_V__", _ruler_data_uri(True, 600)))
    st.markdown(css, unsafe_allow_html=True)


def section_label(text: str):
    """Sidebar/section heading styled as a hairline-ruled label."""
    st.markdown(f'<div class="sidebar-label">{text}</div>', unsafe_allow_html=True)