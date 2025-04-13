import streamlit as st
import os
from PIL import Image
from streamlit.components.v1 import html
import base64
import datetime
import markdown
from dotenv import load_dotenv
import hashlib

# Tải các biến môi trường từ file .env
load_dotenv()

# PHẢI đặt set_page_config trước bất kỳ lệnh streamlit nào khác
st.set_page_config(page_title="🤖 PhoGPT AI", page_icon="assets/logo.png", layout="centered")

# Đặt tên mặc định cho AI
DEFAULT_AI_NAME = "PhoGPT"

# Lấy API Key từ file .env
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ Không tìm thấy GOOGLE_API_KEY trong file .env.")
    st.stop()

# Cấu hình Gemini API
try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
except ModuleNotFoundError:
    st.error("⚠️ Thư viện 'google-generativeai' chưa được cài đặt. Hãy chạy: pip install google-generativeai")
    st.stop()
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

# Chức năng đăng nhập và đăng ký
def create_user_account(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    # Lưu thông tin tài khoản vào session_state
    st.session_state['user'] = {'username': username, 'password': hashed_password}
    st.success(f"Tạo tài khoản thành công cho {username}")

def login_user(username, password):
    if 'user' not in st.session_state:
        st.error("⚠️ Bạn chưa có tài khoản. Vui lòng đăng ký trước.")
        return False

    stored_password = st.session_state['user']['password']
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    if stored_password == hashed_password:
        st.session_state['logged_in'] = True
        st.success(f"Chào mừng trở lại, {username}!")
        return True
    else:
        st.error("⚠️ Sai tên đăng nhập hoặc mật khẩu.")
        return False

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Nếu chưa đăng nhập, yêu cầu đăng nhập
if not st.session_state['logged_in']:
    st.sidebar.header("Đăng nhập")
    username = st.sidebar.text_input("Tên đăng nhập")
    password = st.sidebar.text_input("Mật khẩu", type="password")
    
    login_button = st.sidebar.button("Đăng nhập")
    if login_button:
        if login_user(username, password):
            st.experimental_rerun()  # Làm mới trang để chuyển đến nội dung chính

    st.sidebar.header("Chưa có tài khoản?")
    register_username = st.sidebar.text_input("Tên đăng nhập (Đăng ký mới)")
    register_password = st.sidebar.text_input("Mật khẩu (Đăng ký mới)", type="password")
    register_button = st.sidebar.button("Đăng ký")

    if register_button:
        create_user_account(register_username, register_password)
        st.experimental_rerun()  # Làm mới trang để đăng ký mới thành công

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
avatar_ai = "https://scontent.fhph2-1.fna.fbcdn.net/v/t39.30808-6/490392190_678654707977227_1765116453897262223_n.jpg"

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
                    if word.startswith("http"):
                        st.image(word)
            else:
                st.write(reply)
        except Exception as e:
            st.error(f"❌ Lỗi khi gửi tin nhắn: {e}")