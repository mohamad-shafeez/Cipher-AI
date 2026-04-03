import sqlite3
import os
import re
from datetime import datetime

class VectorMemorySkill:
    def __init__(self):
        # Store memory in a dedicated data folder
        self.db_dir = "cipher_data"
        self.db_path = os.path.join(self.db_dir, "memory.db")
        
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()
        print(">> Vector Memory Skill: ONLINE (Long-term recall active)")

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()

            # --- TRIGGER 1: SAVING KNOWLEDGE ---
            # Command: "Cipher, remember that [FACT]"
            save_match = re.search(r"remember that (.*)", cmd)
            if save_match:
                fact = save_match.group(1).strip()
                # Use the first word as a primary tag, but store the whole thing
                words = fact.split()
                topic = words[0] if words else "general"
                
                print(f">> [VectorMemory] Committing to memory: {fact}")
                
                self.conn.execute(
                    "INSERT INTO knowledge (topic, content, timestamp) VALUES (?, ?, ?)",
                    (topic, fact, datetime.now().isoformat())
                )
                self.conn.commit()
                return f"Sir, I have committed that fact to my long-term memory banks under the sector '{topic}'."

            # --- TRIGGER 2: RECALLING KNOWLEDGE ---
            # Command: "What do you know about [TOPIC/FACT]" or "Recall [TOPIC/FACT]"
            recall_match = re.search(r"(what do you know about|recall|search memory for) (.*)", cmd)
            if recall_match:
                query = recall_match.group(2).strip()
                
                print(f">> [VectorMemory] Searching neural archives for: {query}")
                
                # Search both topics and content using SQL LIKE
                rows = self.conn.execute(
                    "SELECT content FROM knowledge WHERE topic LIKE ? OR content LIKE ? ORDER BY id DESC LIMIT 3",
                    (f"%{query}%", f"%{query}%")
                ).fetchall()

                if rows:
                    facts = " ".join([f"{r[0]}." for r in rows])
                    return f"Sir, my records indicate the following: {facts}"
                else:
                    return f"Sir, I searched my internal archives but found no relevant data regarding '{query}'."

            return None

        except Exception as e:
            print(f"[VectorMemory Error] {e}")
            return None