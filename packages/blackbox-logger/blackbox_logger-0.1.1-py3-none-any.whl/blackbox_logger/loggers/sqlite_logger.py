import sqlite3
import os
import json
from datetime import datetime

class SQLiteLogger:
    def __init__(self, db_path="log/blackbox_logs.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                method TEXT,
                path TEXT,
                user TEXT,
                ip TEXT,
                user_agent TEXT,
                payload TEXT,
                status_code INTEGER,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def log(self, log_type, method, path, user, ip, user_agent, payload, status_code=None):
        self.conn.execute("""
            INSERT INTO logs (type, method, path, user, ip, user_agent, payload, status_code, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_type,
            method,
            path,
            user,
            ip,
            user_agent,
            json.dumps(payload),
            status_code,
            datetime.utcnow().isoformat()
        ))
        self.conn.commit()
