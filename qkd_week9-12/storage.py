"""
storage.py
-----------

Full Production Persistent Storage Layer
Weeks 4 – 12 Complete
ETSI-Aligned
Multi-Node Ready
Metrics & Evaluation Ready
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
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# =================================================
# INITIALIZE DATABASE
# =================================================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

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
            reserved_at TEXT,
            consumed_at TEXT,
            expired_at TEXT
        )
    """)

    # Performance indexes (critical for stress testing)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_role_node ON keys(state, role, node_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON keys(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON keys(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_node_id ON keys(node_id)")

    conn.commit()
    conn.close()


# =================================================
# STORE NEW KEY
# =================================================

def store_key(key, node_id="IITR"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO keys
        (key_id, key_value, key_size, created_at, ttl, state, role, session_id,
         node_id, reserved_at, consumed_at, expired_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        None,
        None,
        None
    ))

    conn.commit()
    conn.close()


# =================================================
# PROMOTE GENERATED → READY
# =================================================

def promote_generated_keys(node_id="IITR"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE keys
        SET state = ?
        WHERE state = ? AND node_id = ?
    """, (
        KeyState.READY.value,
        KeyState.GENERATED.value,
        node_id
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

        cursor.execute("""
            UPDATE keys
            SET state = ?, session_id = ?, reserved_at = ?
            WHERE key_id = ? AND state = ?
        """, (
            KeyState.RESERVED.value,
            session_id,
            datetime.now(timezone.utc).isoformat(),
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

    cursor.execute("""
        UPDATE keys
        SET state = ?, consumed_at = ?
        WHERE key_id = ? AND state = ?
    """, (
        KeyState.CONSUMED.value,
        datetime.now(timezone.utc).isoformat(),
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
# BUFFER METRICS
# =================================================

def count_ready_keys(role: KeyRole, node_id="IITR"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM keys
        WHERE state = ? AND role = ? AND node_id = ?
    """, (
        KeyState.READY.value,
        role.value,
        node_id
    ))

    count = cursor.fetchone()[0]
    conn.close()
    return count


def count_by_state(state: KeyState):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM keys
        WHERE state = ?
    """, (state.value,))

    count = cursor.fetchone()[0]
    conn.close()
    return count


def count_total_keys():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM keys")
    count = cursor.fetchone()[0]

    conn.close()
    return count


# =================================================
# WEEK 12 – METRICS EXPORT
# =================================================

def get_storage_metrics():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM keys WHERE state = ?", (KeyState.CONSUMED.value,))
    consumed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM keys WHERE state = ?", (KeyState.EXPIRED.value,))
    expired = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM keys WHERE state = ?", (KeyState.READY.value,))
    ready = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM keys WHERE state = ?", (KeyState.RESERVED.value,))
    reserved = cursor.fetchone()[0]

    conn.close()

    return {
        "total_ready": ready,
        "total_reserved": reserved,
        "total_consumed": consumed,
        "total_expired": expired
    }


# =================================================
# EXHAUSTION DETECTION
# =================================================

def detect_key_exhaustion(threshold: int = 1):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM keys
        WHERE state = ?
    """, (KeyState.READY.value,))

    ready_count = cursor.fetchone()[0]

    conn.close()

    return ready_count <= threshold
