import streamlit as st
import os
from dotenv import load_dotenv
from PIL import Image
import datetime
import google.generativeai as genai

# PHẢI đặt set_page_config trước bất kỳ lệnh streamlit nào khác
st.set_page_config(
    page_title="🤖 PhoGPT AI", 
    page_icon="assets/logo.png",  # Đặt logo từ thư mục assets
    layout="centered"
)

# Đặt tên mặc định cho AI
DEFAULT_AI_NAME = "PhoGPT"

# Lấy API key từ secrets.toml
try:
    api_key = st.secrets["google"]["GOOGLE_API_KEY"]
except KeyError:
    st.error("⚠️ Không tìm thấy GOOGLE_API_KEY trong secrets.toml.")
    st.stop()

# Cấu hình mô hình Google AI
genai.configure(api_key=api_key)

# Chọn mô hình Gemini (mặc định là mô hình mới nhất có hỗ trợ generateContent)
MODEL_NAME = "models/gemini-2.5-pro-exp-03-25"  # Kiểm tra lại tên mô hình

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
ai_name = st.sidebar.text_input("Tên trợ lý AI", value=st.session_state.get("ai_name", DEFAULT_AI_NAME))
dark_mode = st.sidebar.checkbox("🌙 Dark mode")
selected_voice = st.sidebar.selectbox("🔊 Chọn giọng phản hồi", ["Nữ chuẩn", "Nam trầm", "Trẻ trung"])
st.session_state.ai_name = ai_name

# CSS tùy chỉnh giao diện + hiệu ứng
# Background theo giờ
hour = datetime.datetime.now().hour
if 6 <= hour < 18:
    bg_color = "linear-gradient(135deg, #f5f7fa, #c3cfe2)"
else:
    bg_color = "linear-gradient(135deg, #1e1e1e, #2b2b2b)"

background_style = f"""
    <style>
    .main {{
        background: {bg_color};
        font-family: 'Segoe UI', sans-serif;
        transition: background 1s ease-in-out;
        animation: bgFade 20s ease-in-out infinite alternate;
    }}
    body, .main, .block-container {{
        transition: all 0.5s ease-in-out;
    }}
    .dark .main {{
        background: linear-gradient(135deg, #2c2c2c, #3a3a3a);
        color: #f0f0f0;
    }}
    @keyframes bgFade {{
        0% {{ background-position: 0% 50%; }}
        100% {{ background-position: 100% 50%; }}
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
    .dark .chat-box {{
        background-color: #444444aa;
        color: #f0f0f0;
    }}
    </style>
"""

st.markdown(background_style, unsafe_allow_html=True)

# Hiển thị logo và tiêu đề chính
st.image("assets/logo.png", width=150)  # Thay đổi kích thước của logo tùy ý
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
user_input = st.text_input(f"Nhập câu hỏi cho {ai_name}...")

if user_input:
    st.session_state.history.append(("user", user_input))
    with st.spinner(f"🔄 {ai_name} đang phản hồi..."):
        try:
            response = st.session_state.chat.send_message(user_input)
            reply = response.text
            st.session_state.history.append(("assistant", reply))

            # Tìm và hiển thị hình ảnh nếu có liên kết ảnh trong phản hồi
            if any(ext in reply for ext in [".jpg", ".png", ".jpeg"]):
                for word in reply.split():
                    if word.startswith("http") and any(ext in word for ext in [".jpg", ".png", ".jpeg"]):
                        st.image(word, caption="Hình ảnh liên quan", use_column_width=True)

        except Exception as e:
            error_msg = f"❌ Lỗi: {e}"
            st.error(error_msg)
            st.session_state.history.append(("assistant", error_msg))
