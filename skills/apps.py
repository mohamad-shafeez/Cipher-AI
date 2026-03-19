# skills/apps.py
import subprocess
import psutil
import config

class AppSkills:
    def __init__(self):
        print(">> App Skills: ONLINE")
        self.apps = {
            # Browsers
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            # Dev tools
            "vs code": r"C:\Users\MOHAMAD SHAFEEZ\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "vscode": r"C:\Users\MOHAMAD SHAFEEZ\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "notepad": "notepad.exe",
            "terminal": "wt.exe",
            "powershell": "powershell.exe",
            # Media
            "spotify": r"C:\Users\MOHAMAD SHAFEEZ\AppData\Roaming\Spotify\Spotify.exe",
            "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            # System
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "task manager": "taskmgr.exe",
            "file explorer": "explorer.exe",
            "control panel": "control.exe",
            "settings": "ms-settings:",
            # Office
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
        }

        # websites — handled by browser.py NOT here
        self.websites = [
            "youtube", "google", "github", "gmail", "facebook",
            "instagram", "twitter", "netflix", "amazon", "reddit",
            "stackoverflow", "linkedin", "whatsapp", "spotify"
        ]

    def launch_app(self, app_name):
        try:
            app_name = app_name.lower().strip()
            path = self.apps.get(app_name)

            if path:
                if path.startswith("ms-"):
                    subprocess.Popen(f"start {path}", shell=True)
                else:
                    subprocess.Popen(path, shell=True)
                return f"Opening {app_name}."
            else:
                # ← REMOVED dangerous fallback
                # Only open if it's a known app
                return None
        except Exception as e:
            return f"Could not open {app_name}: {e}"

    def kill_app(self, app_name):
        try:
            killed = False
            for proc in psutil.process_iter(['name']):
                if app_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed = True
            return f"Closed {app_name}." if killed else f"{app_name} is not running."
        except Exception as e:
            return f"Could not close {app_name}: {e}"

    def execute(self, command):
        command_lower = command.lower()

        # Launch app
        if any(w in command_lower for w in ["open", "launch", "start", "run"]):
            # ← Skip websites — let browser.py handle them
            if any(site in command_lower for site in self.websites):
                return None
            # ← Skip phone apps — let mobile.py handle them
            if "phone" in command_lower or "mobile" in command_lower:
                return None

            app = command_lower
            for w in ["open", "launch", "start", "run", "app", "application"]:
                app = app.replace(w, "").strip()

            if app:
                result = self.launch_app(app)
                return result  # returns None if app not found — lets other skills try

        # Kill app
        if any(w in command_lower for w in ["close", "kill", "stop", "quit"]):
            # Skip system shutdown commands
            if any(w in command_lower for w in ["shutdown", "restart", "system"]):
                return None
            app = command_lower
            for w in ["close", "kill", "stop", "quit", "app", "application"]:
                app = app.replace(w, "").strip()
            if app:
                return self.kill_app(app)

        return None