import os
import datetime
import json
from urllib import request, error

import streamlit as st

SYSTEM_PROMPT = "you are a ai friend, and your name is %s.your personality is %s. your answer should align with your personality and you can chat with user."

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "ai_friend_session")
MAX_SESSIONS = 50

DEFAULT_NAME = "陈兆睿"
DEFAULT_PERSONALITY = "tough"

def ask_local_llm(messages: list[dict]) -> str:
    url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": "qwen2.5:3b",
        "messages": messages,
        "stream": True
    }

    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with request.urlopen(req, timeout=300) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue

                part = json.loads(line)
                chunk = part.get("message", {}).get("content", "")
                if chunk:
                    yield chunk

                if part.get("done", False):
                    break
    except error.HTTPError as e:
        return f"HTTP Error: {e.code}"
    except Exception as e:
        return f"调用失败: {e}"


def new_session():
    return datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f")


def get_session_label(messages):
    for item in messages:
        if item.get("role") == "user":
            text = str(item.get("content", "")).strip()
            if text:
                return text[:18] + ("..." if len(text) > 18 else "")
    return "Empty chat"


def prune_sessions():
    session_items = []
    if os.path.exists(SESSIONS_DIR):
        for file_name in os.listdir(SESSIONS_DIR):
            if file_name.endswith(".json"):
                path = os.path.join(SESSIONS_DIR, file_name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    session_items.append({
                        "session_id": data.get("session_id", file_name[:-5]),
                        "updated_at": data.get("updated_at", "1970-01-01T00:00:00")
                    })
                except Exception:
                    continue

    if len(session_items) <= MAX_SESSIONS:
        return

    session_items = sorted(session_items, key=lambda x: x["updated_at"], reverse=True)
    for item in session_items[MAX_SESSIONS:]:
        dead_path = os.path.join(SESSIONS_DIR, f"{item['session_id']}.json")
        if os.path.exists(dead_path):
            os.remove(dead_path)


def save_session():
    session_id = st.session_state.get("session_id")
    if not session_id:
        return

    messages = st.session_state.get("messages", [])
    if not messages:
        return

    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "session_id": session_id,
                "name": st.session_state.get("name", DEFAULT_NAME),
            "personality": st.session_state.get("personality", DEFAULT_PERSONALITY),
            "messages": messages,
            "updated_at": datetime.datetime.now().isoformat(timespec="microseconds")
        }, f, ensure_ascii=False, indent=2)

    prune_sessions()


def load_sessions():
    session_list = []
    if os.path.exists(SESSIONS_DIR):
        for file_name in os.listdir(SESSIONS_DIR):
            if file_name.endswith(".json"):
                path = os.path.join(SESSIONS_DIR, file_name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    messages = data.get("messages", [])
                    if not messages:
                        continue

                    session_list.append({
                        "session_id": data.get("session_id", file_name[:-5]),
                        "updated_at": data.get("updated_at", "1970-01-01T00:00:00"),
                        "messages": messages,
                        "name": data.get("name", DEFAULT_NAME),
                        "personality": data.get("personality", DEFAULT_PERSONALITY)
                    })
                except Exception:
                    continue

    return sorted(session_list, key=lambda x: (x["updated_at"], x["session_id"]), reverse=True)


def load_session(session_id):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        st.session_state.messages = data.get("messages", [])
        st.session_state.session_id = data.get("session_id", session_id)
        st.session_state.name = data.get("name", DEFAULT_NAME)
        st.session_state.personality = data.get("personality", DEFAULT_PERSONALITY)

        st.session_state.profile_name = st.session_state.name
        st.session_state.profile_personality = st.session_state.personality
        st.session_state.show_welcome = False

        # 让当前打开会话更新时间最新，避免高亮项跑到看不见位置
        data["updated_at"] = datetime.datetime.now().isoformat(timespec="microseconds")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        st.error(f"加载会话失败: {e}")


def delete_session(session_id):
    try:
        path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)

        if st.session_state.session_id == session_id:
            st.session_state.messages = []
            st.session_state.session_id = new_session()
            st.session_state.name = DEFAULT_NAME
            st.session_state.personality = DEFAULT_PERSONALITY

            # 输入框清空
            st.session_state.profile_name = ""
            st.session_state.profile_personality = ""
            st.session_state.show_welcome = False
    except Exception as e:
        st.error(f"删除会话失败: {e}")


def save_profile():
    st.session_state.name = (st.session_state.get("profile_name") or DEFAULT_NAME).strip() or DEFAULT_NAME
    st.session_state.personality = (st.session_state.get("profile_personality") or DEFAULT_PERSONALITY).strip() or DEFAULT_PERSONALITY

    if st.session_state.messages:
        save_session()


