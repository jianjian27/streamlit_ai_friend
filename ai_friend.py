import os

import streamlit as st
import datetime
import json
from urllib import request,error

SYSTEM_PROMPT = "you are a ai friend, and your name is %s.your personality is %s. your answer should align with your personality and you can chat with user."

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "ai_friend_session")

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
        with request.urlopen(req,timeout=300) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue

                part = json.loads(line) # Ollama API返回的每一行都是一个JSON对象
                chunk = part.get("message", {}).get("content", "")
                if chunk:
                    yield chunk

                if part.get("done" , False):
                    break
    except error.HTTPError as e:
            return f"HTTP Error: {e.code}"
    except Exception as e:
        return f"调用失败: {e}"


# 保存会话信息函数
def save_session():
    session_id = st.session_state.get("session_id")
    if not session_id:
        return  # 如果没有会话ID，则不保存
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "session_id": session_id,
            "name": st.session_state.get("name", ""),
            "personality": st.session_state.get("personality", ""),
            "messages": st.session_state.get("messages", [])
        }, f, ensure_ascii=False, indent=2)


# 新建会话函数
def new_session():
    return datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f")


# 加载会话列表函数
def load_sessions():
    session_list = []
    # 遍历会话文件夹中的所有JSON文件
    if os.path.exists(SESSIONS_DIR):
        file_list = os.listdir(SESSIONS_DIR)
        for file_name in file_list:
            if file_name.endswith(".json"):
                session_list.append(file_name[:-5])  # 去掉文件扩展名
    return session_list


# 加载会话函数
def load_session(session_id):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        st.session_state.messages = data.get("messages", [])
        st.session_state.session_id = data.get("session_id", session_id)
        st.session_state.name = data.get("name", "陈兆睿")
        st.session_state.personality = data.get("personality", "blue but tough")
    except Exception as e:
        st.error(f"加载会话失败: {e}")


# 删除会话函数
def delete_session(session_id):
    try:
        if os.path.exists(f"./ai_friend_session/{session_id}.json"):
            os.remove(f"./ai_friend_session/{session_id}.json")
            # 如果删除的是当前会话，则清空聊天记录
            if st.session_state.session_id == session_id:
                st.session_state.messages = []
                st.session_state.session_id = new_session()
                st.rerun()
    except Exception as e:
        st.error(f"删除会话失败: {e}")


# 设置页面的配置项
st.set_page_config(
    page_title="Your AI Friend",
    page_icon="🤓",
    layout="wide",

    # 设置初始侧边栏状态
    initial_sidebar_state="expanded",

    menu_items={
        'Get Help': 'https://www.streamlit.io/help',
        'Report a bug': "https://github.com/streamlit/streamlit/issues"
    }
)


# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 初始化AI朋友的昵称和性格
if "name" not in st.session_state:
    st.session_state.name = "陈兆睿"

if "personality" not in st.session_state:
    st.session_state.personality = "blue but tough"

# 会话标识
if "session_id" not in st.session_state:
    st.session_state.session_id = new_session()

# 左侧边栏
with st.sidebar:
    st.subheader("Control Panel")

    # 新建会话
    if st.button("New Chat", width="stretch", icon = "🤤" ):
        # 只有真正有聊天内容的会话，才先保存
        if st.session_state.messages:
            save_session()

        # 无论是否有消息，都会换新对话
        st.session_state.messages = []
        st.session_state.session_id = new_session()
        st.rerun()

    # 加载会话
    st.text("Recent Chats")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4,1])
        with col1:
            if st.button(session, width = "stretch", icon = "🗣️", key=f"load_{session}", type = "primary" if session == st.session_state.session_id else "secondary"):
                save_session()  # 切换前保存当前会话
                load_session(session)
                st.rerun()

        with col2:
            if st.button("", icon = "🗑️", key=f"delete_{session}"):
                delete_session(session)




    st.subheader("AI Friend character")
    # 设置AI朋友的昵称
    name = st.text_input("nickname", placeholder="Give your AI friend a nickname")
    if name:
        st.session_state.name = name
    # 设置AI朋友的性格
    personality = st.text_area("personality", placeholder="Give your AI friend a personality")
    if personality:
        st.session_state.personality = personality

# 大标题
st.title("Your AI Friend")

# logo
st.logo("image/神.png")

st.text("会话名称: " + st.session_state.session_id)
# 显示欢迎消息
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("Hello! I'm your AI friend. How can I assist you today?")

# 显示聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 聊天输入框
prompt = st.chat_input("Enter your message here...")

if prompt: # 字符串会被自动转换为布尔值，非空字符串为True，空字符串为False
    # 1) 保存用户消息
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    save_session()# 用户一发送就保存

    with st.chat_message("user"):
        st.markdown(prompt)

    # 2) 把历史消息一起发给模型
    model_messages = [{"role": "system", "content": SYSTEM_PROMPT % (st.session_state.name, st.session_state.personality)}] + st.session_state.messages

    with st.chat_message("assistant"):
        response = st.write_stream(ask_local_llm(model_messages))

    # 3) 保存模型回复
    if isinstance(response, str):
        assistant_text = response
    else:
        assistant_text = "".join(response)

    assistant_msg = {"role": "assistant", "content": assistant_text}
    st.session_state.messages.append(assistant_msg)
    save_session()
