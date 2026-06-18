import streamlit as st
import pandas as pd
from prescriptive_engine import get_system_advice

st.set_page_config(page_title="Hospital Pressure System", layout="wide")

df = pd.read_csv("results.csv")

st.title("🏥 Ireland Hospital Pressure Forecast System")

# ------------------------
# SIDEBAR
# ------------------------
region = st.sidebar.selectbox("Select Region", ["All"] + list(df["region"].unique()))

urgency = st.sidebar.selectbox(
    "How urgent is your issue?",
    ["Low", "Medium", "High"]
)

# Filter
if region != "All":
    df_view = df[df["region"] == region]
else:
    df_view = df

# ------------------------
# SYSTEM OVERVIEW
# ------------------------
st.subheader("System Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Hospitals", len(df_view))
col2.metric("Red Alerts", len(df_view[df_view["predicted_traffic_light"] == "Red"]))
col3.metric("Green Status", len(df_view[df_view["predicted_traffic_light"] == "Green"]))

st.divider()

# ------------------------
# TABLE
# ------------------------
st.subheader("Hospital Pressure Levels")

st.dataframe(
    df_view[["Hospital", "predicted_occupancy", "predicted_traffic_light"]]
)

st.divider()

# ------------------------
# PRESCRIPTIVE OUTPUT
# ------------------------
st.subheader("🧠 What should I do? (Personalised Guidance)")

system_status = (
    "Red" if len(df_view[df_view["predicted_traffic_light"] == "Red"]) > len(df_view)/2
    else "Amber" if len(df_view[df_view["predicted_traffic_light"] == "Amber"]) > 0
    else "Green"
)

advice = get_system_advice(system_status)

st.info(advice["message"])

for a in advice["advice"]:
    st.write("• " + a)

# ------------------------
# PERSONAL URGENCY LOGIC
# ------------------------
st.subheader("Personal Guidance")

if urgency == "High":
    st.error("➡ Go to A&E immediately regardless of system pressure.")
elif urgency == "Medium":
    st.warning("➡ Consider GP or urgent care depending on symptoms.")
else:
    st.success("➡ GP or pharmacy is likely appropriate first step.")
