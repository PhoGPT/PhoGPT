import streamlit as st
import os
from dotenv import load_dotenv
from PIL import Image
import datetime

try:
    import google.generativeai as genai
except ModuleNotFoundError:
    st.error("⚠️ Chưa cài đặt 'google-generativeai'. Chạy: pip install google-generativeai")
    st.stop()

# Cấu hình trang
st.set_page_config(page_title="🤖 PhoGPT AI", page_icon="assets/logo.png", layout="centered")

# Load biến môi trường nếu cần
load_dotenv()

# Lấy API key từ secrets
try:
    api_key = st.secrets["google"]["GOOGLE_API_KEY"]
except Exception:
    st.error("⚠️ Không tìm thấy GOOGLE_API_KEY trong secrets.toml.")
    st.stop()

# Cấu hình Gemini
genai.configure(api_key=api_key)

MODEL_NAME = "models/gemini-1.5-pro-latest"

# Khởi tạo model chat
if "chat" not in st.session_state:
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        st.session_state.chat = model.start_chat()
    except Exception as e:
        st.error(f"❌ Không thể khởi tạo Gemini: {e}")
        st.stop()

# Sidebar
st.sidebar.title("⚙️ Cài đặt")
ai_name = "PhoGPT"  # Cố định tên trợ lý
selected_voice = st.sidebar.selectbox("🔊 Chọn giọng", ["Nữ chuẩn", "Nam trầm", "Trẻ trung"])

# Logo & tiêu đề
st.image("assets/logo.png", width=120)
st.title(f"🤖 {ai_name}")
st.caption("🧠 Trợ lý AI thông minh từ Gemini")

# Nút reset
if st.sidebar.button("🧹 Xóa hội thoại"):
    st.session_state.history = []

# Lịch sử hội thoại
if "history" not in st.session_state:
    st.session_state.history = []

# Giao diện chat
avatar_user = "https://i.imgur.com/7q6cP1B.png"
avatar_ai = "https://i.imgur.com/N5uCbDu.png"

for role, msg in st.session_state.history:
    with st.container():
        st.markdown(f"""
            <div style='background-color:#f0f2f6; padding:1rem; border-radius:1rem; margin-bottom:0.5rem; display:flex; align-items:start; gap:1rem;'>
                <img src="{avatar_user if role=='user' else avatar_ai}" width="40" style="border-radius:50%;">
                <div>{msg}</div>
            </div>
        """, unsafe_allow_html=True)

# Nhập & gửi tin nhắn
user_input = st.chat_input(f"Nhập câu hỏi cho {ai_name}...")

if user_input:
    st.session_state.history.append(("user", user_input))
    with st.spinner("🔄 Đang phản hồi..."):
        try:
            response = st.session_state.chat.send_message(user_input)
            reply = response.text
            st.session_state.history.append(("assistant", reply))

            # Nếu có hình ảnh
            for word in reply.split():
                if word.startswith("http") and any(ext in word for ext in [".jpg", ".png", ".jpeg"]):
                    st.image(word, caption="Ảnh liên quan", use_column_width=True)
        except Exception as e:
            error_msg = f"❌ Lỗi: {e}"
            st.session_state.history.append(("assistant", error_msg))
            st.error(error_msg)