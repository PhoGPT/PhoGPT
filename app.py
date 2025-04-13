import streamlit as st
import os
from PIL import Image
from streamlit.components.v1 import html
import base64
import datetime
import markdown

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
MODEL_NAME = "models/gemini-1.5-pro"

# Sidebar cài đặt
st.sidebar.title("⚙️ Cài đặt")
ai_name = DEFAULT_AI_NAME

# Toggle cho dark mode
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark_mode = st.sidebar.toggle("🌙 Chế độ tối", value=st.session_state.dark_mode)
st.session_state.dark_mode = dark_mode

# Danh mục đoạn chat
st.sidebar.markdown("---")
st.sidebar.subheader("🗂️ Danh mục đoạn chat")
if "chat_logs" not in st.session_state:
    st.session_state.chat_logs = []

for i, (ts, preview) in enumerate(st.session_state.chat_logs):
    if st.sidebar.button(f"📌 {ts}", key=f"chat_{i}"):
        st.session_state.history = preview
        model = genai.GenerativeModel(MODEL_NAME)
        st.session_state.chat = model.start_chat(history=preview)

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
        word-break: break-word;
        white-space: pre-wrap;
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
    </style>
"""

st.markdown(background_style, unsafe_allow_html=True)

# Tiêu đề chính
st.title(f"🤖 {ai_name}")
st.caption(f"🧠 Trò chuyện cùng {ai_name}, trợ lý AI thông minh từ Gemini")

# Kiểm tra nếu người dùng đã đăng nhập
if 'user_logged_in' not in st.session_state:
    st.session_state['user_logged_in'] = False

# Nếu chưa đăng nhập, yêu cầu nhập tên người dùng
if not st.session_state['user_logged_in']:
    st.text_input("Vui lòng nhập tên của bạn:", key="username_input")
    if st.button("Đăng nhập"):
        if st.session_state.get("username_input"):
            st.session_state['user_logged_in'] = True
            st.session_state['username'] = st.session_state.get("username_input")
            st.experimental_rerun()  # Làm mới trang sau khi đăng nhập thành công

# Nếu đã đăng nhập, hiển thị nội dung
if st.session_state['user_logged_in']:
    # Hiển thị tên người dùng
    st.markdown(f"**Xin chào, {st.session_state['username']}!**")

    # Nút xóa hội thoại
    if st.sidebar.button("🧹 Xóa hội thoại"):
        st.session_state.history = []

    # Nút bắt đầu chat mới
    if st.sidebar.button("💬 Đoạn chat mới"):
        if st.session_state.get("history"):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            st.session_state.chat_logs.insert(0, (timestamp, st.session_state.history.copy()))
        st.session_state.history = []
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            st.session_state.chat = model.start_chat()
        except Exception as e:
            st.error(f"❌ Không thể khởi tạo mô hình mới: {e}")

    # Nút tải đoạn chat
    if st.sidebar.button("📥 Tải đoạn chat"):
        if st.session_state.get("history"):
            filename = f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            content = "\n".join([f"{r.upper()}: {m}" for r, m in st.session_state.history])
            b64 = base64.b64encode(content.encode()).decode()
            href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">📄 Tải xuống {filename}</a>'
            st.sidebar.markdown(href, unsafe_allow_html=True)

    # Khởi tạo model chat
    if "chat" not in st.session_state:
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            st.session_state.chat = model.start_chat()
        except Exception as e:
            st.error(f"❌ Không thể khởi tạo mô hình Gemini: {e}")
            st.stop()

    # Khởi tạo history nếu chưa có
    if "history" not in st.session_state:
        st.session_state.history = []

    # Hiển thị lịch sử hội thoại
    avatar_user = "https://i.pinimg.com/236x/5e/e0/82/5ee082781b8c41406a2a50a0f32d6aa6.jpg"
    avatar_ai = "https://scontent.fhph2-1.fna.fbcdn.net/v/t39.30808-6/490392190_678654707977227_1765116453897262223_n.jpg?_nc_cat=109&ccb=1-7&_nc_sid=127cfc&_nc_ohc=llepRsrx304Q7kNvwGTUEHC&_nc_oc=AdlQWumfAI8cp0RzFwaHFOkm2IDY8d8mIbOzmQ0Ufp3gT7dVJ-15ytX03w0x1n-nOWzYl_gchD0SB5djyvj32P6e&_nc_zt=23&_nc_ht=scontent.fhph2-1.fna&_nc_gid=oWRsYsffWetuNZ-BZDxjGw&oh=00_AfEtc4wygalKzz8d9-lT7IyE3HIx1TLzhZXg-upq8NwjVA&oe=68012025"

    for role, msg in st.session_state.history:
        avatar = avatar_user if role == "user" else avatar_ai
        with st.container():
            msg_html = markdown.markdown(msg)
            st.markdown(f'''
                <div class="chat-box">
                    <img class="avatar" src="{avatar}" alt="avatar" />
                    <div>{msg_html}</div>
                </div>
            ''', unsafe_allow_html=True)

    # Nhập tin nhắn người dùng
    user_input = st.chat_input(f"Nhập câu hỏi cho {ai_name}...")

    if user_input:
        st.session_state.history.append(("user", user_input))
        with st.spinner(f"🔄 {ai_name} đang phản hồi..."):
            try:
                response = st.session_state.chat.send_message(user_input)
                reply = response.text.strip().rstrip("|")
                st.session_state.history.append(("assistant", reply))

                if any(ext in reply for ext in [".jpg", ".png", ".jpeg"]):
                    for word in reply.split():
                        if word.startswith("http") and any(ext in word for ext in [".jpg", ".png", ".jpeg"]):
                            st.image(word, caption="Hình ảnh liên quan", use_column_width=True)

            except Exception as e:
                error_msg = f"❌ Lỗi: {e}"
                st.error(error_msg)
                st.session_state.history.append(("assistant", error_msg))