# monitoring/dashboard_server.py

import streamlit as st
import pandas as pd
import requests
from config import CENTRAL_KMS_URL

st.set_page_config(layout="wide")

st.title("QKD Research Platform Dashboard")

# =================================================
# Live KMS Metrics
# =================================================

st.header("Live KMS Metrics")

if st.button("Refresh KMS Metrics"):

    response = requests.get(f"{CENTRAL_KMS_URL}/api/v1/metrics")

    if response.status_code == 200:
        data = response.json()

        st.json(data)
    else:
        st.error("Failed to fetch metrics")


# =================================================
# Experiment Results
# =================================================

st.header("Experiment Results")

try:
    df = pd.read_csv("experiment_results.csv")

    st.subheader("Raw Results")
    st.dataframe(df)

    st.subheader("Average Latency")
    st.bar_chart(df.set_index("mode")["avg_latency"])

    st.subheader("Throughput")
    st.bar_chart(df.set_index("mode")["throughput_bytes_per_sec"])

    st.subheader("Success Rate")
    st.bar_chart(df.set_index("mode")["success_rate"])

    st.subheader("Rekey Count")
    st.bar_chart(df.set_index("mode")["rekey_count"])

except FileNotFoundError:
    st.warning("No experiment_results.csv found. Run experiments first.")