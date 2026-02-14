"""
storage.py
-----------
Persistent storage layer for the Central KMS.

Implements:
- Q Buffer (GENERATED keys)
- S Buffer (RESERVED keys)
- ENC / DEC key pools
- TTL-based expiry
- Buffer statistics
- Server-safe absolute DB path handling
"""

import os
import sqlite3
from datetime import datetime, timezone, timedelta
from models import KeyState, KeyRole


# -------------------------------------------------
# Absolute DB Path (Server + Local Safe)
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "kms.db")


# -------------------------------------------------
# Connection Helper
# -------------------------------------------------
def get_connection():
    """
    Create DB connection.
    Centralized for future migration (PostgreSQL etc.)
    """
    return sqlite3.connect(DB_NAME)


# -------------------------------------------------
# Database Initialization
# -------------------------------------------------
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
            session_id TEXT
        )
    """)

    conn.commit()
    conn.close()


# -------------------------------------------------
# Store New Key (Q Buffer – GENERATED)
# -------------------------------------------------
def store_key(key):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO keys
        (key_id, key_value, key_size, created_at, ttl, state, role, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        key.key_id,
        key.key_value,
        key.key_size,
        key.created_at.isoformat(),
        int(key.ttl.total_seconds()),
        KeyState.GENERATED.value,
        key.role.value,
        None
    ))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Promote GENERATED → READY
# -------------------------------------------------
def promote_generated_keys():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE keys
        SET state = ?
        WHERE state = ?
    """, (
        KeyState.READY.value,
        KeyState.GENERATED.value
    ))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Fetch Oldest READY Key (Policy-ready)
# -------------------------------------------------
def fetch_ready_key(role: KeyRole):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key_id
        FROM keys
        WHERE state = ? AND role = ?
        ORDER BY created_at ASC
        LIMIT 1
    """, (
        KeyState.READY.value,
        role.value
    ))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


# -------------------------------------------------
# Reserve Key (READY → RESERVED)
# -------------------------------------------------
def reserve_key(key_id: str, session_id: str):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE keys
        SET state = ?, session_id = ?
        WHERE key_id = ? AND state = ?
    """, (
        KeyState.RESERVED.value,
        session_id,
        key_id,
        KeyState.READY.value
    ))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Consume Key (RESERVED → CONSUMED)
# -------------------------------------------------
def consume_key(key_id: str):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE keys
        SET state = ?
        WHERE key_id = ? AND state = ?
    """, (
        KeyState.CONSUMED.value,
        key_id,
        KeyState.RESERVED.value
    ))

    conn.commit()
    conn.close()


# -------------------------------------------------
# TTL Enforcement
# -------------------------------------------------
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

    for key_id, created_at, ttl in rows:
        created_time = datetime.fromisoformat(created_at)

        if now > created_time + timedelta(seconds=ttl):
            cursor.execute("""
                UPDATE keys
                SET state = ?
                WHERE key_id = ?
            """, (
                KeyState.EXPIRED.value,
                key_id
            ))

    conn.commit()
    conn.close()


# -------------------------------------------------
# READY Buffer Count
# -------------------------------------------------
def count_ready_keys(role: KeyRole):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM keys
        WHERE state = ? AND role = ?
    """, (
        KeyState.READY.value,
        role.value
    ))

    count = cursor.fetchone()[0]
    conn.close()

    return count
