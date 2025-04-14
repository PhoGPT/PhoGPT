import streamlit as st
import os
import json
import base64
import datetime
import markdown
from dotenv import load_dotenv
from PIL import Image
import hashlib
import dropbox

# Load biến môi trường từ .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
dropbox_token = os.getenv("DROPBOX_ACCESS_TOKEN")

if not api_key or not dropbox_token:
    st.error("❌ Không tìm thấy GOOGLE_API_KEY hoặc DROPBOX_ACCESS_TOKEN trong file .env.")
    st.stop()

# Cấu hình Google Generative AI
import google.generativeai as genai
genai.configure(api_key=api_key)

# Cấu hình Dropbox API
dbx = dropbox.Dropbox(dropbox_token)

# Cấu hình Streamlit
st.set_page_config(page_title="🤖 PhoGPT AI", page_icon="assets/logo.png", layout="centered")

# File dữ liệu người dùng trên Dropbox
USER_DATA_FILE = "/users.json"

# Mã hóa mật khẩu
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Hàm tải lên file JSON vào Dropbox
def upload_file(file_path, file_content):
    try:
        dbx.files_upload(json.dumps(file_content).encode(), file_path, mode=dropbox.files.WriteMode.overwrite)
        print(f"File đã được tải lên: {file_path}")
    except dropbox.exceptions.ApiError as err:
        print(f"Lỗi khi tải lên file: {err}")

# Hàm tải xuống file JSON từ Dropbox
def download_file(file_path):
    try:
        metadata, res = dbx.files_download(file_path)
        file_content = json.loads(res.content)
        print(f"File đã được tải xuống: {file_path}")
        return file_content
    except dropbox.exceptions.ApiError as err:
        print(f"Lỗi khi tải xuống file: {err}")
        return {}

# Hàm đăng ký
def register_user(username, password):
    users = download_file(USER_DATA_FILE)
    if username in users:
        return False
    users[username] = hash_password(password)
    upload_file(USER_DATA_FILE, users)
    return True

# Hàm đăng nhập
def login_user(username, password):
    users = download_file(USER_DATA_FILE)
    return username in users and users[username] == hash_password(password)

# Giao diện đăng nhập / đăng ký
def user_login_registration():
    if "user_logged_in" not in st.session_state or not st.session_state.user_logged_in:
        st.title("Đăng ký / Đăng nhập")
        action = st.selectbox("Chọn hành động", ["Đăng nhập", "Đăng ký"])
        username = st.text_input("Tên người dùng")
        password = st.text_input("Mật khẩu", type="password")

        if action == "Đăng ký" and st.button("Đăng ký"):
            if register_user(username, password):
                st.success("🎉 Đăng ký thành công!")
            else:
                st.error("❌ Tên người dùng đã tồn tại.")
        elif action == "Đăng nhập" and st.button("Đăng nhập"):
            if login_user(username, password):
                st.session_state.user_logged_in = True
                st.session_state.username = username
                st.success("✅ Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("❌ Sai tên người dùng hoặc mật khẩu.")

user_login_registration()

# Nếu đăng nhập thành công
if st.session_state.get("user_logged_in"):
    MODEL_NAME = "models/gemini-1.5-pro"
    ai_name = f"{st.session_state.username}"
    avatar_user = "https://i.pinimg.com/236x/5e/e0/82/5ee082781b8c41406a2a50a0f32d6aa6.jpg"
    avatar_ai = "https://scontent.fhph2-1.fna.fbcdn.net/v/t39.30808-6/490392190_678654707977227_1765116453897262223_n.jpg"

    def render_message(role, message, avatar_url):
        st.markdown(f"""
            <div style="display: flex; align-items: flex-start; margin-bottom: 1rem;">
                <img src="{avatar_url}" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 1rem;" />
                <div style="background-color: #ffffffcc; padding: 1rem 1.25rem; border-radius: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.05); max-width: 80%;">
                    {markdown.markdown(message)}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Sidebar
    st.sidebar.title("⚙️ Tuỳ chọn")
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Lịch sử đoạn chat")

    history_file = f"/history_{st.session_state.username}.json"
    if os.path.exists(history_file):
        st.session_state.history = download_file(history_file)
    else:
        st.session_state.history = []

    if st.sidebar.button("🧹 Xoá đoạn chat"):
        st.session_state.history = []

    if st.sidebar.button("💬 Đoạn chat mới"):
        st.session_state.history = []
        st.session_state.chat = genai.GenerativeModel(MODEL_NAME).start_chat()

    if st.sidebar.button("📥 Tải đoạn chat"):
        if st.session_state.get("history"):
            filename = f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            content = "\n".join([f"{r.upper()}: {m}" for r, m in st.session_state.history])
            b64 = base64.b64encode(content.encode()).decode()
            href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">📄 Tải xuống {filename}</a>'
            st.sidebar.markdown(href, unsafe_allow_html=True)

    if st.sidebar.button("🔒 Đăng xuất"):
        st.session_state.user_logged_in = False
        st.session_state.username = ""
        st.session_state.history = []
        st.success("👋 Đã đăng xuất!")
        st.rerun()

    # Khởi tạo model lần đầu
    if "chat" not in st.session_state:
        st.session_state.chat = genai.GenerativeModel(MODEL_NAME).start_chat()

    st.title(f"🤖 Xin chào, {ai_name}")
    st.caption("🧠 Trò chuyện cùng trợ lý AI PhoGPT")

    # Hiển thị lịch sử
    for role, msg in st.session_state.history:
        avatar = avatar_user if role == "user" else avatar_ai
        with st.chat_message(role):
            render_message(role, msg, avatar)

    # Nhập đầu vào
    user_input = st.chat_input(f"Nhập câu hỏi cho {ai_name}...")

    if user_input:
        st.session_state.history.append(("user", user_input))
        with st.chat_message("user"):
            render_message("user", user_input, avatar_user)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Đang suy nghĩ..."):
                try:
                    response = st.session_state.chat.send_message(user_input)
                    reply = response.text.strip().rstrip("|")
                    st.session_state.history.append(("assistant", reply))
                    render_message("assistant", reply, avatar_ai)

                    # Hiển thị ảnh nếu có
                    if any(ext in reply for ext in [".jpg", ".png", ".jpeg"]):
                        for word in reply.split():
                            if word.startswith("http") and any(ext in word for ext in [".jpg", ".png", ".jpeg"]):
                                st.image(word, caption="Hình ảnh liên quan", use_column_width=True)

                except Exception as e:
                    error_msg = f"❌ Lỗi: {e}"
                    st.session_state.history.append(("assistant", error_msg))
                    render_message("assistant", error_msg, avatar_ai)

    # Lưu lại lịch sử sau mỗi lần
    upload_file(history_file, st.session_state.history)

    # Trang quản trị
    if st.session_state.username == "admin":
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Quản trị viên")
        users = download_file(USER_DATA_FILE)
        st.sidebar.text(f"👥 Tổng người dùng: {len(users)}")
        st.sidebar.write("**Danh sách người dùng:**")
        for user in users:
            st.sidebar.write(f"- {user}")