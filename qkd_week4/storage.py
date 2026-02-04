"""
storage.py
-----------
Handles persistent storage of keys using SQLite.
Responsible for storing, retrieving, and updating key lifecycle states.
"""

import sqlite3
from models import KeyState

DB_NAME = "kms.db"


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
            state TEXT
        )
    """)

    conn.commit()
    conn.close()


def store_key(key):
    """
    Store a newly generated key in the database.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO keys VALUES (?, ?, ?, ?, ?, ?)
    """, (
        key.key_id,
        key.key_value,
        key.key_size,
        key.created_at.isoformat(),
        int(key.ttl.total_seconds()),
        key.state
    ))

    conn.commit()
    conn.close()


def fetch_ready_key():
    """
    Fetch one unused (READY) key from the database.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key_id FROM keys
        WHERE state = 'READY'
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


def mark_consumed(key_id):
    """
    Mark a key as CONSUMED after it is issued to an application.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE keys SET state = 'CONSUMED'
        WHERE key_id = ?
    """, (key_id,))

    conn.commit()
    conn.close()
