import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from openpyxl import load_workbook
from PIL import Image

st.set_page_config(page_title="CIRCULA LOGESTIC SYSTEM", page_icon="🚚", layout="wide")

# Load logo and set header
logo = Image.open("logo_circula.png.jpeg")
st.image(logo, width=150)

# Check login session
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🚫 Please login first.")
    st.stop()

# Load data
excel_path = "logistics_system_sheets.xlsx"
transfers_df = pd.read_excel(excel_path, sheet_name="Transfers")
users_df = pd.read_excel(excel_path, sheet_name="Users")

# Session info
username = st.session_state["username"]
role = st.session_state["role"]
region = st.session_state["region"]
branch_code = st.session_state["branch_code"]

st.title(f"🚚 Welcome to CIRCULA, {role} - {username}")

# --- HELPER FUNCTIONS ---
def save_transfers():
    with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        transfers_df.to_excel(writer, sheet_name="Transfers", index=False)

def get_days_diff(date):
    if pd.isna(date): return 0
    return (datetime.now() - pd.to_datetime(date)).days

# ====== FILTERS ======
st.markdown("### فلاتر عامة (تنطبق على كل الجداول أدناه)")
all_branches = sorted(set(transfers_df["From Branch"]).union(transfers_df["To Branch"]))
selected_branch = st.selectbox("فلتر برقم الفرع", ["All"] + all_branches)
filter_date = st.date_input("فلتر بالتاريخ (اختياري)", value=None)
search_transfer_id = st.text_input("بحث برقم التحويل (اختياري)").strip()

filtered_df = transfers_df.copy()
if selected_branch != "All":
    filtered_df = filtered_df[
        (filtered_df["From Branch"] == selected_branch) |
        (filtered_df["To Branch"] == selected_branch)
    ]

if filter_date:
    filtered_df["Created At"] = pd.to_datetime(filtered_df["Created At"])
    filtered_df = filtered_df[filtered_df["Created At"].dt.date == filter_date]

if search_transfer_id:
    filtered_df = filtered_df[filtered_df["Transfer ID"].astype(str).str.contains(search_transfer_id, case=False)]

# === BRANCH ===
if role == "Branch":
    st.header(":package: Create Manual Transfer")
    transfer_id = st.text_input("Enter Transfer ID (Manual)")

    branch_list = sorted(users_df[users_df["Role"] == "Branch"]["Branch Code"].unique().tolist())
    branch_list = [b for b in branch_list if b != branch_code]
    to_branch = st.selectbox("To Branch Code", options=["Select..."] + branch_list, index=0)

    transfer_type = st.selectbox("Transfer Type", options=["NORMAL", "RETURN", "RECALL"], index=0)
    value = st.number_input("Transfer Value (SAR)", min_value=1.0, format="%.2f")
    notes = st.text_area("Notes (Optional)")
    submit = st.button("Submit Transfer")

    if submit and transfer_id and to_branch != "Select...":
        new_transfer = {
            "Transfer ID": transfer_id,
            "From Branch": branch_code,
            "To Branch": to_branch,
            "Value": value,
            "Transfer Type": transfer_type,
            "Status": "Pending",
            "Created At": datetime.now(),
            "Picked Up At": None,
            "Received At": None,
            "Driver": "",
            "Handled By WH": "",
            "Attachment": "",
            "Notes": notes
        }
        transfers_df.loc[len(transfers_df)] = new_transfer
        save_transfers()
        st.success(f"✅ Transfer {transfer_id} created.")
        st.session_state["transfer_id"] = ""
        st.session_state["to_branch"] = "Select..."
        st.session_state["value"] = 1.0
        st.session_state["notes"] = ""
        st.rerun()
 

    # KPIs
    st.markdown("---")
    st.subheader(":bar_chart: Transfer KPIs")
    sent = filtered_df[filtered_df["From Branch"] == branch_code]
    received = filtered_df[filtered_df["To Branch"] == branch_code]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Sent Total", f"{sent['Value'].sum():,.2f}", len(sent))
    col2.metric("Received Total", f"{received['Value'].sum():,.2f}", len(received))
    col3.metric("Pending Sent", f"{sent[sent['Status'] != 'Received']['Value'].sum():,.2f}")

    col4, col5 = st.columns(2)
    col4.metric("Receiving Pending", f"{received[received['Status'] != 'Received']['Value'].sum():,.2f}")
    col5.metric("Most From", received["From Branch"].mode().values[0] if not received.empty else "-")

    # Transfers view
    st.markdown("---")
    st.subheader("Your Transfers")

    sending_pending = sent[sent["Status"] != "Received"]
    sent_done = sent[sent["Status"] == "Received"]
    receiving_pending = received[received["Status"] != "Received"]
    received_done = received[received["Status"] == "Received"]

    with st.expander("📤 Sending Pending"):
        st.dataframe(sending_pending)
    with st.expander("✅ Sent Transfers"):
        st.dataframe(sent_done)
    with st.expander("📥 Receiving Pending"):
        for i, row in receiving_pending.iterrows():
            with st.expander(f"{row['Transfer ID']} | {row['Status']} | SAR {row['Value']:,.2f}"):
                st.write(row)
                if st.button(f"Confirm Receipt - {row['Transfer ID']}", key=f"receive_{i}"):
                    transfers_df.at[i, "Status"] = "Received"
                    transfers_df.at[i, "Received At"] = datetime.now()
                    save_transfers()
                    st.success("Marked as Received!")
                    st.rerun()
    with st.expander("✅ Received Transfers"):
        st.dataframe(received_done)

