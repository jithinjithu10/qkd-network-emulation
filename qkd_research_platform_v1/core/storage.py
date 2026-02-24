"""
storage.py
----------

Optimized Research-Grade Persistent Storage Layer
ETSI-Aligned | High-Performance | WAL Enabled | Batch Commit

Performance Improvements:
- Persistent global connection
- WAL journal mode
- Batched commit
- Reduced connection overhead
"""

import os
import sqlite3
from datetime import datetime, timezone, timedelta
from qkd_research_platform_v1.core.models import KeyState, KeyRole


# =================================================
# DATABASE CONFIGURATION
# =================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "kms.db")

# Global connection
_global_conn = None
_global_cursor = None


# =================================================
# INITIALIZE DATABASE (Persistent Connection)
# =================================================

def init_db():

    global _global_conn, _global_cursor

    if _global_conn:
        return  # Already initialized

    _global_conn = sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)
    _global_conn.row_factory = sqlite3.Row
    _global_cursor = _global_conn.cursor()

    # 🔥 Enable WAL for high write throughput
    _global_cursor.execute("PRAGMA journal_mode=WAL;")
    _global_cursor.execute("PRAGMA synchronous=NORMAL;")
    _global_cursor.execute("PRAGMA temp_store=MEMORY;")
    _global_cursor.execute("PRAGMA cache_size=10000;")

    # ---------------- KEY TABLE ----------------
    _global_cursor.execute("""
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
            bit_error_rate REAL,
            entropy_score REAL,
            amplification_factor REAL,
            link_quality REAL,
            reserved_at TEXT,
            consumed_at TEXT,
            expired_at TEXT,
            experiment_id TEXT
        )
    """)

    # Indexes
    _global_cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_state_role_node ON keys(state, role, node_id)"
    )
    _global_cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_created_at ON keys(created_at)"
    )
    _global_cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_experiment_id ON keys(experiment_id)"
    )

    _global_conn.commit()


# =================================================
# BATCH COMMIT
# =================================================

def commit_batch():
    global _global_conn
    if _global_conn:
        _global_conn.commit()


# =================================================
# STORE NEW KEY (Batch Insert)
# =================================================

def store_key(key, node_id="IITR", experiment_id=None):

    global _global_cursor

    _global_cursor.execute("""
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


# =================================================
# ATOMIC FETCH + RESERVE
# =================================================

def fetch_and_reserve(role: KeyRole, session_id: str, node_id="IITR"):

    global _global_conn, _global_cursor

    try:
        _global_cursor.execute("BEGIN IMMEDIATE")

        _global_cursor.execute("""
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

        row = _global_cursor.fetchone()

        if not row:
            _global_conn.commit()
            return None

        key_id = row["key_id"]
        now = datetime.now(timezone.utc).isoformat()

        _global_cursor.execute("""
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

        _global_conn.commit()
        return key_id

    except Exception:
        _global_conn.rollback()
        raise


# =================================================
# CONSUME KEY
# =================================================

def consume_key(key_id: str):

    global _global_conn, _global_cursor

    now = datetime.now(timezone.utc).isoformat()

    _global_cursor.execute("""
        UPDATE keys
        SET state = ?, consumed_at = ?
        WHERE key_id = ? AND state = ?
    """, (
        KeyState.CONSUMED.value,
        now,
        key_id,
        KeyState.RESERVED.value
    ))

    _global_conn.commit()


# =================================================
# TTL ENFORCEMENT
# =================================================

def expire_old_keys():

    global _global_conn, _global_cursor

    now = datetime.now(timezone.utc)

    _global_cursor.execute("""
        SELECT key_id, created_at, ttl
        FROM keys
        WHERE state IN (?, ?, ?)
    """, (
        KeyState.GENERATED.value,
        KeyState.READY.value,
        KeyState.RESERVED.value
    ))

    rows = _global_cursor.fetchall()

    for row in rows:
        created_time = datetime.fromisoformat(row["created_at"])
        if now > created_time + timedelta(seconds=row["ttl"]):
            _global_cursor.execute("""
                UPDATE keys
                SET state = ?, expired_at = ?
                WHERE key_id = ?
            """, (
                KeyState.EXPIRED.value,
                now.isoformat(),
                row["key_id"]
            ))

    _global_conn.commit()


# =================================================
# METRICS EXPORT
# =================================================

def get_storage_metrics():

    global _global_cursor

    def count(state):
        _global_cursor.execute(
            "SELECT COUNT(*) FROM keys WHERE state = ?", (state,)
        )
        return _global_cursor.fetchone()[0]

    return {
        "ready": count(KeyState.READY.value),
        "reserved": count(KeyState.RESERVED.value),
        "consumed": count(KeyState.CONSUMED.value),
        "expired": count(KeyState.EXPIRED.value)
    }


# =================================================
# EXHAUSTION DETECTION
# =================================================

def detect_key_exhaustion(threshold=1):

    global _global_cursor

    _global_cursor.execute("""
        SELECT COUNT(*) FROM keys
        WHERE state = ?
    """, (KeyState.READY.value,))

    ready_count = _global_cursor.fetchone()[0]

    return ready_count <= threshold