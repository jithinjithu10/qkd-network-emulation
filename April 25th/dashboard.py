# next_level_dashboard.py (FINAL FIXED VERSION)

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

from config import AUTH_TOKEN


# =================================================
# CONFIGURATION
# =================================================

IITR_KMS = "http://127.0.0.1:8000"
IITJ_KMS = "http://127.0.0.1:8001"
IITJ_API = f"{IITJ_KMS}/receive-message"

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}"
}


# =================================================
# WAIT FOR KEY SYNC (CRITICAL FIX)
# =================================================
def wait_for_key(key_id):
    for _ in range(10):
        try:
            r = requests.get(
                f"{IITJ_KMS}/etsi/v2/keys/{key_id}",
                headers=HEADERS,
                timeout=2
            )

            if r.status_code == 200:
                return True

        except:
            pass

        time.sleep(0.5)

    return False


# =================================================
# HELPERS
# =================================================
def get_status(url):
    try:
        r = requests.get(f"{url}/etsi/v2/status", headers=HEADERS, timeout=2)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


def log_metrics(status):
    if status:
        st.session_state.metrics.append({
            "time": datetime.now(),
            "available": status.get("available_keys", 0),
            "total": status.get("total_keys", 0),
            "sync": status.get("sync_index", 0)
        })


def log_throughput(size):
    st.session_state.throughput.append({
        "time": datetime.now(),
        "bytes": size
    })


# =================================================
# SESSION STATE
# =================================================
if "metrics" not in st.session_state:
    st.session_state.metrics = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "throughput" not in st.session_state:
    st.session_state.throughput = []


# =================================================
# UI
# =================================================
st.set_page_config(layout="wide")
st.title("QKD Dashboard")


# =================================================
# STATUS
# =================================================
status_iitr = get_status(IITR_KMS)
status_iitj = get_status(IITJ_KMS)

col1, col2, col3 = st.columns(3)

col1.metric("IITR Status", "Online" if status_iitr else "Offline")
col2.metric("IITJ Status", "Online" if status_iitj else "Offline")

if status_iitr:
    col3.metric("Available Keys", status_iitr["available_keys"])


# =================================================
# LAYOUT
# =================================================
left, right = st.columns([2, 1])


# =================================================
# ANALYTICS
# =================================================
with left:

    st.subheader("Live System Metrics")

    if status_iitr:
        log_metrics(status_iitr)

    if st.session_state.metrics:
        df = pd.DataFrame(st.session_state.metrics)
        st.line_chart(df.set_index("time")[["available"]])
        st.line_chart(df.set_index("time")[["sync"]])

    st.subheader("Throughput")

    if st.session_state.throughput:
        df_t = pd.DataFrame(st.session_state.throughput)
        st.line_chart(df_t.set_index("time")[["bytes"]])
    else:
        st.info("No data yet")


# =================================================
# CONTROL PANEL
# =================================================
with right:

    st.subheader("Send Message")

    msg = st.text_input("Message")

    if st.button("Send Secure Message"):

        if not msg:
            st.warning("Enter message")

        else:
            try:
                from secure_transfer import SecureTransfer

                st_obj = SecureTransfer(IITR_KMS, AUTH_TOKEN)

                key_id, iv, ct, tag = st_obj.send_secure_message(msg)

                # CRITICAL: WAIT FOR SYNC
                if not wait_for_key(key_id):
                    st.error("Receiver does not have key yet")
                    st.stop()

                response = requests.post(
                    IITJ_API,
                    headers=HEADERS,
                    json={
                        "key_id": key_id,
                        "iv": iv.hex(),
                        "ciphertext": ct.hex(),
                        "tag": tag.hex()
                    },
                    timeout=5
                )

                response.raise_for_status()

                size = len(msg.encode())
                log_throughput(size)

                st.session_state.messages.append({
                    "time": datetime.now(),
                    "message": msg,
                    "key_id": key_id
                })

                st.success("Message sent")

            except Exception as e:
                st.error(str(e))


    st.subheader("Message Log")

    if st.session_state.messages:
        df_msg = pd.DataFrame(st.session_state.messages)
        st.dataframe(df_msg, use_container_width=True)

        csv = df_msg.to_csv(index=False).encode()
        st.download_button("Download Logs", csv, "messages.csv")
    else:
        st.info("No messages yet")


# =================================================
# AUTO REFRESH
# =================================================
time.sleep(2)
st.rerun()