import sqlite3
import os
from datetime import datetime

class MemorySQL:
    def __init__(self):
        self.db_dir = "storage"
        self.db_path = os.path.join(self.db_dir, "cipher_history.db")
        
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # 🛡️ THE CONCURRENCY SHIELD
        # Enable Write-Ahead Logging to allow simultaneous readers/writers
        self.conn.execute('PRAGMA journal_mode=WAL;')
        # Optimize syncing for speed vs safety (NORMAL is best for WAL)
        self.conn.execute('PRAGMA synchronous=NORMAL;')
        # If the DB is locked, wait up to 5 seconds before giving up
        self.conn.execute('PRAGMA busy_timeout=5000;')
        
        self._init_db()
        print(">> Memory SQL: ONLINE")

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                raw_input TEXT,
                executed_skill TEXT,
                response_summary TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS self_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                failed_state TEXT,
                successful_state TEXT
            )
        """)
        self.conn.commit()

    def log_self_correction(self, failed_state: str, successful_state: str):
        try:
            self.conn.execute(
                "INSERT INTO self_corrections (timestamp, failed_state, successful_state) VALUES (?, ?, ?)",
                (datetime.now().isoformat(), failed_state, successful_state)
            )
            self.conn.commit()
            print(">> [Memory SQL] Logged Self-Correction learning event.")
        except Exception as e:
            print(f"[MemorySQL Error] Failed to log self-correction: {e}")

    def add_log(self, raw_input: str, executed_skill: str, response_summary: str):
        try:
            self.conn.execute(
                "INSERT INTO interactions (timestamp, raw_input, executed_skill, response_summary) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), raw_input, executed_skill, response_summary)
            )
            self.conn.commit()
        except Exception as e:
            print(f"[MemorySQL Error] Failed to add log: {e}")

    def get_recent_context(self, limit=3) -> str:
        try:
            rows = self.conn.execute(
                "SELECT raw_input, response_summary FROM interactions ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
            
            if not rows:
                return ""
                
            context = []
            # Reverse to get chronological order (oldest first)
            for row in reversed(rows):
                context.append(f"User: {row[0]}\nCipher: {row[1]}")
                
            return "\n\n".join(context)
        except Exception as e:
            print(f"[MemorySQL Error] Failed to get context: {e}")
            return ""
