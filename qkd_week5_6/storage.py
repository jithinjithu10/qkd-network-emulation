"""
storage.py
-----------
Persistent storage layer for the Central KMS.

Implements:
- Q Buffer (GENERATED keys)
- S Buffer (RESERVED keys)
- ENC / DEC key pools
- TTL-based expiry
- Buffer statistics for adaptive refill
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from models import KeyState, KeyRole

DB_NAME = "kms.db"


# -------------------------------------------------
# Database Initialization
# -------------------------------------------------
def init_db():
    """
    Initialize the SQLite database and create tables if not present.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key_id TEXT PRIMARY KEY,
            key_value TEXT,
            key_size INTEGER,
            created_at TEXT,
            ttl INTEGER,
            state TEXT,
            role TEXT,
            session_id TEXT
        )
    """)

    conn.commit()
    conn.close()


# -------------------------------------------------
# Store New Key (Q Buffer)
# -------------------------------------------------
def store_key(key):
    """
    Store a newly generated key in the Q Buffer.
    Initial state: GENERATED
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO keys VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        key.key_id,
        key.key_value,
        key.key_size,
        key.created_at.isoformat(),
        int(key.ttl.total_seconds()),
        KeyState.GENERATED,
        key.role,
        None
    ))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Promote Q Buffer → READY
# -------------------------------------------------
def promote_generated_keys():
    """
    Promote GENERATED keys to READY state.
    Represents synchronization / validation phase.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE keys
        SET state = ?
        WHERE state = ?
    """, (KeyState.READY, KeyState.GENERATED))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Fetch READY Key (Policy-aware)
# -------------------------------------------------
def fetch_ready_key(role: KeyRole):
    """
    Fetch a READY key for the given role (ENC / DEC).
    Oldest key is selected to minimize waste.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key_id FROM keys
        WHERE state = ? AND role = ?
        ORDER BY created_at ASC
        LIMIT 1
    """, (KeyState.READY, role))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


# -------------------------------------------------
# Reserve Key (READY → RESERVED)
# -------------------------------------------------
def reserve_key(key_id, session_id):
    """
    Reserve a key for a session/application.
    Moves key from READY to RESERVED (S Buffer).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE keys
        SET state = ?, session_id = ?
        WHERE key_id = ?
    """, (KeyState.RESERVED, session_id, key_id))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Consume Key (RESERVED → CONSUMED)
# -------------------------------------------------
def consume_key(key_id):
    """
    Mark a key as consumed after cryptographic use.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE keys
        SET state = ?
        WHERE key_id = ?
    """, (KeyState.CONSUMED, key_id))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Expire Old Keys (TTL enforcement)
# -------------------------------------------------
def expire_old_keys():
    """
    Expire keys whose TTL has elapsed.
    Prevents stale key usage.
    """
    now = datetime.now(timezone.utc)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key_id, created_at, ttl FROM keys
        WHERE state IN (?, ?, ?)
    """, (KeyState.GENERATED, KeyState.READY, KeyState.RESERVED))

    rows = cursor.fetchall()

    for key_id, created_at, ttl in rows:
        created_time = datetime.fromisoformat(created_at)
        if now > created_time + timedelta(seconds=ttl):
            cursor.execute("""
                UPDATE keys SET state = ?
                WHERE key_id = ?
            """, (KeyState.EXPIRED, key_id))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Buffer Monitoring (Week 6)
# -------------------------------------------------
def count_ready_keys(role: KeyRole):
    """
    Return number of READY keys for a given role.
    Used for adaptive refill policies.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM keys
        WHERE state = ? AND role = ?
    """, (KeyState.READY, role))

    count = cursor.fetchone()[0]
    conn.close()

    return count
