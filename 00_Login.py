
# -------------------- 00_Login.py --------------------
import streamlit as st
import pandas as pd

# Load users data
users_df = pd.read_excel("logistics_system_sheets.xlsx", sheet_name="Users")

st.set_page_config(page_title="Login", page_icon="🔐")
st.title("🔐 Logistics System Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")
login_button = st.button("Login")

if login_button:
    user = users_df[(users_df["Username"] == username) & (users_df["Password"] == password)]
    if not user.empty:
        # Store session data
        st.session_state["logged_in"] = True
        st.session_state["username"] = user.iloc[0]["Username"]
        st.session_state["role"] = user.iloc[0]["Role"]
        st.session_state["region"] = user.iloc[0]["Region"]
        st.session_state["branch_code"] = user.iloc[0]["Branch Code"]
        st.success("✅ Login successful!")
        st.rerun()

    else:
        st.error("❌ Invalid username or password.")
