# next_level_dashboard.py
# HYBRID QUANTUM-CLASSICAL QKD DASHBOARD

import hashlib
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from config import (
    AUTH_TOKEN,
    PEER_NODES,
    QKD_PROTOCOL,
    SYSTEM_MODE,
    ENABLE_SHA256_SYNC,
    ENABLE_QBER_MONITORING
)


# =========================================================
# CONFIGURATION
# =========================================================

IITR_KMS = PEER_NODES["IITR"]

IITJ_KMS = PEER_NODES["IITJ"]

IITJ_API = (
    f"{IITJ_KMS}/receive-message"
)

HEADERS = {

    "Authorization":
        f"Bearer {AUTH_TOKEN}"
}


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(

    page_title=
        "Hybrid QKD Dashboard",

    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title(
    "Hybrid Quantum-Classical QKD Dashboard"
)

st.markdown(
    """
Architecture:
- Quantum Layer → SimulaQron + BB84
- Classical Layer → FastAPI + ETSI APIs
- Encryption → AES-256-GCM
"""
)


# =========================================================
# SESSION STATE
# =========================================================

if "metrics" not in st.session_state:

    st.session_state.metrics = []

if "messages" not in st.session_state:

    st.session_state.messages = []

if "throughput" not in st.session_state:

    st.session_state.throughput = []

if "sync_logs" not in st.session_state:

    st.session_state.sync_logs = []


# =========================================================
# STATUS FETCH
# =========================================================

def get_status(url):

    try:

        r = requests.get(

            f"{url}/etsi/v2/status",

            headers=HEADERS,

            timeout=2
        )

        if r.status_code != 200:
            return None

        return r.json()

    except Exception:

        return None


# =========================================================
# WAIT FOR SYNCHRONIZATION
# =========================================================

def wait_for_sync(key_id):

    """
    Wait for synchronization metadata.
    """

    for _ in range(20):

        try:

            r = requests.get(

                f"{IITJ_KMS}/etsi/v2/keys/{key_id}",

                headers=HEADERS,

                timeout=2
            )

            if r.status_code == 200:

                data = r.json()

                if data.get("key_hash"):

                    return data

        except Exception:

            pass

        time.sleep(0.5)

    return None


# =========================================================
# METRIC LOGGER
# =========================================================

def log_metrics(status):

    if not status:
        return

    st.session_state.metrics.append({

        "time":
            datetime.now(),

        "available":
            status.get(
                "available_keys",
                0
            ),

        "total":
            status.get(
                "total_keys",
                0
            ),

        "sync":
            status.get(
                "sync_index",
                0
            ),

        "verified":
            status.get(
                "verified_keys",
                0
            )
    })


# =========================================================
# THROUGHPUT LOGGER
# =========================================================

def log_throughput(size):

    st.session_state.throughput.append({

        "time":
            datetime.now(),

        "bytes":
            size
    })


# =========================================================
# SHA-256 HASH
# =========================================================

def sha256_hash(key_material):

    return hashlib.sha256(
        key_material.encode()
    ).hexdigest()


# =========================================================
# VERIFY SYNCHRONIZATION
# =========================================================

def verify_sync(
    local_key,
    remote_hash
):

    local_hash = sha256_hash(
        local_key
    )

    return local_hash == remote_hash


# =========================================================
# FETCH METADATA
# =========================================================

def fetch_metadata(key_id):

    try:

        r = requests.get(

            f"{IITR_KMS}/etsi/v2/keys/{key_id}",

            headers=HEADERS,

            timeout=3
        )

        if r.status_code != 200:
            return None

        return r.json()

    except Exception:

        return None


# =========================================================
# STATUS PANEL
# =========================================================

status_iitr = get_status(IITR_KMS)

status_iitj = get_status(IITJ_KMS)

col1, col2, col3, col4 = st.columns(4)

col1.metric(

    "IITR",

    "ONLINE"
    if status_iitr
    else "OFFLINE"
)

col2.metric(

    "IITJ",

    "ONLINE"
    if status_iitj
    else "OFFLINE"
)

if status_iitr:

    col3.metric(

        "Available Keys",

        status_iitr.get(
            "available_keys",
            0
        )
    )

    col4.metric(

        "Verified Keys",

        status_iitr.get(
            "verified_keys",
            0
        )
    )


# =========================================================
# MAIN LAYOUT
# =========================================================

left, right = st.columns([2, 1])


# =========================================================
# ANALYTICS PANEL
# =========================================================

with left:

    st.subheader(
        "QKD System Analytics"
    )

    # -----------------------------------------------------
    # LOG METRICS
    # -----------------------------------------------------

    if status_iitr:

        log_metrics(status_iitr)

    # -----------------------------------------------------
    # METRICS GRAPH
    # -----------------------------------------------------

    if st.session_state.metrics:

        df = pd.DataFrame(
            st.session_state.metrics
        )

        st.markdown(
            "### Available Quantum Keys"
        )

        st.line_chart(
            df.set_index("time")[["available"]]
        )

        st.markdown(
            "### Synchronization Index"
        )

        st.line_chart(
            df.set_index("time")[["sync"]]
        )

        st.markdown(
            "### Verified Key Count"
        )

        st.line_chart(
            df.set_index("time")[["verified"]]
        )

    # -----------------------------------------------------
    # THROUGHPUT
    # -----------------------------------------------------

    st.subheader(
        "Communication Throughput"
    )

    if st.session_state.throughput:

        df_t = pd.DataFrame(
            st.session_state.throughput
        )

        st.line_chart(
            df_t.set_index("time")[["bytes"]]
        )

    else:

        st.info(
            "No throughput data"
        )


# =========================================================
# CONTROL PANEL
# =========================================================

with right:

    st.subheader(
        "Secure Message Transmission"
    )

    msg = st.text_input(
        "Message"
    )

    # -----------------------------------------------------
    # SEND SECURE MESSAGE
    # -----------------------------------------------------

    if st.button(
        "Send Secure Message"
    ):

        if not msg:

            st.warning(
                "Enter message"
            )

        else:

            try:

                from secure_transfer import (
                    SecureTransfer
                )

                # -----------------------------------------
                # SEND
                # -----------------------------------------

                st_obj = SecureTransfer(
                    IITR_KMS,
                    AUTH_TOKEN
                )

                (
                    key_id,
                    iv,
                    ct,
                    tag
                ) = st_obj.send_secure_message(
                    msg
                )

                # -----------------------------------------
                # WAIT FOR SYNC
                # -----------------------------------------

                metadata = wait_for_sync(
                    key_id
                )

                if not metadata:

                    st.error(
                        "Synchronization timeout"
                    )

                    st.stop()

                # -----------------------------------------
                # IMPORTANT ARCHITECTURE NOTE
                # -----------------------------------------

                """
                Raw keys should NEVER be fetched
                from metadata APIs.

                Future architecture:
                - fetch local BB84 key
                - verify hash only
                """

                remote_hash = metadata.get(
                    "key_hash"
                )

                verified = (
                    remote_hash is not None
                )

                # -----------------------------------------
                # SEND TO IITJ
                # -----------------------------------------

                response = requests.post(

                    IITJ_API,

                    headers=HEADERS,

                    json={

                        "key_id":
                            key_id,

                        "iv":
                            iv.hex(),

                        "ciphertext":
                            ct.hex(),

                        "tag":
                            tag.hex(),

                        "metadata":
                            {

                                "protocol":
                                    QKD_PROTOCOL,

                                "mode":
                                    SYSTEM_MODE,

                                "verified":
                                    verified
                            }
                    },

                    timeout=5
                )

                response.raise_for_status()

                # -----------------------------------------
                # THROUGHPUT
                # -----------------------------------------

                size = len(
                    msg.encode()
                )

                log_throughput(size)

                # -----------------------------------------
                # MESSAGE LOG
                # -----------------------------------------

                st.session_state.messages.append({

                    "time":
                        datetime.now(),

                    "message":
                        msg,

                    "key_id":
                        key_id,

                    "verified":
                        verified
                })

                # -----------------------------------------
                # SYNC LOG
                # -----------------------------------------

                st.session_state.sync_logs.append({

                    "time":
                        datetime.now(),

                    "key_id":
                        key_id,

                    "status":
                        (
                            "VERIFIED"
                            if verified
                            else "FAILED"
                        )
                })

                st.success(
                    "Secure message transmitted"
                )

            except Exception as e:

                st.error(str(e))

    # =====================================================
    # MESSAGE LOGS
    # =====================================================

    st.subheader(
        "Message Logs"
    )

    if st.session_state.messages:

        df_msg = pd.DataFrame(
            st.session_state.messages
        )

        st.dataframe(
            df_msg,
            use_container_width=True
        )

        csv = df_msg.to_csv(
            index=False
        ).encode()

        st.download_button(

            "Download Message Logs",

            csv,

            "messages.csv"
        )

    else:

        st.info(
            "No messages"
        )

    # =====================================================
    # SYNC LOGS
    # =====================================================

    st.subheader(
        "Synchronization Logs"
    )

    if st.session_state.sync_logs:

        df_sync = pd.DataFrame(
            st.session_state.sync_logs
        )

        st.dataframe(
            df_sync,
            use_container_width=True
        )

    else:

        st.info(
            "No synchronization logs"
        )


# =========================================================
# SYSTEM INFO
# =========================================================

st.markdown("---")

st.subheader(
    "QKD System Information"
)

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:

    st.markdown(
        f"""
### Quantum Layer
- Protocol: {QKD_PROTOCOL}
- SimulaQron Enabled
- Runtime Key Regeneration
"""
    )

with info_col2:

    st.markdown(
        """
### Classical Layer
- ETSI APIs
- Metadata Synchronization
- SHA-256 Verification
"""
    )

with info_col3:

    st.markdown(
        """
### Security Layer
- AES-256-GCM
- Authenticated Encryption
- Session Synchronization
"""
    )


# =========================================================
# AUTO REFRESH
# =========================================================

time.sleep(2)

st.rerun()