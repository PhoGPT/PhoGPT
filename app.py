import streamlit as st
import os
import pyttsx3
from dotenv import load_dotenv
import google.generativeai as genai
import platform

# Kiểm tra môi trường và quyết định có sử dụng TTS hay không
is_streamlit_cloud = "STREAMLIT_SERVER" in os.environ  # Kiểm tra môi trường Streamlit Cloud

# Nếu không phải trên Streamlit Cloud, tiếp tục khởi tạo TTS
if not is_streamlit_cloud:
    import pyttsx3
    engine = pyttsx3.init()
    def speak(text):
        engine.say(text)
        engine.runAndWait()

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", st.secrets.get("GOOGLE_API_KEY", "")))

# Khởi tạo Gemini
if "chat" not in st.session_state:
    model = genai.GenerativeModel("gemini-pro")
    st.session_state.chat = model.start_chat()

# NEW: Cho phép đặt tên AI
st.sidebar.header("⚙️ Tuỳ chỉnh")
ai_name = st.sidebar.text_input("PhoGPT", value=st.session_state.get("ai_name", "PhoGPT"))
st.session_state.ai_name = ai_name

# Cấu hình giao diện Streamlit
st.set_page_config(page_title=f"🤖 {ai_name} AI", page_icon="🤖", layout="centered")

# Header
st.title(f"🤖 {ai_name}")
st.caption(f"🧠 Trò chuyện cùng {ai_name}, trợ lý AI powered by Gemini")

# Tuỳ chọn đọc to
tts_enabled = st.checkbox("🔊 Luôn đọc to phản hồi", value=False)

# Xóa hội thoại
if st.button("🧹 Xóa hội thoại"):
    st.session_state.history = []

# Lưu hội thoại
if "history" not in st.session_state:
    st.session_state.history = []

# Hiển thị lịch sử hội thoại
for role, msg in st.session_state.history:
    with st.chat_message("user" if role == "user" else "assistant"):
        st.markdown(msg)

# Nhập từ người dùng
user_input = st.chat_input(f"💬 Hãy trò chuyện với {ai_name}...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.history.append(("user", user_input))

    with st.chat_message("assistant"):
        with st.spinner("🧠 Đang suy nghĩ..."):
            try:
                response = st.session_state.chat.send_message(user_input)
                reply = response.text
                st.markdown(reply)
                st.session_state.history.append(("assistant", reply))

                if tts_enabled and not is_streamlit_cloud:  # Chỉ đọc to nếu không phải trên Streamlit Cloud
                    speak(reply)

            except Exception as e:
                error_msg = f"❌ Lỗi: {e}"
                st.error(error_msg)
                st.session_state.history.append(("assistant", error_msg))