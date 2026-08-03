"""
app.py
------
Streamlit entry point.

Run with:
    streamlit run app.py

Flow per message:
    1. User types a question in the chat box
    2. Router agent labels it QA / QUIZ / DEADLINE
    3. The matching sub-agent retrieves context from ChromaDB and
       calls Groq to generate a reply
    4. Reply + label are stored in session memory and shown in the chat
"""
import streamlit as st

from memory import SessionMemory
from agents.router import route
from agents import qa_agent, quiz_agent, deadline_agent

st.set_page_config(page_title="Campus Copilot", page_icon="🎓")

# ---------------------------------------------------------------------------
# Agent styling: each specialist gets its own color + icon, like a
# highlighter tab for a subject. This stays fixed across light/dark mode
# so the color-coding is a consistent visual language either way.
# ---------------------------------------------------------------------------
AGENT_META = {
    "QA": {"name": "Q&A Agent", "icon": "📘", "color": "#2E5A88", "fn": qa_agent.answer},
    "QUIZ": {"name": "Quiz Agent", "icon": "✏️", "color": "#C89B3C", "fn": quiz_agent.answer},
    "DEADLINE": {"name": "Deadline Agent", "icon": "⏰", "color": "#A63D40", "fn": deadline_agent.answer},
}
USER_AVATAR = "🧑‍🎓"

# ---------------------------------------------------------------------------
# Light / dark palettes. Same variable names in both, so the CSS template
# below never needs to branch on theme - just pick which dict to render it with.
# ---------------------------------------------------------------------------
LIGHT_PALETTE = {
    "bg": "#F4F6F8", "surface": "#FFFFFF", "sidebar": "#EBEEF2",
    "border": "#D6DCE3", "text": "#10151C", "muted": "#5B6472",
    "ink": "#10151C", "accent": "#0891B2", "glow": "8, 145, 178",
}
DARK_PALETTE = {
    "bg": "#090C12", "surface": "#10151F", "sidebar": "#0C1119",
    "border": "#1F2A38", "text": "#E7EDF3", "muted": "#7C8898",
    "ink": "#E7EDF3", "accent": "#34E6D0", "glow": "52, 230, 208",
}

st.session_state.setdefault("dark_mode", False)
p = DARK_PALETTE if st.session_state.dark_mode else LIGHT_PALETTE

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Space+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{ font-family: 'Space Grotesk', sans-serif; }}

/* Base app background + dotted grid */
.stApp {{
    background-color: {p['bg']};
    background-image: radial-gradient(rgba({p['glow']}, 0.35) 1.5px, transparent 1.5px);
    background-size: 24px 24px;
}}

/* Raw page canvas fallback (solid); the view container stays transparent
   so the dotted grid above shows through instead of being covered */
html, body {{
    background-color: {p['bg']};
}}
[data-testid="stAppViewContainer"] {{
    background-color: transparent !important;
}}

/* Top toolbar (Deploy button, menu) - blend into the page background */
[data-testid="stHeader"] {{
    background-color: {p['bg']} !important;
    box-shadow: none;
    border-bottom: none;
}}

/* Recolor the default decoration line to match the theme glow */
[data-testid="stDecoration"] {{
    background-image: linear-gradient(90deg, rgba({p['glow']}, 0.9), transparent);
}}

/* Sidebar expand/collapse arrow - force a visible icon color in both themes */
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stHeader"] svg,
[data-testid="baseButton-headerNoPadding"] svg {{
    color: {p['ink']} !important;
    fill: {p['ink']} !important;
}}
[data-testid="stSidebarCollapsedControl"] {{
    background-color: {p['surface']} !important;
    border: 1px solid {p['border']} !important;
    border-radius: 8px !important;
}}

/* Sticky footer bar behind the chat input - blend it into the main background */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] > div {{
    background-color: {p['bg']} !important;
    border-top: none;
    box-shadow: none;
}}

/* Hero header - HUD title bar, gently pulsing like a system that's "online" */
@keyframes pulseGlow {{
    0%, 100% {{ box-shadow: 0 1px 12px rgba({p['glow']}, 0.25); }}
    50% {{ box-shadow: 0 1px 18px rgba({p['glow']}, 0.55); }}
}}
.campus-hero {{
    padding: 1.5rem 1.25rem 1.1rem 1.25rem;
    border: 1px solid rgba({p['glow']}, 0.5);
    border-radius: 16px;
    background-color: {p['surface']};
    margin-bottom: 1.4rem;
    animation: pulseGlow 3.5s ease-in-out infinite;
}}
.campus-hero h1 {{
    font-family: 'Orbitron', sans-serif;
    font-weight: 800;
    font-size: 1.85rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {p['ink']};
    text-shadow: 0 0 14px rgba({p['glow']}, 0.55);
    margin: 0 0 0.25rem 0;
}}
.campus-hero p {{
    font-family: 'IBM Plex Mono', monospace;
    color: {p['muted']};
    font-size: 0.82rem;
    letter-spacing: 0.02em;
    margin: 0;
}}

/* Chat bubbles - console panels */
[data-testid="stChatMessage"] {{
    background-color: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin-bottom: 0.7rem;
    box-shadow: 0 0 0 1px rgba({p['glow']}, 0.08), 0 2px 10px rgba(0, 0, 0, 0.25);
}}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span {{
    color: {p['text']};
    font-family: 'Space Grotesk', sans-serif;
}}

