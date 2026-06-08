import os
import time
import sqlite3
import json
import psutil
import datetime
import threading
from core.hud_server import HUDServer
from core.llm_interface import LocalLLM
from core.speak import speak

class TemporalEngine:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TemporalEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.db_dir = "storage"
        self.db_path = os.path.join(self.db_dir, "cipher_temporal.db")
        
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()
        
        self.is_running = False
        self._thread = None
        self._initialized = True
        print(">> Temporal Memory Engine: ONLINE")

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                target_timestamp REAL,
                is_active INTEGER DEFAULT 1
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS recurring_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                cron_desc TEXT,
                last_run REAL,
                action_payload TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS watchers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expression TEXT,
                action_payload TEXT,
                check_interval_sec INTEGER DEFAULT 10,
                last_checked REAL DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        """)
        self.conn.commit()

    def start_daemon(self):
        """Starts the background temporal monitoring loop."""
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print(">> Temporal Engine background daemon thread started.")

    def add_reminder(self, message: str, delay_seconds: int) -> float:
        target_timestamp = time.time() + delay_seconds
        try:
            self.conn.execute(
                "INSERT INTO reminders (message, target_timestamp) VALUES (?, ?)",
                (message, target_timestamp)
            )
            self.conn.commit()
            formatted_time = datetime.datetime.fromtimestamp(target_timestamp).strftime('%I:%M:%S %p')
            print(f"⏰ [TEMPORAL]: Added reminder '{message}' scheduled for {formatted_time}")
            HUDServer.push_log(f"⏰ TEMPORAL: Added reminder for {formatted_time}")
            return target_timestamp
        except Exception as e:
            print(f"❌ [TEMPORAL ERROR] Failed to add reminder: {e}")
            return 0.0

    def add_watcher(self, expression: str, action_payload: str, check_interval: int = 10):
        try:
            self.conn.execute(
                "INSERT INTO watchers (expression, action_payload, check_interval_sec) VALUES (?, ?, ?)",
                (expression, action_payload, check_interval)
            )
            self.conn.commit()
            print(f"👁️ [TEMPORAL]: Added watcher '{expression}' -> '{action_payload}'")
            HUDServer.push_log(f"👁️ TEMPORAL: Watcher added for {expression}")
        except Exception as e:
            print(f"❌ [TEMPORAL ERROR] Failed to add watcher: {e}")

    def parse_and_schedule(self, user_input: str) -> bool:
        """
        Uses the LocalLLM to parse natural language temporal requests,
        and schedules them into the SQLite database dynamically.
        """
        HUDServer.set_agent("Heavy Planner")
        print(f"🧠 [TEMPORAL PARSER]: Parsing scheduled request -> '{user_input}'")
        
        system_prompt = """
        You are the Temporal Parsing Engine for an OS-level AI daemon.
        Analyze the user's scheduling/reminder request and output ONLY a raw JSON object.
        Do not include markdown formatting or explanations.
        
        Schema requirements:
        {
          "type": "reminder" | "recurring_task" | "watcher" | "unknown",
          "delay_seconds": int (number of seconds from now to execute, or null),
          "message": "the reminder message or description of the task",
          "watcher_expression": "condition expression like 'battery < 20' or null",
          "action_payload": "message/action to execute, or null"
        }
        
        Examples:
        - "remind me in 5 minutes to stretch"
          {"type": "reminder", "delay_seconds": 300, "message": "stretch", "watcher_expression": null, "action_payload": "stretch"}
        - "watch for battery dropping below 20 percent"
          {"type": "watcher", "delay_seconds": null, "message": "battery level low", "watcher_expression": "battery < 20", "action_payload": "Sir, your laptop battery is below 20 percent. Please connect a charger."}
        """
        
        raw_json_response = LocalLLM.generate(system_prompt, user_input)
        
        # Clean markdown code block decorators if present
        cleaned_response = raw_json_response.strip()
        if cleaned_response.startswith("```"):
            lines = cleaned_response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_response = "\n".join(lines).strip()
            
        try:
            payload = json.loads(cleaned_response)
            t_type = payload.get("type")
            
            if t_type == "reminder":
                delay = payload.get("delay_seconds")
                message = payload.get("message", "General reminder")
                if delay:
                    self.add_reminder(message, int(delay))
                    speak(f"Sir, I have set a reminder for '{message}' in {delay // 60} minutes.")
                    return True
                    
            elif t_type == "watcher":
                expr = payload.get("watcher_expression")
                action = payload.get("action_payload", "Watcher triggered")
                if expr and action:
                    self.add_watcher(expr, action)
                    speak("Sir, I have registered the background state watcher.")
                    return True
            
            print(f"⚠️ [TEMPORAL PARSER]: Unhandled or unknown schema: {payload}")
            return False
            
        except Exception as e:
            print(f"❌ [TEMPORAL PARSER CRASH]: Failed to parse: {e}. Raw: '{raw_json_response}'")
            return False

    def _evaluate_watchers(self):
        try:
            cursor = self.conn.execute("SELECT id, expression, action_payload, check_interval_sec, last_checked FROM watchers WHERE is_active = 1")
            watchers = cursor.fetchall()
            now = time.time()
            
            for w_id, expr, action, interval, last_checked in watchers:
                if now - last_checked < interval:
                    continue
                
                # Update last checked
                self.conn.execute("UPDATE watchers SET last_checked = ? WHERE id = ?", (now, w_id))
                self.conn.commit()
                
                # Evaluate watcher condition
                triggered = False
                if "battery" in expr:
                    battery = psutil.sensors_battery()
                    if battery:
                        percent = battery.percent
                        # Simple parser for e.g. "battery < 20"
                        if "<" in expr:
                            try:
                                val = int(expr.split("<")[1].strip())
                                if percent < val:
                                    triggered = True
                            except Exception:
                                pass
                
                if triggered:
                    print(f"👁️ [TEMPORAL WATCHER]: Condition '{expr}' triggered!")
                    HUDServer.push_log(f"👁️ WATCHER TRIGGERED: {expr}")
                    speak(action)
                    # Deactivate watcher to prevent spamming unless reset
                    self.conn.execute("UPDATE watchers SET is_active = 0 WHERE id = ?", (w_id,))
                    self.conn.commit()
        except Exception as e:
            print(f"❌ [TEMPORAL MONITOR ERROR]: Evaluation failure: {e}")

    def _monitor_loop(self):
        while self.is_running:
            try:
                now = time.time()
                
                # 1. Check reminders
                cursor = self.conn.execute("SELECT id, message, target_timestamp FROM reminders WHERE is_active = 1")
                reminders = cursor.fetchall()
                
                for r_id, message, target_time in reminders:
                    if now >= target_time:
                        print(f"⏰ [TEMPORAL REMINDER TRIGGERED]: {message}")
                        HUDServer.push_log(f"⏰ REMINDER: {message}")
                        
                        # Vocal alert
                        speak(f"Sir, this is your reminder to: {message}")
                        
                        # Mark inactive
                        self.conn.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (r_id,))
                        self.conn.commit()
                
                # 2. Evaluate state watchers
                self._evaluate_watchers()
                
            except Exception as e:
                print(f"❌ [TEMPORAL MONITOR LOOP ERROR]: {e}")
                
            time.sleep(1)
