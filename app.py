import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
from streamlit.components.v1 import html

# Load Google API Key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", st.secrets.get("GOOGLE_API_KEY", "")))

# Set page config (phải đặt đầu tiên)
st.set_page_config(page_title="🤖 PhoGPT AI", page_icon="🤖", layout="centered")

# Chọn mô hình Gemini
MODEL_NAME = "models/gemini-2.5-pro-exp-03-25"

# Khởi tạo model chat
if "chat" not in st.session_state:
    model = genai.GenerativeModel(MODEL_NAME)
    st.session_state.chat = model.start_chat()

# Tùy chỉnh AI name
st.sidebar.title("⚙️ Cài đặt")
ai_name = st.sidebar.text_input("Tên trợ lý AI", value=st.session_state.get("ai_name", "PhoGPT"))
st.session_state.ai_name = ai_name

# Giao diện chính
st.markdown("""
    <style>
    .main {
        background: linear-gradient(120deg, #f0f2f6, #ffffff);
        font-family: 'Segoe UI', sans-serif;
    }
    .chat-box {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 1.5rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .user-msg {
        color: #1a73e8;
        font-weight: bold;
    }
    .assistant-msg {
        color: #4b4b4b;
    }
    </style>
""", unsafe_allow_html=True)

st.title(f"🤖 {ai_name}")
st.caption(f"🧠 Trò chuyện cùng {ai_name}, trợ lý AI thông minh từ Gemini")

# Reset hội thoại
if st.sidebar.button("🧹 Xóa hội thoại"):
    st.session_state.history = []

# Khởi tạo history nếu chưa có
if "history" not in st.session_state:
    st.session_state.history = []

# Hiển thị lịch sử hội thoại
for role, msg in st.session_state.history:
    with st.container():
        role_class = "user-msg" if role == "user" else "assistant-msg"
        st.markdown(f'<div class="chat-box {role_class}">{msg}</div>', unsafe_allow_html=True)

# Gửi tin nhắn
user_input = st.chat_input(f"Nhập câu hỏi cho {ai_name}...")

if user_input:
    st.session_state.history.append(("user", user_input))
    with st.spinner("🔄 {ai_name} đang phản hồi..."):
        try:
            response = st.session_state.chat.send_message(user_input)
            reply = response.text
            st.session_state.history.append(("assistant", reply))

            # Hiển thị nếu có ảnh trong phản hồi
            if any(ext in reply for ext in [".jpg", ".png", ".jpeg"]):
                for word in reply.split():
                    if word.startswith("http") and any(ext in word for ext in [".jpg", ".png", ".jpeg"]):
                        st.image(word, caption="Hình ảnh liên quan", use_column_width=True)

        except Exception as e:
            error_msg = f"❌ Lỗi: {e}"
            st.error(error_msg)
            st.session_state.history.append(("assistant", error_msg))
