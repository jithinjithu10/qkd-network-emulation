"""
storage.py
----------

Research-Grade Persistent Storage Layer
ETSI-Aligned | Quantum Metadata Ready | Experiment-Aware
Weeks 4 – 12 Complete
"""

import os
import sqlite3
from datetime import datetime, timezone, timedelta
from models import KeyState, KeyRole


# =================================================
# DATABASE CONFIGURATION
# =================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "kms.db")


def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


# =================================================
# INITIALIZE DATABASE
# =================================================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # ---------------- KEY TABLE ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key_id TEXT PRIMARY KEY,
            key_value TEXT NOT NULL,
            key_size INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            ttl INTEGER NOT NULL,
            state TEXT NOT NULL,
            role TEXT NOT NULL,
            session_id TEXT,
            node_id TEXT,
            source_node TEXT,

            -- Quantum metadata
            bit_error_rate REAL,
            entropy_score REAL,
            amplification_factor REAL,
            link_quality REAL,

            -- Lifecycle timestamps
            reserved_at TEXT,
            consumed_at TEXT,
            expired_at TEXT,

            -- Experiment context
            experiment_id TEXT
        )
    """)

    # ---------------- LINK EVENTS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS link_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_a TEXT,
            node_b TEXT,
            event_type TEXT,
            timestamp TEXT
        )
    """)

    # ---------------- STRESS EVENTS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stress_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            timestamp TEXT
        )
    """)

    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_role_node ON keys(state, role, node_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON keys(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiment_id ON keys(experiment_id)")

    conn.commit()
    conn.close()


# =================================================
# STORE NEW KEY (Quantum-Aware)
# =================================================

def store_key(key, node_id="IITR", experiment_id=None):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO keys (
            key_id, key_value, key_size, created_at, ttl,
            state, role, session_id, node_id, source_node,
            bit_error_rate, entropy_score,
            amplification_factor, link_quality,
            reserved_at, consumed_at, expired_at,
            experiment_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        key.key_id,
        key.key_value,
        key.key_size,
        key.created_at.isoformat(),
        int(key.ttl.total_seconds()),
        KeyState.GENERATED.value,
        key.role.value,
        None,
        node_id,
        key.source_node,
        key.bit_error_rate,
        key.entropy_score,
        key.amplification_factor,
        key.link_quality,
        None,
        None,
        None,
        experiment_id
    ))

    conn.commit()
    conn.close()


# =================================================
# ATOMIC FETCH + RESERVE
# =================================================

def fetch_and_reserve(role: KeyRole, session_id: str, node_id="IITR"):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT key_id
            FROM keys
            WHERE state = ? AND role = ? AND node_id = ?
            ORDER BY created_at ASC
            LIMIT 1
        """, (
            KeyState.READY.value,
            role.value,
            node_id
        ))

        row = cursor.fetchone()

        if not row:
            conn.commit()
            return None

        key_id = row["key_id"]

        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            UPDATE keys
            SET state = ?, session_id = ?, reserved_at = ?
            WHERE key_id = ? AND state = ?
        """, (
            KeyState.RESERVED.value,
            session_id,
            now,
            key_id,
            KeyState.READY.value
        ))

        conn.commit()
        return key_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =================================================
# CONSUME KEY
# =================================================

def consume_key(key_id: str):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        UPDATE keys
        SET state = ?, consumed_at = ?
        WHERE key_id = ? AND state = ?
    """, (
        KeyState.CONSUMED.value,
        now,
        key_id,
        KeyState.RESERVED.value
    ))

    conn.commit()
    conn.close()


# =================================================
# TTL ENFORCEMENT
# =================================================

def expire_old_keys():

    now = datetime.now(timezone.utc)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key_id, created_at, ttl
        FROM keys
        WHERE state IN (?, ?, ?)
    """, (
        KeyState.GENERATED.value,
        KeyState.READY.value,
        KeyState.RESERVED.value
    ))

    rows = cursor.fetchall()

    for row in rows:
        created_time = datetime.fromisoformat(row["created_at"])
        if now > created_time + timedelta(seconds=row["ttl"]):
            cursor.execute("""
                UPDATE keys
                SET state = ?, expired_at = ?
                WHERE key_id = ?
            """, (
                KeyState.EXPIRED.value,
                now.isoformat(),
                row["key_id"]
            ))

    conn.commit()
    conn.close()


# =================================================
# LINK EVENT LOGGING (Week 11)
# =================================================

def record_link_event(node_a, node_b, event_type):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO link_events (node_a, node_b, event_type, timestamp)
        VALUES (?, ?, ?, ?)
    """, (
        node_a,
        node_b,
        event_type,
        datetime.now(timezone.utc).isoformat()
    ))

    conn.commit()
    conn.close()


# =================================================
# STRESS EVENT LOGGING
# =================================================

def record_stress_event(event_type):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO stress_events (event_type, timestamp)
        VALUES (?, ?)
    """, (
        event_type,
        datetime.now(timezone.utc).isoformat()
    ))

    conn.commit()
    conn.close()


# =================================================
# METRICS EXPORT (Week 12)
# =================================================

def get_storage_metrics():

    conn = get_connection()
    cursor = conn.cursor()

    def count(state):
        cursor.execute("SELECT COUNT(*) FROM keys WHERE state = ?", (state,))
        return cursor.fetchone()[0]

    metrics = {
        "ready": count(KeyState.READY.value),
        "reserved": count(KeyState.RESERVED.value),
        "consumed": count(KeyState.CONSUMED.value),
        "expired": count(KeyState.EXPIRED.value)
    }

    conn.close()
    return metrics


# =================================================
# EXHAUSTION DETECTION
# =================================================

def detect_key_exhaustion(threshold=1):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM keys
        WHERE state = ?
    """, (KeyState.READY.value,))

    ready_count = cursor.fetchone()[0]

    conn.close()

    if ready_count <= threshold:
        record_stress_event("KEY_EXHAUSTION")

    return ready_count <= threshold