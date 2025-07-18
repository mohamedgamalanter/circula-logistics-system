
# -------------------- 99_Logout.py --------------------
import streamlit as st

st.set_page_config(page_title="Logout", page_icon="🚪")
st.title("🚪 Logout")

if st.button("Confirm Logout"):
    st.session_state.clear()
    st.success("You have been logged out.")
    st.switch_page("Home.py")