elif role == "Driver":
    st.header("🚛 Available Transfers to Pick Up")
    prefix = {"Riyadh": "P00", "Taif": "P01", "Jeddah": "P02", "Qassim": "P03", "Meccah": "P04"}.get(region, "")

    # الفلترة تكون على الجدول الأصلي دايمًا
    pending = transfers_df[
        (
            (transfers_df["From Branch"].str.startswith(prefix)) |
            (transfers_df["To Branch"].str.startswith(prefix))
        ) &
        (transfers_df["Status"] == "Pending")
    ]

    for i, row in pending.iterrows():
        with st.expander(f"{row['Transfer ID']} | {row['From Branch']} ➜ {row['To Branch']} | SAR {row['Value']:,.2f}"):
            st.write(row)
            if st.button(f"📥 Pick Up - {row['Transfer ID']}", key=f"pickup_{i}"):
                idx = row.name  # index الحقيقي في transfers_df
                transfers_df.at[idx, "Status"] = "Picked Up"
                transfers_df.at[idx, "Picked Up At"] = datetime.now()
                transfers_df.at[idx, "Driver"] = username
                save_transfers()
                st.success("Picked up.")
                st.rerun()

    st.markdown("---")
    st.subheader("📦 Transfers You're Holding")
    # نعرض التحويلات اللي مع السواق فعلاً من الجدول الأصلي مش filtered_df
    holding = transfers_df[(transfers_df["Driver"] == username) & (transfers_df["Status"] == "Picked Up")]
    for i, row in holding.iterrows():
        with st.expander(f"{row['Transfer ID']} | To {row['To Branch']} | SAR {row['Value']:,.2f}"):
            st.write(row)
            if st.button(f"🏭 Put in WH - {row['Transfer ID']}", key=f"putwh_{i}"):
                idx = row.name
                transfers_df.at[idx, "From Branch"] = "WH"
                transfers_df.at[idx, "Status"] = "Pending"
                transfers_df.at[idx, "Handled By WH"] = "Yes"
                transfers_df.at[idx, "Picked Up At"] = None
                transfers_df.at[idx, "Driver"] = ""
                save_transfers()
                st.success("Sent to WH.")
                st.rerun()


# === SUPERVISOR & MANAGER ===
elif role in ["Supervisor", "Manager"]:
    def map_region(code):
        if code.startswith("P00"):
            return "الرياض"
        elif code.startswith("P01"):
            return "الطائف"
        elif code.startswith("P02"):
            return "جدة"
        elif code.startswith("P03"):
            return "القصيم"
        else:
            return "أخرى"

    # Filter by region if Supervisor
    if role == "Supervisor":
        region_mapping = {
            "RIYADH": "P00",
            "TAIF": "P01",
            "JEDDAH": "P02",
            "QASSIM": "P03"
        }
        region_code = region_mapping.get(region.upper(), "")
        region_transfers = filtered_df[
            ((filtered_df["From Branch"].str.startswith(region_code)) |
             (filtered_df["To Branch"].str.startswith(region_code))) &
            (~filtered_df["From Branch"].str.startswith("WH")) &
            (~filtered_df["To Branch"].str.startswith("WH"))
        ]
    else:
        region_transfers = filtered_df.copy()

    st.header("📊 Transfers Overview")
    st.dataframe(region_transfers)

    if not region_transfers.empty:
        region_transfers["Created At"] = pd.to_datetime(region_transfers["Created At"])
        region_transfers["Month"] = region_transfers["Created At"].dt.to_period("M").astype(str)
        region_transfers["Region"] = region_transfers["From Branch"].apply(map_region)

        monthly_summary = region_transfers.groupby("Month")["Value"].sum().reset_index()
        st.subheader("📈 Monthly Transfer Value")
        st.bar_chart(monthly_summary.set_index("Month"))

        region_summary = region_transfers.groupby("Region")["Value"].sum().reset_index()
        st.subheader("🧭 Transfer Distribution by Region")
        fig = px.pie(region_summary, names="Region", values="Value", title="Transfer Value by Region")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transfers found with current filters.")

# === OWNER ===
elif role == "Owner":
    st.header("🏢 Full Company Overview")

    def map_region(code):
        if code.startswith("P00"):
            return "الرياض"
        elif code.startswith("P01"):
            return "الطائف"
        elif code.startswith("P02"):
            return "جدة"
        elif code.startswith("P03"):
            return "القصيم"
        else:
            return "أخرى"

    st.dataframe(filtered_df)

    total_value = filtered_df[filtered_df["Status"] == "Received"]["Value"].sum()
    pending_value = filtered_df[filtered_df["Status"] == "Pending"]["Value"].sum()
    st.metric("Company Transfers Completed", f"{total_value:,.2f} SAR")
    st.metric("Pending Transfers", f"{pending_value:,.2f} SAR")

    filtered_df["Region"] = filtered_df["From Branch"].apply(map_region)

    st.subheader("📌 Region Summary")
    region_summary = filtered_df.groupby("Region")["Value"].agg(["sum", "count"]).reset_index()
    st.dataframe(region_summary)

    if not filtered_df.empty:
        filtered_df["Month"] = pd.to_datetime(filtered_df["Created At"]).dt.to_period("M").astype(str)
        monthly_chart = filtered_df.groupby("Month")["Value"].sum().reset_index()
        st.subheader("📊 Monthly Transfer Value")
        st.bar_chart(monthly_chart.set_index("Month"))

        region_pie = filtered_df.groupby("Region")["Value"].sum().reset_index()
        st.subheader("📍 Transfer Value by Area")
        fig = px.pie(region_pie, names="Region", values="Value", title="Distribution by Area")
        st.plotly_chart(fig)

# === LOGOUT ===
if st.button("Logout"):
    st.session_state.clear()
    st.rerun()
