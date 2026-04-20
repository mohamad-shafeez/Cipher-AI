import os
import subprocess
import psutil
import re
from typing import Optional

class AppsSkill:
    """
    Cipher Skill — Advanced Application Manager
    Dynamically locates, launches, and terminates Windows applications using Registry routing.
    """
    def __init__(self):
        print(">> App Skills: ONLINE (Advanced Process Manager Active)")
        # Map spoken names to (Display Name, [Exact Process Names], [Windows Launch Commands])
        self.apps = {
            "chrome": ("Google Chrome", ["chrome.exe"], ["chrome"]),
            "vs code": ("VS Code", ["Code.exe"], ["code"]),
            "visual studio code": ("VS Code", ["Code.exe"], ["code"]),
            "spotify": ("Spotify", ["Spotify.exe"], ["spotify"]),
            "notepad": ("Notepad", ["notepad.exe"], ["notepad"]),
            "terminal": ("Terminal", ["wt.exe", "cmd.exe"], ["wt", "cmd"]),
            "powershell": ("PowerShell", ["powershell.exe"], ["powershell"]),
            "calculator": ("Calculator", ["CalculatorApp.exe", "calc.exe"], ["calc"]),
            "paint": ("Paint", ["mspaint.exe"], ["mspaint"]),
            "vlc": ("VLC Media Player", ["vlc.exe"], ["vlc"]),
            "word": ("Microsoft Word", ["WINWORD.EXE"], ["winword"]),
            "excel": ("Microsoft Excel", ["EXCEL.EXE"], ["excel"]),
            "powerpoint": ("PowerPoint", ["POWERPNT.EXE"], ["powerpnt"]),
            "settings": ("Settings", ["SystemSettings.exe"], ["ms-settings:"]),
            "task manager": ("Task Manager", ["Taskmgr.exe"], ["taskmgr"]),
            "file explorer": ("File Explorer", ["explorer.exe"], ["explorer"])
        }
        
        # Ignored keywords to prevent overlapping with Browser or OS-level commands
        self.ignored_keywords = [
            "youtube", "google", "github", "gmail", "facebook", "instagram", 
            "twitter", "whatsapp", "phone", "mobile", "shutdown", "restart"
        ]

    def launch_app(self, app_name: str) -> str:
        target_key = None
        for key in self.apps.keys():
            if re.search(r'\b' + re.escape(key) + r'\b', app_name):
                target_key = key
                break
        
        if not target_key:
            # Fallback: If not in our dictionary, let Windows try to find it blindly
            clean_name = re.sub(r'^(?:open|launch|start|run)\s+', '', app_name).strip()
            try:
                subprocess.Popen(f"start {clean_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Sir, attempting to launch {clean_name.capitalize()} via the Windows registry."
            except Exception:
                return f"Sir, I could not find an application named {clean_name}."

        display_name, _, commands = self.apps[target_key]

        # Launch using the recognized Windows alias
        for cmd in commands:
            try:
                if cmd.startswith("ms-"):
                    subprocess.Popen(f"start {cmd}", shell=True)
                else:
                    subprocess.Popen(f"start {cmd}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Sir, opening {display_name}."
            except Exception:
                continue
        
        return f"Sir, I recognized {display_name}, but the executable failed to launch."

    def kill_app(self, app_name: str) -> str:
        target_key = None
        for key in self.apps.keys():
            if re.search(r'\b' + re.escape(key) + r'\b', app_name):
                target_key = key
                break
        
        # Extract raw name if not found in dictionary
        raw_name = re.sub(r'^(?:close|kill|stop|quit)\s+(?:the\s+)?(?:app\s+)?', '', app_name).strip()
        
        target_processes = self.apps[target_key][1] if target_key else [f"{raw_name}.exe", raw_name]
        display_name = self.apps[target_key][0] if target_key else raw_name.capitalize()

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