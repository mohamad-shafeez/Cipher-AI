import sqlite3
import os
import json
from datetime import datetime
from typing import Any, Dict
from core.event_bus import Event

class CognitiveMemory:
    """A dual-tier memory system: Volatile (Working) and Persistent (Episodic)."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CognitiveMemory, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # 1. WORKING MEMORY (Volatile, clears on reboot)
        self.working_context: Dict[str, Any] = {
            "last_spoken_command": None,
            "active_project_directory": None,
            "last_launched_app": None,
            "current_focus": "idle"
        }
        
        # 2. EPISODIC MEMORY (Persistent SQLite database)
        os.makedirs("storage", exist_ok=True)
        self.db_path = "storage/cognitive_timeline.db"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_type TEXT,
                    source TEXT,
                    details TEXT
                )
            """)
            conn.commit()
            
        print("🧠 [COGNITIVE MEMORY]: Dual-tier memory systems initialized.")

    def _get_connection(self):
        """Creates a concurrency-safe database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # 🛡️ THE CONCURRENCY SHIELD
        # Enable Write-Ahead Logging to allow simultaneous readers/writers
        conn.execute('PRAGMA journal_mode=WAL;')
        # Optimize syncing for speed vs safety (NORMAL is best for WAL)
        conn.execute('PRAGMA synchronous=NORMAL;')
        # If the DB is locked, wait up to 5 seconds before giving up
        conn.execute('PRAGMA busy_timeout=5000;')
        
        return conn

    # --- WORKING MEMORY METHODS ---
    
    def update_working_context(self, key: str, value: Any):
        """Updates the fast, active context of the current session."""
        self.working_context[key] = value

    def get_working_context(self) -> Dict[str, Any]:
        return self.working_context

    # --- EPISODIC MEMORY METHODS ---

    def log_episode(self, event: Event):
        """Saves a permanent memory of an event to the SQLite timeline."""
        # We selectively log important things so the DB doesn't explode
        important_events = [
            "os.system.active", 
            "os.clipboard.changed", 
            "os.app.launched", 
            "graph.step.success", 
            "graph.step.failed"
        ]
        
        if event.type in important_events:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    data_str = json.dumps(event.data) if event.data is not None else ""
                    cursor.execute(
                        "INSERT INTO episodic_log (timestamp, event_type, source, details) VALUES (?, ?, ?, ?)",
                        (event.timestamp.isoformat(), event.type, event.source, data_str)
                    )
                    conn.commit()
            except Exception as e:
                print(f"⚠️ [MEMORY ERROR]: Failed to log episodic event to SQLite: {e}")
                
            # If an app was launched, update working memory so Cipher knows what's on screen!
            if event.type == "os.app.launched" and isinstance(event.data, dict):
                self.update_working_context("last_launched_app", event.data.get("application"))

    def recall_recent_episodes(self, limit: int = 5) -> list:
        """Pulls the most recent events from long-term storage."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timestamp, event_type, details FROM episodic_log ORDER BY id DESC LIMIT ?", (limit,))
                return cursor.fetchall()
        except Exception as e:
            print(f"⚠️ [MEMORY ERROR]: Failed to recall episodes: {e}")
            return []