/* Agent tab badge - LED status chip */
.agent-tab {{
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #FFFDF8;
    padding: 3px 10px;
    border-radius: 4px;
    margin-bottom: 0.55rem;
    box-shadow: 0 0 10px rgba({p['glow']}, 0.55);
}}

/* Sidebar - control panel */
[data-testid="stSidebar"] {{
    background-color: {p['sidebar']};
    border-right: 1px solid rgba({p['glow']}, 0.25);
}}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-size: 1rem;
    color: {p['ink']};
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {{
    font-family: 'IBM Plex Mono', monospace;
    color: {p['text']};
}}

/* Dark mode toggle - real data-testid is "stCheckbox" (confirmed via DevTools),
   not "stToggle" as previously guessed. */
[data-testid="stCheckbox"] {{
    background-color: {p['surface']} !important;
    border: 1.5px solid {p['border']} !important;
    border-radius: 999px !important;
    padding: 0.35rem 0.9rem !important;
    display: inline-flex !important;
    align-items: center !important;
    width: fit-content !important;
}}
[data-testid="stCheckbox"] label {{
    color: {p['text']} !important;
}}
/* The switch track - first div inside the label */
[data-testid="stCheckbox"] label > div:first-child {{
    border: 1.5px solid rgba({p['glow']}, 0.6) !important;
    border-radius: 999px !important;
    background-color: {p['bg']} !important;
}}
/* Track lights up when dark mode is on */
[data-testid="stCheckbox"] label:has(input[aria-checked="true"]) > div:first-child {{
    background-color: rgba({p['glow']}, 0.6) !important;
    border-color: rgba({p['glow']}, 0.9) !important;
}}

/* Chat input - command line, glows when focused */
[data-testid="stChatInput"] {{
    background-color: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}}
[data-testid="stChatInput"]:focus-within {{
    border-color: rgba({p['glow']}, 0.9);
    box-shadow: 0 0 16px rgba({p['glow']}, 0.4);
}}
[data-testid="stChatInput"] textarea {{
    color: {p['text']};
    background-color: {p['surface']};
    border: none;
    font-family: 'Space Grotesk', sans-serif;
}}

/* Empty-state info box */
.stAlert {{
    background-color: {p['surface']};
    border: 1px solid {p['border']};
    border-left: 3px solid rgba({p['glow']}, 0.8);
}}
.stAlert p, .stAlert li {{
    color: {p['text']};
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
}}

/* Buttons - ghost console buttons */
.stButton > button {{
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-size: 0.8rem;
    background-color: transparent;
    color: {p['ink']};
    border: 1px solid rgba({p['glow']}, 0.6);
    border-radius: 6px;
    padding: 0.45rem 1.1rem;
    transition: box-shadow 0.2s ease, background-color 0.2s ease;
}}
.stButton > button:hover {{
    background-color: rgba({p['glow']}, 0.12);
    box-shadow: 0 0 14px rgba({p['glow']}, 0.5);
    color: {p['ink']};
    border: 1px solid rgba({p['glow']}, 0.9);
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="campus-hero">
        <h1>🎓 Campus Copilot</h1>
        <p>Ask about your syllabus, handbook, or previous papers — or ask for a quiz or deadlines.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

memory = SessionMemory(st.session_state)


def render_agent_badge(label: str):
    meta = AGENT_META.get(label)
    if not meta:
        return
    st.markdown(
        f'<span class="agent-tab" style="background-color:{meta["color"]}">'
        f'{meta["icon"]} {meta["name"]}</span>',
        unsafe_allow_html=True,
    )


# --- render existing chat history ---
history = memory.get_recent_history(n=50)
if not history:
    st.info(
        "No messages yet — try one of these:\n\n"
        "- *\"What's the attendance policy in the handbook?\"* → Q&A Agent\n"
        "- *\"Quiz me on chapter 3\"* → Quiz Agent\n"
        "- *\"When is the assignment 2 submission due?\"* → Deadline Agent"
    )

for turn in history:
    if turn["role"] == "user":
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(turn["text"])
    else:
        label = turn.get("agent")
        avatar = AGENT_META.get(label, {}).get("icon", "🤖")
        with st.chat_message("assistant", avatar=avatar):
            render_agent_badge(label)
            st.markdown(turn["text"])

# --- handle new input ---
user_input = st.chat_input("Ask something...")
if user_input:
    memory.add_turn("user", user_input)
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_input)

    label = route(user_input)
    meta = AGENT_META[label]
    memory.set_last_agent(label)

    with st.chat_message("assistant", avatar=meta["icon"]):
        with st.spinner(f"Thinking..."):
            reply = meta["fn"](user_input, memory)
        render_agent_badge(label)
        st.markdown(reply)
    memory.add_turn("assistant", reply, agent=label)

# --- sidebar: session info + theme toggle ---
with st.sidebar:
    st.markdown("## 🗂️ Session")
    st.toggle("🌙 Dark mode", key="dark_mode")
    st.write(f"Turns so far: {len(memory.state['history'])}")

    last_label = memory.state.get("last_agent")
    if last_label:
        st.markdown("**Last agent used:**")
        render_agent_badge(last_label)

    st.markdown("---")
    if st.button("Clear session memory"):
        for key in ("history", "last_context", "last_agent", "known_deadlines"):
            st.session_state[key] = [] if key != "last_agent" else None
        st.rerun()