# -------------------- Home.py --------------------
import streamlit as st

st.set_page_config(page_title="Logistics System", page_icon="🚚")
st.title("🚚 Logistics System")

# التحقق من حالة تسجيل الدخول
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.success(f"✅ Welcome back, {st.session_state['username']} ({st.session_state['role']})")
    st.info("Use the sidebar to go to your Dashboard or Logout.")
else:
    st.warning("🔐 Please login from the sidebar.")
