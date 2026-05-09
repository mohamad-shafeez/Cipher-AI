# skills/system.py
import psutil
import datetime
import os
import subprocess
import pyperclip
import platform
# import config

class SystemSkill:
    def __init__(self):
        print(">> Initializing System Skills...")
        self.os = platform.system()  # 'Windows', 'Linux', 'Darwin'
        print(f">> System Skills: ONLINE ({self.os})")

    # ─────────────────────────────────────────
    # TIME & DATE
    # ─────────────────────────────────────────
    def get_time(self):
        return datetime.datetime.now().strftime("%I:%M %p")

    def get_date(self):
        return datetime.datetime.now().strftime("%A, %B %d, %Y")

    # ─────────────────────────────────────────
    # BATTERY
    # ─────────────────────────────────────────
    def get_battery(self):
        battery = psutil.sensors_battery()
        if not battery:
            return "Battery information unavailable."
        status = "charging" if battery.power_plugged else "not charging"
        return f"Battery is at {battery.percent:.0f}% and {status}."

    # ─────────────────────────────────────────
    # VOLUME (Windows)
    # ─────────────────────────────────────────
    def set_volume(self, level):
        try:
            level = max(0, min(100, int(level)))
            if self.os == "Windows":
                # Most reliable method — no pycaw dependency
                script = f"""
                $obj = New-Object -ComObject WScript.Shell
                $obj.SendKeys([char]174 * 50)
                $steps = [math]::Round({level} / 2)
                $obj.SendKeys([char]175 * $steps)
                """
                subprocess.run(
                    ["powershell", "-Command", script],
                    capture_output=True
                )
            elif self.os == "Linux":
                subprocess.run(["amixer", "sset", "Master", f"{level}%"])
            elif self.os == "Darwin":
                subprocess.run(["osascript", "-e", f"set volume output volume {level}"])
            return f"Volume set to {level} percent."
        except Exception as e:
            return f"Could not set volume: {e}"

    def mute_volume(self):
        try:
            if self.os == "Windows":
                subprocess.run([
                    "powershell", "-Command",
                    "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
                ], capture_output=True)
            return "Volume muted."
        except Exception as e:
            return f"Could not mute: {e}"

    # ─────────────────────────────────────────
    # BRIGHTNESS
    # ─────────────────────────────────────────
    def set_brightness(self, level):
        try:
            import screen_brightness_control as sbc
            level = max(0, min(100, int(level)))
            sbc.set_brightness(level)
            return f"Brightness set to {level} percent."
        except Exception as e:
            return f"Could not set brightness: {e}"

    # ─────────────────────────────────────────
    # SYSTEM CONTROLS
    # ─────────────────────────────────────────
    def take_screenshot(self):
        try:
            import pyautogui
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            return f"Screenshot saved as {filename}."
        except Exception as e:
            return f"Could not take screenshot: {e}"

    def shutdown(self):
        try:
            if self.os == "Windows":
                os.system("shutdown /s /t 5")
            elif self.os in ["Linux", "Darwin"]:
                os.system("shutdown -h now")
            return "Shutting down in 5 seconds. Goodbye, sir."
        except Exception as e:
            return f"Could not shutdown: {e}"

    def restart(self):
        try:
            if self.os == "Windows":
                os.system("shutdown /r /t 5")
            elif self.os in ["Linux", "Darwin"]:
                os.system("shutdown -r now")
            return "Restarting in 5 seconds."
        except Exception as e:
            return f"Could not restart: {e}"

    def lock_screen(self):
        try:
            if self.os == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
            elif self.os == "Linux":
                os.system("gnome-screensaver-command -l")
            elif self.os == "Darwin":
                os.system("pmset displaysleepnow")
            return "Screen locked."
        except Exception as e:
            return f"Could not lock screen: {e}"

    # ─────────────────────────────────────────
    # CLIPBOARD
    # ─────────────────────────────────────────
    def get_clipboard(self):
        try:
            content = pyperclip.paste()
            return f"Clipboard contains: {content[:100]}" if content else "Clipboard is empty."
        except Exception as e:
            return f"Could not read clipboard: {e}"

    def clear_clipboard(self):
        try:
            pyperclip.copy("")
            return "Clipboard cleared."
        except Exception as e:
            return f"Could not clear clipboard: {e}"

    # ─────────────────────────────────────────
    # SYSTEM INFO
    # ─────────────────────────────────────────
    def get_system_info(self):
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return (
                f"CPU usage is {cpu}%. "
                f"RAM usage is {ram.percent}% with {ram.available // (1024**3)} GB available. "
                f"Disk usage is {disk.percent}%."
            )
        except Exception as e:
            return f"Could not get system info: {e}"

    # ─────────────────────────────────────────
    # EXECUTE — VOICE COMMAND ROUTER
    # ─────────────────────────────────────────
    def execute(self, command):
        command = command.lower()

        # Time & Date
        if "time" in command:
            return f"The time is {self.get_time()}."
        if "date" in command or "day" in command:
            return f"Today is {self.get_date()}."

        # Battery
        if any(w in command for w in ["battery", "metric", "power", "charge", "charging"]):
            return self.get_battery()

        # Volume
        if "mute" in command:
            return self.mute_volume()
        if "volume" in command:
            for word in command.split():
                if word.isdigit():
                    return self.set_volume(word)
            return "What volume level should I set, sir?"

        # Brightness
        if "brightness" in command:
            for word in command.split():
                if word.isdigit():
                    return self.set_brightness(word)
            return "What brightness level should I set, sir?"

        # Screenshot
        if "screenshot" in command or "capture screen" in command:
            return self.take_screenshot()

        # System controls
        if "shutdown" in command or "turn off" in command:
            return self.shutdown()
        if "restart" in command or "reboot" in command:
            return self.restart()
        if "lock" in command:
            return self.lock_screen()

        # Clipboard
        if "clipboard" in command:
            if "clear" in command:
                return self.clear_clipboard()
            return self.get_clipboard()

        # System info
        if any(w in command for w in ["system info", "stem info", "cpu", "ram", "memory", "disk", "system"]):
            return self.get_system_info()

        return None