st.set_page_config(
    page_title="Your AI Friend",
    page_icon="🤓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.streamlit.io/help",
        "Report a bug": "https://github.com/streamlit/streamlit/issues"
    }
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #0b1020 0%, #111827 100%);
        color: #e5e7eb;
    }

    .main .block-container {
        background: #0f172a;
        border-radius: 20px;
        padding: 1rem 1.2rem;
        border: 1px solid rgba(148,163,184,0.18);
    }

    [data-testid="stChatMessage"] {
        background: rgba(17,24,39,0.8);
        border: 1px solid rgba(148,163,184,0.15);
        border-radius: 18px;
        padding: 0.6rem 0.8rem;
        color: #e5e7eb;
    }

    [data-testid="stChatMessage"]:has(div[data-testid="chat-message-user"]) {
        background: rgba(59,130,246,0.12);
    }

    [data-testid="stChatMessage"]:has(div[data-testid="chat-message-assistant"]) {
        background: rgba(30,41,59,0.8);
    }

    .stChatInput {
        background: #111827 !important;
        color: white !important;
        border: 1px solid rgba(148,163,184,0.2) !important;
        border-radius: 16px;
    }

    [data-testid="stSidebar"] {
        background: #020817;
        color: white;
    }

    div.stButton > button {
        background: rgba(255,255,255,0.06);
        color: #e5e7eb;
        border: 1px solid rgba(148,163,184,0.2);
        border-radius: 12px;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: #ffffff;
        border: 1px solid #60a5fa;
        box-shadow: 0 0 0 1px rgba(96,165,250,0.45), 0 6px 16px rgba(37,99,235,0.35);
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

if "name" not in st.session_state:
    st.session_state.name = DEFAULT_NAME

if "personality" not in st.session_state:
    st.session_state.personality = DEFAULT_PERSONALITY

if "session_id" not in st.session_state:
    st.session_state.session_id = new_session()

if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

if "profile_name" not in st.session_state:
    st.session_state.profile_name = ""

if "profile_personality" not in st.session_state:
    st.session_state.profile_personality = ""

with st.sidebar:
    st.subheader("Control Panel")

    if st.button("New Chat", key="new_chat_button", width="stretch", icon="🤤"):
        if st.session_state.messages:
            save_session()

        st.session_state.messages = []
        st.session_state.session_id = new_session()
        st.session_state.name = DEFAULT_NAME
        st.session_state.personality = DEFAULT_PERSONALITY

        # 输入框为空但内部为默认值
        st.session_state.profile_name = ""
        st.session_state.profile_personality = ""
        st.session_state.show_welcome = False

    st.text("Recent Chats")

    recent_container = st.container(height=420)
    with recent_container:
        sessions = load_sessions()
        current_session_id = st.session_state.get("session_id")

        for item in sessions:
            session_id = item["session_id"]
            label = get_session_label(item.get("messages", []))
            is_active = (session_id == current_session_id)

            display_label = f"● {label}" if is_active else label

            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(
                    display_label,
                    key=f"load_{session_id}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True
                ):
                    if current_session_id != session_id:
                        save_session()
                        load_session(session_id)
                        st.rerun()

            with col2:
                if st.button("🗑️", key=f"delete_{session_id}", use_container_width=True):
                    delete_session(session_id)
                    st.rerun()

    st.subheader("AI Friend character")

    st.text_input(
        "nickname",
        key="profile_name",
        placeholder="Give your AI friend a nickname",
        on_change=save_profile
    )

    st.text_area(
        "personality",
        key="profile_personality",
        placeholder="Describe your AI friend's personality",
        on_change=save_profile
    )

st.title("Your AI Friend")
st.logo("image/神.png")

chat_container = st.container(height=650)

with chat_container:
    if st.session_state.show_welcome and not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown("Hello! I'm your AI friend. How can I assist you today?")
        st.session_state.show_welcome = False

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

prompt = st.chat_input("Enter your message here...")

if prompt:
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    save_session()

    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

        model_messages = [
            {"role": "system", "content": SYSTEM_PROMPT % (st.session_state.name, st.session_state.personality)}
        ] + st.session_state.messages

        with st.chat_message("assistant"):
            with st.status("AI 正在思考中...", expanded=True) as status:
                response = st.write_stream(ask_local_llm(model_messages))
                status.update(label="AI 已回答", state="complete")

    assistant_text = response if isinstance(response, str) else "".join(response)
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    save_session()