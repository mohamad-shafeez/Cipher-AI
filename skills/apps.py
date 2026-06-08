import os
import subprocess
import psutil
import re
import time
import pyautogui
from typing import Optional

class AppsSkill:
    """
    Cipher Skill — Advanced Application Manager
    Dynamically locates, launches, and terminates Windows applications using Registry routing.
    """
    def __init__(self):
        print(">> App Skills: ONLINE (Advanced Process Manager Active)")
        
        # Ignored keywords to prevent overlapping with Browser or OS-level commands
        self.ignored_keywords = [
            "youtube", "google", "github", "gmail", "facebook", "instagram", 
            "twitter", "whatsapp", "phone", "mobile", "shutdown", "restart"
        ]

    def launch_app(self, app_name: str) -> str:
        clean_name = re.sub(r'^(?:open|launch|start|run)\s+', '', app_name).strip()
        
        try:
            print(f"[APPS] Using Windows Search to launch: {clean_name}")
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(clean_name, interval=0.05)
            time.sleep(0.5)
            pyautogui.press('enter')
            
            return f"Sir, I have attempted to launch {clean_name} via Windows Search."
        except Exception as e:
            print(f">> [APPS] Error in Windows Search launch: {e}")
            return f"Sir, I failed to launch {clean_name} via Windows Search."

    def kill_app(self, app_name: str) -> str:
        # Extract raw name
        raw_name = re.sub(r'^(?:close|kill|stop|quit)\s+(?:the\s+)?(?:app\s+)?', '', app_name).strip()
        
        target_processes = [f"{raw_name}.exe", raw_name]
        display_name = raw_name.capitalize()

        killed_count = 0
        try:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name']
                if proc_name and any(tp.lower() in proc_name.lower() for tp in target_processes):
                    proc.terminate() # Graceful termination
                    killed_count += 1
            
            if killed_count > 0:
                return f"Sir, I have successfully closed {display_name}."
            return f"Sir, {display_name} does not appear to be running."
        except psutil.AccessDenied:
            return f"Sir, I lack the administrator permissions required to close {display_name}."
        except Exception as e:
            return f"I encountered an error while trying to close {display_name}."

    def execute(self, command: str) -> Optional[str]:
        if not command: return None
        cmd = command.lower().strip()

        if any(w in cmd for w in self.ignored_keywords):
            return None

        # 1. Open / Launch Command
        if re.search(r"^(?:open|launch|start|run)\s+(.+)", cmd):
            return self.launch_app(cmd)

        # 2. Close / Kill Command
        if re.search(r"^(?:close|kill|stop|quit)\s+(.+)", cmd):
            return self.kill_app(cmd)

        return None