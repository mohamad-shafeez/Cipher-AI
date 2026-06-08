"""
Multi-turn Conversation Manager

Maintains conversation session context, turn history, and message tracking.
Integrates with memory systems for persistent conversation state.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import sqlite3
import os

class ConversationMessage:
    """Represents a single message in a conversation."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }


class ConversationSession:
    """Represents a single conversation session with turn history."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.messages: List[ConversationMessage] = []
        self.turn_count = 0
        self.metadata: Dict[str, Any] = {
            "active_project": None,
            "active_app": None,
            "tags": []
        }
    
    def add_message(self, role: str, content: str):
        """Adds a message to the conversation."""
        msg = ConversationMessage(role, content)
        self.messages.append(msg)
        if role == "user":
            self.turn_count += 1
        return msg
    
    def get_context(self, max_turns: int = 5) -> str:
        """
        Generates conversation context string for memory injection.
        
        Args:
            max_turns: Number of recent turn pairs to include
        
        Returns:
            Formatted conversation history
        """
        if not self.messages:
            return ""
        
        # Get recent messages up to max_turns*2 (user + assistant pairs)
        recent = self.messages[-(max_turns * 2):] if len(self.messages) > max_turns * 2 else self.messages
        
        context = f"[CONVERSATION HISTORY - Session {self.session_id[:8]}]\n"
        context += f"Turn {self.turn_count}\n"
        context += "-" * 40 + "\n"
        
        for msg in recent:
            prefix = "User" if msg.role == "user" else "Cipher"
            context += f"{prefix}: {msg.content}\n"
        
        context += "-" * 40 + "\n"
        return context
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializes the session to a dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "turn_count": self.turn_count,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata
        }


class ConversationManager:
    """
    Manages conversation sessions and multi-turn context.
    Persists to SQLite for recovery across restarts.
    """
    
    def __init__(self):
        self.db_dir = "storage"
        self.db_path = os.path.join(self.db_dir, "conversations.db")
        
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL;')
        self.conn.execute('PRAGMA synchronous=NORMAL;')
        self.conn.execute('PRAGMA busy_timeout=5000;')
        
        self._init_db()
        
        # Current active session
        self.current_session: Optional[ConversationSession] = None
        
        print(">> Conversation Manager: ONLINE")
    
    def _init_db(self):
        """Initializes conversation tables."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT,
                last_turn_count INTEGER,
                metadata TEXT,
                active BOOLEAN DEFAULT 1
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                turn_number INTEGER,
                FOREIGN KEY(session_id) REFERENCES conversation_sessions(session_id)
            )
        """)
        self.conn.commit()
    
    def create_session(self) -> ConversationSession:
        """Creates a new conversation session."""
        session = ConversationSession()
        self.current_session = session
        
        # Persist to DB
        import json
        self.conn.execute(
            """INSERT INTO conversation_sessions 
               (session_id, created_at, last_turn_count, metadata, active) 
               VALUES (?, ?, ?, ?, ?)""",
            (session.session_id, session.created_at, 0, json.dumps(session.metadata), 1)
        )
        self.conn.commit()
        
        print(f"[Conversation Manager] New session created: {session.session_id[:8]}")
        return session
    
    def get_current_session(self) -> ConversationSession:
        """Gets or creates the current active session."""
        if self.current_session is None:
            self.create_session()
        return self.current_session
    
    def add_turn(self, user_message: str, assistant_message: str):
        """Adds a user-assistant turn pair to the current session."""
        session = self.get_current_session()
        
        # Add messages
        session.add_message("user", user_message)
        session.add_message("assistant", assistant_message)
        
        # Persist to DB
        user_msg_id = session.turn_count * 2 - 1
        asst_msg_id = session.turn_count * 2
        
        self.conn.execute(
            """INSERT INTO conversation_messages 
               (session_id, role, content, timestamp, turn_number) 
               VALUES (?, ?, ?, ?, ?)""",
            (session.session_id, "user", user_message, datetime.now().isoformat(), session.turn_count)
        )
        self.conn.execute(
            """INSERT INTO conversation_messages 
               (session_id, role, content, timestamp, turn_number) 
               VALUES (?, ?, ?, ?, ?)""",
            (session.session_id, "assistant", assistant_message, datetime.now().isoformat(), session.turn_count)
        )
        
        # Update session turn count
        self.conn.execute(
            "UPDATE conversation_sessions SET last_turn_count = ? WHERE session_id = ?",
            (session.turn_count, session.session_id)
        )
        self.conn.commit()
    
    def get_conversation_context(self, max_turns: int = 5) -> str:
        """Gets formatted context for memory injection."""
        session = self.get_current_session()
        return session.get_context(max_turns)
    
    def load_session(self, session_id: str) -> Optional[ConversationSession]:
        """Loads a previous session from database."""
        try:
            # Load session metadata
            row = self.conn.execute(
                "SELECT created_at, last_turn_count, metadata FROM conversation_sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            
            if not row:
                return None
            
            import json
            session = ConversationSession(session_id)
            session.created_at = row[0]
            session.turn_count = row[1]
            session.metadata = json.loads(row[2])
            
            # Load messages
            messages = self.conn.execute(
                """SELECT role, content, timestamp FROM conversation_messages 
                   WHERE session_id = ? ORDER BY id ASC""",
                (session_id,)
            ).fetchall()
            
            for role, content, timestamp in messages:
                session.messages.append(ConversationMessage(role, content, timestamp))
            
            self.current_session = session
            print(f"[Conversation Manager] Session loaded: {session_id[:8]} ({session.turn_count} turns)")
            return session
        
        except Exception as e:
            print(f"[Conversation Manager] Failed to load session: {e}")
            return None
    
    def end_session(self):
        """Ends the current session (marks as inactive)."""
        if self.current_session:
            self.conn.execute(
                "UPDATE conversation_sessions SET active = 0 WHERE session_id = ?",
                (self.current_session.session_id,)
            )
            self.conn.commit()
            print(f"[Conversation Manager] Session ended: {self.current_session.session_id[:8]}")
            self.current_session = None
    
    def list_sessions(self, active_only: bool = True) -> List[str]:
        """Lists all conversation sessions."""
        query = "SELECT session_id FROM conversation_sessions"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY created_at DESC"
        
        rows = self.conn.execute(query).fetchall()
        return [row[0] for row in rows]
