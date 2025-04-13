import streamlit as st
import os
from dotenv import load_dotenv  # Thư viện để tải các biến môi trường từ file .env
from PIL import Image
import datetime

# Load biến môi trường từ file .env
load_dotenv()  # Đảm bảo các biến môi trường từ file .env được tải

# Đọc API key từ biến môi trường
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ Không tìm thấy GOOGLE_API_KEY trong file .env. Vui lòng kiểm tra lại.")
    st.stop()

# Cài đặt Google API
try:
    import google.generativeai as genai
except ModuleNotFoundError:
    st.error("⚠️ Thư viện 'google-generativeai' chưa được cài đặt. Hãy chạy: pip install google-generativeai")
    st.stop()

# PHẢI đặt set_page_config trước bất kỳ lệnh streamlit nào khác
st.set_page_config(page_title="🤖 PhoGPT AI", page_icon="assets/logo.png", layout="centered")

# Đặt tên mặc định cho AI
DEFAULT_AI_NAME = "PhoGPT"

# Cấu hình Gemini API
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ Lỗi cấu hình API: {e}")
    st.stop()

# Chọn mô hình Gemini ổn định
MODEL_NAME = "models/gemini-1.5-pro-latest"

# Khởi tạo model chat
if "chat" not in st.session_state:
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        st.session_state.chat = model.start_chat()
    except Exception as e:
        st.error(f"❌ Không thể khởi tạo mô hình GPT: {e}")
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
st.caption(f"🧠 Trò chuyện cùng {ai_name}, trợ lý AI thông minh từ NguyenVu")

# Nút xóa hội thoại
if st.sidebar.button("🧹 Xóa hội thoại"):
    st.session_state.history = []

# Khởi tạo history nếu chưa có
if "history" not in st.session_state:
    st.session_state.history = []

# Hiển thị lịch sử hội thoại
avatar_user = "https://i.pinimg.com/236x/5e/e0/82/5ee082781b8c41406a2a50a0f32d6aa6.jpg"
avatar_ai = "https://scontent.fhph2-1.fna.fbcdn.net/v/t39.30808-6/490392190_678654707977227_1765116453897262223_n.jpg?_nc_cat=109&ccb=1-7&_nc_sid=127cfc&_nc_ohc=llepRsrx304Q7kNvwGTUEHC&_nc_oc=AdlQWumfAI8cp0RzFwaHFOkm2IDY8d8mIbOzmQ0Ufp3gT7dVJ-15ytX03w0x1n-nOWzYl_gchD0SB5djyvj32P6e&_nc_zt=23&_nc_ht=scontent.fhph2-1.fna&_nc_gid=oWRsYsffWetuNZ-BZDxjGw&oh=00_AfEtc4wygalKzz8d9-lT7IyE3HIx1TLzhZXg-upq8NwjVA&oe=68012025"

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