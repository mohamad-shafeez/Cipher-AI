import threading
import time
import re
import os
from datetime import datetime, timedelta
from core.speak import Speaker # Import the speaker for background alerts

class SchedulerSkill:
    def __init__(self):
        self.reminders = []
        self.lock = threading.Lock()
        self.running = True
        self.mouth = Speaker() # Background speaker instance
        
        # Start the background thread immediately
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        print(">> Scheduler Skill: ONLINE (Background Thread Active)")

    def _scheduler_loop(self):
        """Checks for due reminders every 2 seconds."""
        while self.running:
            now = datetime.now()
            due_reminders = []
            
            with self.lock:
                for rem in self.reminders[:]:
                    if now >= rem['time']:
                        due_reminders.append(rem)
                        self.reminders.remove(rem)
            
            # Speak the reminders outside the lock
            for rem in due_reminders:
                print(f"\n>> [ALARM] {rem['message']}")
                self.mouth.speak(f"Sir, I have a reminder for you: {rem['message']}")
            
            time.sleep(2)

    def _parse_time(self, command):
        """Extracts time and returns a datetime object."""
        now = datetime.now()
        
        # 1. Handle "in X minutes/hours"
        relative_match = re.search(r'in (\d+) (minute|minutes|min|hour|hours|hr)', command)
        if relative_match:
            amount = int(relative_match.group(1))
            unit = relative_match.group(2)
            if unit.startswith('hour') or unit.startswith('hr'):
                return now + timedelta(hours=amount)
            return now + timedelta(minutes=amount)

        # 2. Handle "at HH:MM AM/PM" or "at HH:MM"
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', command)
        if time_match:
            hr, mn = int(time_match.group(1)), int(time_match.group(2))
            meridiem = time_match.group(3)
            
            if meridiem == 'pm' and hr < 12: hr += 12
            if meridiem == 'am' and hr == 12: hr = 0
            
            target_time = now.replace(hour=hr, minute=mn, second=0, microsecond=0)
            if target_time < now:
                target_time += timedelta(days=1)
            return target_time

        return None

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()

            # --- LIST REMINDERS ---
            if any(w in cmd for w in ["list reminders", "show reminders", "what are my reminders"]):
                with self.lock:
                    if not self.reminders:
                        return "Sir, you have no pending reminders."
                    
                    resp = "Sir, your current reminders are: "
                    items = [f"{r['message']} at {r['time'].strftime('%I:%M %p')}" for r in self.reminders]
                    return resp + ". ".join(items)

            # --- SET REMINDER ---
            if "remind me" in cmd or "set alarm" in cmd:
                # Extract the message: "remind me to [MESSAGE] [TIME]"
                target_time = self._parse_time(cmd)
                if not target_time:
                    return "Sir, please specify a valid time, like 'in 10 minutes' or 'at 5:30 PM'."

                # Extract content
                content = cmd
                for word in ["remind me", "set alarm", "to", "at", "in", "for"]:
                    content = content.replace(word, "").strip()
                
                # Clean up leftover time strings from the message
                content = re.sub(r'\d{1,2}:\d{2}\s*(am|pm)?', '', content).strip()
                content = re.sub(r'in \d+ (minute|hour)\w*', '', content).strip()

                if not content:
                    content = "Time is up"

                with self.lock:
                    self.reminders.append({'time': target_time, 'message': content})
                
                return f"Sir, I have scheduled that reminder for {target_time.strftime('%I:%M %p')}."

            return None

        except Exception as e:
            print(f"[SchedulerSkill Error] {e}")
            return None