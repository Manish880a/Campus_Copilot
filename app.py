import uuid
import time
import streamlit as st

from memory import SessionMemory
from agents.router import route
from agents import qa_agent, quiz_agent, deadline_agent

st.set_page_config(page_title="Campus Copilot", page_icon="🎓", layout="wide")

# ---------------- AGENTS ----------------
AGENT_META = {
    "QA": {"name": "Q&A Agent", "icon": "📘", "color": "#2E5A88", "fn": qa_agent.answer},
    "QUIZ": {"name": "Quiz Agent", "icon": "✏️", "color": "#C89B3C", "fn": quiz_agent.answer},
    "DEADLINE": {"name": "Deadline Agent", "icon": "⏰", "color": "#A63D40", "fn": deadline_agent.answer},
}
USER_AVATAR = "🧑‍🎓"

# ---------------- STATE ----------------
st.session_state.setdefault("chats", {})
st.session_state.setdefault("chat_order", [])
st.session_state.setdefault("current_chat_id", None)

def new_chat():
    cid = str(uuid.uuid4())
    st.session_state["chats"][cid] = {
        "title": None,
        "history": [],
        "last_agent": None,
    }
    st.session_state["chat_order"].insert(0, cid)
    st.session_state["current_chat_id"] = cid

if not st.session_state["current_chat_id"]:
    new_chat()

memory = SessionMemory(st.session_state["chats"][st.session_state["current_chat_id"]])

# ---------------- STREAMING ----------------
def stream_text(text):
    placeholder = st.empty()
    out = ""
    for word in text.split():
        out += word + " "
        placeholder.markdown(out + "▌")
        time.sleep(0.015)
    placeholder.markdown(out)
    return out.strip()

# ---------------- CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Space+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* BASE */
html, body, .stApp {
    background: #090C12;
    background-image: radial-gradient(rgba(52,230,208,0.25) 1.5px, transparent 1.5px);
    background-size: 26px 26px;
    font-family: 'Space Grotesk', sans-serif;
    color: #E7EDF3;
}

/* REMOVE HEADER */
header[data-testid="stHeader"] {
    background: transparent;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #0C1119;
    border-right: 1px solid rgba(52,230,208,0.2);
}

/* SIDEBAR BUTTON STYLE (ChatGPT-like) */
.stButton > button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    padding: 10px 12px;
    border-radius: 10px;
    font-size: 14px;
    color: #E7EDF3;
    transition: 0.2s;
}

.stButton > button:hover {
    background: rgba(52,230,208,0.12);
}

/* ACTIVE CHAT */
.active-chat {
    background: rgba(52,230,208,0.18) !important;
    font-weight: 600 !important;
}

/* HERO */
.hero {
    border: 1px solid rgba(52,230,208,0.6);
    border-radius: 18px;
    padding: 24px;
    background: #10151F;
    box-shadow: 0 0 25px rgba(52,230,208,0.25);
    margin-bottom: 20px;
}
.hero h1 {
    font-family: 'Orbitron';
    text-shadow: 0 0 12px rgba(52,230,208,0.6);
}

/* CHAT */
[data-testid="stChatMessage"] {
    background: #10151F;
    border: 1px solid #1F2A38;
    border-radius: 12px;
    font-family: 'IBM Plex Mono';
}

/* INPUT */
[data-testid="stChatInput"] {
    background: #10151F;
    border: 1px solid #1F2A38;
}
[data-testid="stChatInput"]:focus-within {
    border-color: rgba(52,230,208,0.9);
    box-shadow: 0 0 12px rgba(52,230,208,0.5);
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="hero">
<h1>🎓 CAMPUS COPILOT</h1>
<p style="color:#7C8898;font-family:IBM Plex Mono;">Ask about syllabus, quizzes, deadlines</p>
</div>
""", unsafe_allow_html=True)

# ---------------- CHAT ----------------
history = memory.state["history"]

for msg in history:
    if msg["role"] == "user":
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(msg["text"])
    else:
        meta = AGENT_META[msg["agent"]]
        with st.chat_message("assistant", avatar=meta["icon"]):
            st.markdown(f"**{meta['icon']} {meta['name']}**")
            st.markdown(msg["text"])

# ---------------- INPUT ----------------
prompt = st.chat_input("Ask something...")

if prompt:
    if memory.state["title"] is None:
        memory.state["title"] = prompt[:40] + "..." if len(prompt) > 40 else prompt

    memory.add_turn("user", prompt)

    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    label = route(prompt)
    fn = AGENT_META[label]["fn"]

    with st.chat_message("assistant", avatar=AGENT_META[label]["icon"]):
        with st.spinner("Thinking..."):
            reply = fn(prompt, memory)

        streamed = stream_text(reply)

    memory.add_turn("assistant", streamed, agent=label, query=prompt)
    st.rerun()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("### 🧠 Chats")

    if st.button("➕ New Chat"):
        new_chat()
        st.rerun()

    for cid in st.session_state["chat_order"]:
        chat = st.session_state["chats"][cid]
        title = chat["title"] or "New Chat"
        active = cid == st.session_state["current_chat_id"]

        key = f"chat_{cid}"

        if st.button(f"💬 {title}", key=key):
            st.session_state["current_chat_id"] = cid
            st.rerun()