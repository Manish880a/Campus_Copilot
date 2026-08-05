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
    4. Reply + label + originating query are stored in the active chat's
       memory and shown in the chat

Chats: the sidebar supports multiple chat threads (like a normal chat
app). Each thread has its own independent memory. "New Chat" starts a
fresh thread; clicking a past thread in the list switches to it.
"""
import json
import uuid

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

# ---------------------------------------------------------------------------
# Multi-chat state: a dict of chat_id -> chat state dict, plus an ordered
# list of chat_ids (newest first) for the sidebar list.
# ---------------------------------------------------------------------------
st.session_state.setdefault("chats", {})
st.session_state.setdefault("chat_order", [])
st.session_state.setdefault("current_chat_id", None)


def _create_chat() -> str:
    cid = str(uuid.uuid4())
    st.session_state["chats"][cid] = {
        "title": None,
        "history": [],
        "last_context": [],
        "last_agent": None,
        "known_deadlines": [],
    }
    st.session_state["chat_order"].insert(0, cid)
    st.session_state["current_chat_id"] = cid
    return cid


if (
    not st.session_state["current_chat_id"]
    or st.session_state["current_chat_id"] not in st.session_state["chats"]
):
    _create_chat()

current_chat_id = st.session_state["current_chat_id"]
memory = SessionMemory(st.session_state["chats"][current_chat_id])

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

/* Sidebar collapse/expand icon - actual Streamlit collapse button structure */
[data-testid="stSidebarCollapseButton"] button {{
    background-color: {p['surface']} !important;
    border: 1px solid {p['border']} !important;
    border-radius: 8px !important;
    color: transparent !important;
    font-size: 0 !important;
    width: 2.4rem !important;
    height: 2.4rem !important;
    padding: 0 !important;
    position: relative !important;
}}
[data-testid="stSidebarCollapseButton"] button::before {{
    content: "<";
    position: absolute !important;
    inset: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: {p['ink']} !important;
    font-size: 1rem !important;
    text-indent: 0 !important;
}}
[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarCollapseButton"] button::before {{
    content: ">";
}}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
[data-testid="stSidebarCollapseButton"] button > span {{
    display: none !important;
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

/* Copy / regenerate action row under each assistant message - icon-only,
   compact square buttons */
.msg-copy-btn {{
    font-size: 0.95rem;
    line-height: 1;
    background-color: transparent;
    color: {p['ink']};
    border: 1px solid rgba({p['glow']}, 0.6);
    border-radius: 6px;
    width: 2.1rem;
    height: 2.1rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: box-shadow 0.2s ease, background-color 0.2s ease;
    margin-top: 0.35rem;
}}
.msg-copy-btn:hover {{
    background-color: rgba({p['glow']}, 0.12);
    box-shadow: 0 0 14px rgba({p['glow']}, 0.5);
    border: 1px solid rgba({p['glow']}, 0.9);
}}
/* Regenerate is a real st.button - match the same compact icon-only size */
[class*="st-key-msg_actions"] .stButton > button {{
    width: 2.1rem;
    height: 2.1rem;
    padding: 0 !important;
    font-size: 0.95rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
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

/* Chat input - command line, glows when focused */
[data-testid="stChatInput"] {{
    background-color: transparent !important;
    border: none !important;
    border-radius: 8px;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div,
[data-testid="stChatInput"] > div > div > div,
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] div[role="textbox"] {{
    background-color: {p['surface']} !important;
    color: {p['text']} !important;
    border-radius: 8px !important;
}}
[data-testid="stChatInput"] > div {{
    border: 1px solid {p['border']} !important;
}}
[data-testid="stChatInput"]:focus-within > div {{
    border-color: rgba({p['glow']}, 0.9) !important;
    box-shadow: 0 0 16px rgba({p['glow']}, 0.4) !important;
}}
[data-testid="stChatInput"] textarea {{
    background-color: transparent !important;
    border: none !important;
    font-family: 'Space Grotesk', sans-serif;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: {p['muted']} !important;
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

/* Sidebar nav list (New Chat + Chat History) - flat rows, no borders,
   icon + text, soft highlight on hover, persistent highlight for the
   active chat (rendered as a "primary" button). */
[class*="st-key-sidebar_nav"] .stButton > button {{
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 0.55rem 0.7rem !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    font-size: 0.88rem !important;
    font-weight: 400 !important;
}}
[class*="st-key-sidebar_nav"] .stButton > button:hover {{
    background-color: rgba({p['glow']}, 0.14) !important;
    box-shadow: none !important;
    border: none !important;
}}
[class*="st-key-sidebar_nav"] .stButton > button[kind="primary"] {{
    background-color: rgba({p['glow']}, 0.18) !important;
    font-weight: 600 !important;
    color: {p['ink']} !important;
}}

/* Buttons - ghost console buttons (theme toggle, regenerate) */
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


def render_agent_badge(label: str):
    meta = AGENT_META.get(label)
    if not meta:
        return
    st.markdown(
        f'<span class="agent-tab" style="background-color:{meta["color"]}">'
        f'{meta["icon"]} {meta["name"]}</span>',
        unsafe_allow_html=True,
    )


def render_message_actions(turn: dict, idx: int, chat_id: str):
    """Copy + Regenerate row under an assistant message."""
    text = turn["text"]
    query = turn.get("query")
    label = turn.get("agent")

    safe_text = json.dumps(text)  # safe JS string literal (escaped quotes/newlines)
    with st.container(key=f"msg_actions_{chat_id}_{idx}"):
        col1, col2, _spacer = st.columns([0.6, 0.6, 8])
        with col1:
            st.markdown(
                f"<button class='msg-copy-btn' title='Copy' "
                f"onclick='navigator.clipboard.writeText({safe_text})'>📋</button>",
                unsafe_allow_html=True,
            )
        with col2:
            if query and label and st.button("🔄", key=f"regen_{chat_id}_{idx}", help="Regenerate"):
                fn = AGENT_META[label]["fn"]
                history_list = memory.state["history"]
                del history_list[idx]  # remove so the agent doesn't see its own old answer
                new_reply = fn(query, memory)
                history_list.insert(
                    idx,
                    {"role": "assistant", "text": new_reply, "agent": label, "query": query},
                )
                memory.set_last_agent(label)
                st.rerun()


# --- render chat history for the active chat ---
history = memory.state["history"]
if not history:
    st.info(
        "No messages yet — try one of these:\n\n"
        "- *\"What's the attendance policy in the handbook?\"* → Q&A Agent\n"
        "- *\"Quiz me on chapter 3\"* → Quiz Agent\n"
        "- *\"When is the assignment 2 submission due?\"* → Deadline Agent"
    )

for idx, turn in enumerate(history):
    if turn["role"] == "user":
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(turn["text"])
    else:
        label = turn.get("agent")
        avatar = AGENT_META.get(label, {}).get("icon", "🤖")
        with st.chat_message("assistant", avatar=avatar):
            render_agent_badge(label)
            st.markdown(turn["text"])
            render_message_actions(turn, idx, current_chat_id)

# --- handle new input ---
user_input = st.chat_input("Ask something...")
if user_input:
    if memory.state.get("title") is None:
        memory.state["title"] = (user_input[:40] + "…") if len(user_input) > 40 else user_input

    memory.add_turn("user", user_input)

    label = route(user_input)
    meta = AGENT_META[label]
    memory.set_last_agent(label)

    with st.spinner("Thinking..."):
        reply = meta["fn"](user_input, memory)

    memory.add_turn("assistant", reply, agent=label, query=user_input)
    st.rerun()

# --- sidebar: theme, session info, and multi-chat history ---
with st.sidebar:
    st.markdown("## 🗂️ Session")

    dark_label = "☀️ Light Mode" if st.session_state.dark_mode else "🌙 Dark Mode"
    if st.button(dark_label, key="theme_toggle_btn", use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.write(f"Turns so far: {len(history)}")

    last_label = memory.state.get("last_agent")
    if last_label:
        st.markdown("**Last agent used:**")
        render_agent_badge(last_label)

    st.markdown("---")

    with st.container(key="sidebar_nav"):
        if st.button("➕  New Chat", key="new_chat_btn", use_container_width=True):
            _create_chat()
            st.rerun()

        st.markdown("### 💬 Chat History")
        for cid in st.session_state["chat_order"]:
            chat = st.session_state["chats"][cid]
            title = chat["title"] or "New chat"
            is_current = cid == current_chat_id
            if st.button(
                f"💬  {title}",
                key=f"switch_{cid}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                st.session_state["current_chat_id"] = cid
                st.rerun()