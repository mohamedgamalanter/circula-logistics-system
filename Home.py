import streamlit as st
from PIL import Image

st.set_page_config(page_title="Logistics System", page_icon="🚚")

# تحميل صورة اللوجو
logo = Image.open("logo_circula.png.jpeg")

with st.sidebar:
    st.image(logo, width=150)  # حجم اللوجو
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

if login_button:
    if username == "admin" and password == "1234":
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
    else:
        st.error("Invalid username or password")

if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.success(f"✅ Welcome back, {st.session_state['username']}")
    st.info("Use the sidebar to go to your Dashboard or Logout.")
else:
    st.warning("🔐 Please login from the sidebar.")
