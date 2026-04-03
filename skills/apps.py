import os
import subprocess
import psutil

class AppSkills:
    def __init__(self):
        print(">> App Skills: ONLINE")
        # Maps keywords to (Display Name, List of possible paths)
        self.apps = {
            "chrome": ("Chrome", [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
            ]),
            "vs code": ("VS Code", [
                r"C:\Users\MOHAMAD SHAFEEZ\AppData\Local\Programs\Microsoft VS Code\Code.exe",
                os.path.expanduser(r"~\AppData\Local\Programs\Microsoft VS Code\Code.exe"),
                r"C:\Program Files\Microsoft VS Code\Code.exe"
            ]),
            "spotify": ("Spotify", [
                r"C:\Users\MOHAMAD SHAFEEZ\AppData\Roaming\Spotify\Spotify.exe",
                os.path.expanduser(r"~\AppData\Roaming\Spotify\Spotify.exe")
            ]),
            "notepad": ("Notepad", ["notepad.exe"]),
            "terminal": ("Terminal", ["wt.exe", "cmd.exe"]),
            "powershell": ("PowerShell", ["powershell.exe"]),
            "calculator": ("Calculator", ["calc.exe"]),
            "paint": ("Paint", ["mspaint.exe"]),
            "vlc": ("VLC", [r"C:\Program Files\VideoLAN\VLC\vlc.exe"]),
            "word": ("Word", ["winword.exe"]),
            "excel": ("Excel", ["excel.exe"]),
            "powerpoint": ("PowerPoint", ["powerpnt.exe"]),
            "settings": ("Settings", ["ms-settings:"]),
            "task manager": ("Task Manager", ["taskmgr.exe"]),
            "file explorer": ("Explorer", ["explorer.exe"])
        }

        # Block list to avoid conflicts with browser.py and mobile.py
        self.websites = ["youtube", "google", "github", "gmail", "facebook", "instagram", "twitter", "whatsapp"]

    def launch_app(self, app_name):
        app_name = app_name.lower().strip()
        
        # Longest match first logic
        target_key = None
        for key in sorted(self.apps.keys(), key=len, reverse=True):
            if key in app_name:
                target_key = key
                break
        
        if not target_key:
            return None

        display_name, paths = self.apps[target_key]

        for path in paths:
            try:
                if path.startswith("ms-"): # Handle Windows Settings
                    subprocess.Popen(f"start {path}", shell=True)
                    return f"Sir, opening your {display_name}."
                
                # Check if path is just a command (like notepad.exe) or a full path
                if "\\" not in path or os.path.exists(path):
                    # Launch and detach so Cipher doesn't wait
                    subprocess.Popen(
                        path if "\\" not in path else [path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                    )
                    return f"Sir, opening {display_name} for you."
            except Exception:
                continue
        
        return f"Sir, I found the path for {display_name}, but I couldn't launch it."

    def kill_app(self, app_name):
        try:
            killed = False
            for proc in psutil.process_iter(['name']):
                if app_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed = True
            return f"Sir, I have closed {app_name}." if killed else f"Sir, {app_name} doesn't seem to be running."
        except Exception as e:
            return f"I encountered an error while closing {app_name}."

    def execute(self, command):
        command_lower = command.lower().strip()

        # 1. SKIP Logic (Don't steal from other skills)
        if any(site in command_lower for site in self.websites): return None
        if "phone" in command_lower or "mobile" in command_lower: return None
        if any(w in command_lower for w in ["shutdown", "restart"]): return None

        # 2. OPEN Logic
        if any(w in command_lower for w in ["open", "launch", "start", "run"]):
            return self.launch_app(command_lower)

        # 3. CLOSE Logic
        if any(w in command_lower for w in ["close", "kill", "stop", "quit"]):
            # Extract the app name from command
            app_to_kill = command_lower
            for verb in ["close", "kill", "stop", "quit", "app"]:
                app_to_kill = app_to_kill.replace(verb, "").strip()
            return self.kill_app(app_to_kill)

        return None