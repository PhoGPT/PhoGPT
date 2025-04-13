import streamlit as st
import os
import json
from PIL import Image
import base64
import datetime
import markdown

# Tạo tệp lưu trữ người dùng nếu chưa có
USER_DATA_FILE = "users.json"

# Kiểm tra xem tệp lưu trữ người dùng có tồn tại không, nếu không thì tạo mới
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "w") as f:
        json.dump({}, f)

# Đăng ký người dùng
def register_user(username, password):
    with open(USER_DATA_FILE, "r") as f:
        users = json.load(f)
    if username in users:
        return False  # Tên người dùng đã tồn tại
    users[username] = password
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f)
    return True

# Đăng nhập người dùng
def login_user(username, password):
    with open(USER_DATA_FILE, "r") as f:
        users = json.load(f)
    if username in users and users[username] == password:
        return True
    return False

# Đặt tên mặc định cho AI
DEFAULT_AI_NAME = "PhoGPT"

# Đặt cấu hình cho trang
st.set_page_config(page_title="🤖 PhoGPT AI", page_icon="assets/logo.png", layout="centered")

# Hiển thị tên người dùng khi đã đăng nhập
if "user_logged_in" in st.session_state and st.session_state.user_logged_in:
    ai_name = f"Xin chào, {st.session_state.username}!"
else:
    ai_name = DEFAULT_AI_NAME

# Chức năng đăng ký và đăng nhập
def user_login_registration():
    if "user_logged_in" not in st.session_state or not st.session_state.user_logged_in:
        st.title("Đăng ký và Đăng nhập")
        action = st.selectbox("Chọn hành động", ["Đăng nhập", "Đăng ký"])

        username = st.text_input("Tên người dùng")
        password = st.text_input("Mật khẩu", type="password")

        if action == "Đăng ký":
            if st.button("Đăng ký"):
                if register_user(username, password):
                    st.success("Đăng ký thành công! Bạn có thể đăng nhập ngay.")
                else:
                    st.error("Tên người dùng đã tồn tại. Vui lòng chọn tên khác.")
        elif action == "Đăng nhập":
            if st.button("Đăng nhập"):
                if login_user(username, password):
                    st.success("Đăng nhập thành công!")
                    st.session_state.user_logged_in = True
                    st.session_state.username = username
                    st.experimental_rerun()  # Tải lại trang
                else:
                    st.error("Tên người dùng hoặc mật khẩu không đúng.")
    else:
        st.session_state.user_logged_in = True
        st.session_state.username = st.session_state.username

# Gọi hàm đăng nhập và đăng ký
user_login_registration()

# Chỉ cho phép người dùng đã đăng nhập tiếp tục sử dụng ứng dụng
if "user_logged_in" in st.session_state and st.session_state.user_logged_in:
    # Load Google API Key từ secrets.toml
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        st.error("⚠️ Không tìm thấy GOOGLE_API_KEY trong secrets.toml.")
        st.stop()

    # Cấu hình Gemini API
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"❌ Lỗi cấu hình API: {e}")
        st.stop()

    # Chọn mô hình Gemini ổn định
    MODEL_NAME = "models/gemini-1.5-pro"

    # Sidebar cài đặt
    st.sidebar.title("⚙️ Cài đặt")

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
    bg_color = "linear-gradient(135deg, #2c2c2c, #3a3a3a)" if hour >= 18 else "linear-gradient(135deg, #f5f7fa, #c3cfe2)"
    background_style = f"""
        <style>
        .main {{
            background: {bg_color};
            font-family: 'Segoe UI', sans-serif;
            transition: background 1s ease-in-out;
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
        }}
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
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
                        if word.startswith("http") and any(ext in word for ext in [".jpg", ".png", ".jpeg"]):
                            st.image(word, caption="Hình ảnh liên quan", use_column_width=True)

            except Exception as e:
                error_msg = f"❌ Lỗi: {e}"
                st.error(error_msg)
                st.session_state.history.append(("assistant", error_msg))