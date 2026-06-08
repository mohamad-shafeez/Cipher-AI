import sqlite3
import os
import re
import threading
from datetime import datetime

class VectorMemorySkill:
    def __init__(self):
        # Store memory in a dedicated data folder
        self.db_dir = "cipher_data"
        self.db_path = os.path.join(self.db_dir, "memory.db")
        
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
        
        self.lock = threading.Lock()
        self._init_db()
        print(">> Vector Memory Skill: ONLINE (Long-term recall active)")

    def _init_db(self):
        with self.lock:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    content TEXT,
                    timestamp TEXT
                )
            """)
            self.conn.commit()

    def save_interaction(self, command: str, result: str):
        try:
            with self.lock:
                self.conn.execute(
                    "INSERT INTO knowledge (topic, content, timestamp) VALUES (?, ?, ?)",
                    ("auto_memory", f"Command: {command}\nResult: {result}", datetime.now().isoformat())
                )
                self.conn.commit()
        except Exception as e:
            print(f"[VectorMemory Error] Failed to save interaction: {e}")

    def similarity_search(self, query: str) -> str:
        try:
            words = query.lower().split()
            if not words:
                return ""
            conditions = " OR ".join(["content LIKE ?"] * len(words))
            params = [f"%{w}%" for w in words]
            with self.lock:
                rows = self.conn.execute(
                    f"SELECT content FROM knowledge WHERE {conditions} ORDER BY id DESC LIMIT 3",
                    params
                ).fetchall()
            
            db_res = " ".join([r[0] for r in rows]) if rows else ""
            
            # --- INFINITE RAG MEMORY (Project Ledgers) ---
            project_res = []
            if os.path.exists("projects"):
                for root, dirs, files in os.walk("projects"):
                    for file in files:
                        if file.endswith(".md"):
                            try:
                                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                                    content = f.read()
                                    if any(w in content.lower() for w in words):
                                        # Extract context snippet
                                        project_res.append(f"[{file} Ledger Context]: {content[:500]}")
                            except Exception:
                                pass

            # --- DEEP RESEARCH VAULT (my_research/) ---
            research_res = []
            if os.path.exists("my_research"):
                for file in os.listdir("my_research"):
                    if file.endswith(".md"):
                        try:
                            with open(os.path.join("my_research", file), "r", encoding="utf-8") as f:
                                content = f.read()
                                if any(w in content.lower() for w in words):
                                    # Extract a larger snippet from research reports
                                    research_res.append(
                                        f"[Deep Research: {file}]: {content[:1000]}"
                                    )
                        except Exception:
                            pass

            full_context = db_res
            if project_res:
                full_context += "\n\nProject Ledgers Context:\n" + "\n".join(project_res[:2]) # Keep top 2
            if research_res:
                full_context += "\n\nDeep Research Vault:\n" + "\n".join(research_res[:2])  # Keep top 2

            return full_context
        except Exception as e:
            print(f"[VectorMemory Error] Similarity search failed: {e}")
            return ""

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
                
                with self.lock:
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
                with self.lock:
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