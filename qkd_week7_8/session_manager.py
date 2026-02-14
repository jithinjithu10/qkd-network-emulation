"""
session_manager.py
-------------------
Handles session abstraction for applications.
"""

import uuid


class SessionManager:

    def __init__(self):
        self.sessions = {}

    def create_session(self, app_id):
        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            "app_id": app_id,
            "active": True
        }

        return session_id

    def close_session(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]["active"] = False
            return True
        return False
