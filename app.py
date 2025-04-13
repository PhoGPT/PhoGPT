# NOTE: This code assumes a Streamlit environment where streamlit is installed
# Ensure you install required packages: streamlit, python-dotenv, google-generativeai, pillow

import streamlit as st
import os
from PIL import Image
from streamlit.components.v1 import html
import base64
import datetime

try:
    import google.generativeai as genai
except ModuleNotFoundError:
    st.error("⚠️ Thư viện 'google-generativeai' chưa được cài đặt. Hãy chạy: pip install google-generativeai")
    st.stop()

# PHẢI đặt set_page_config trước bất kỳ lệnh streamlit nào khác
st.set_page_config(page_title="🤖 PhoGPT AI", page_icon="assets/logo.png", layout="centered")

# Đặt tên mặc định cho AI
DEFAULT_AI_NAME = "PhoGPT"

# Load Google API Key từ secrets.toml
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except KeyError:
    st.error("⚠️ Không tìm thấy GOOGLE_API_KEY trong secrets.toml.")
    st.stop()

# Cấu hình Gemini API
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ Lỗi cấu hình API: {e}")
    st.stop()

# Chọn mô hình Gemini ổn định
MODEL_NAME = "models/gemini-pro"

# Khởi tạo model chat
if "chat" not in st.session_state:
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        st.session_state.chat = model.start_chat()
    except Exception as e:
        st.error(f"❌ Không thể khởi tạo mô hình Gemini: {e}")
        st.stop()

# Sidebar cài đặt
st.sidebar.title("⚙️ Cài đặt")
ai_name = DEFAULT_AI_NAME

# Toggle cho dark mode
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark_mode = st.sidebar.toggle("🌙 Chế độ tối", value=st.session_state.dark_mode)
st.session_state.dark_mode = dark_mode

# CSS tùy chỉnh giao diện + hiệu ứng
hour = datetime.datetime.now().hour
if dark_mode:
    bg_color = "linear-gradient(135deg, #2c2c2c, #3a3a3a)"
else:
    bg_color = "linear-gradient(135deg, #f5f7fa, #c3cfe2)"

background_style = f"""
    <style>
    .main {{
        background: {bg_color};
        font-family: 'Segoe UI', sans-serif;
        transition: background 1s ease-in-out;
        animation: bgFade 20s ease-in-out infinite alternate;
    }}
    .chat-box {{
        background-color: #ffffffcc;
        padding: 1.5rem;
        border-radius: 1.5rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        backdrop-filter: blur(8px);
        transform: translateY(10px);
        opacity: 0;
        animation: fadeIn 0.6s ease-in-out forwards;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }}
    .avatar {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
    }}
    @keyframes fadeIn {{
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .typing {{
        display: inline-block;
        overflow: hidden;
        border-right: .15em solid orange;
        white-space: nowrap;
        animation: typing 3s steps(40, end), blink .75s step-end infinite;
    }}
    @keyframes typing {{
        from {{ width: 0 }}
        to {{ width: 100% }}
    }}
    @keyframes blink {{
        from, to {{ border-color: transparent }}
        50% {{ border-color: orange }}
    }}
    </style>
"""

st.markdown(background_style, unsafe_allow_html=True)

# Tiêu đề chính
st.title(f"🤖 {ai_name}")
st.caption(f"🧠 Trò chuyện cùng {ai_name}, trợ lý AI thông minh từ Gemini")

# Nút xóa hội thoại
if st.sidebar.button("🧹 Xóa hội thoại"):
    st.session_state.history = []

# Khởi tạo history nếu chưa có
if "history" not in st.session_state:
    st.session_state.history = []

# Hiển thị lịch sử hội thoại
avatar_user = "https://i.imgur.com/7q6cP1B.png"
avatar_ai = "https://i.imgur.com/N5uCbDu.png"

for role, msg in st.session_state.history:
    avatar = avatar_user if role == "user" else avatar_ai
    role_class = "user-msg" if role == "user" else "assistant-msg"
    typing_class = "typing" if role == "assistant" else ""
    with st.container():
        st.markdown(f'''
            <div class="chat-box {role_class}">
                <img class="avatar" src="{avatar}" alt="avatar" />
                <div class="{typing_class}">{msg}</div>
            </div>
        ''', unsafe_allow_html=True)

# Nhập tin nhắn người dùng
user_input = st.chat_input(f"Nhập câu hỏi cho {ai_name}...")

if user_input:
    st.session_state.history.append(("user", user_input))
    with st.spinner(f"🔄 {ai_name} đang phản hồi..."):
        try:
            response = st.session_state.chat.send_message(user_input)
            reply = response.text
            st.session_state.history.append(("assistant", reply))

            if any(ext in reply for ext in [".jpg", ".png", ".jpeg"]):
                for word in reply.split():
                    if word.startswith("http") and any(ext in word for ext in [".jpg", ".png", ".jpeg"]):
                        st.image(word, caption="Hình ảnh liên quan", use_column_width=True)

        except Exception as e:
            error_msg = f"❌ Lỗi: {e}"
            st.error(error_msg)
            st.session_state.history.append(("assistant", error_msg))
