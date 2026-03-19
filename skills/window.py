# skills/window.py
import subprocess
import pyautogui
import psutil
import config

class WindowSkills:
    def __init__(self):
        print(">> Window Skills: ONLINE")

    # ─────────────────────────────────────────
    # WINDOW CONTROLS
    # ─────────────────────────────────────────
    def minimize_all(self):
        try:
            pyautogui.hotkey('win', 'd')
            return "All windows minimized."
        except Exception as e:
            return f"Could not minimize: {e}"

    def maximize_window(self):
        try:
            pyautogui.hotkey('win', 'up')
            return "Window maximized."
        except Exception as e:
            return f"Could not maximize: {e}"

    def minimize_window(self):
        try:
            pyautogui.hotkey('win', 'down')
            return "Window minimized."
        except Exception as e:
            return f"Could not minimize: {e}"

    def close_window(self):
        try:
            pyautogui.hotkey('alt', 'f4')
            return "Window closed."
        except Exception as e:
            return f"Could not close: {e}"

    def switch_window(self):
        try:
            pyautogui.hotkey('alt', 'tab')
            return "Switched window."
        except Exception as e:
            return f"Could not switch: {e}"

    def snap_left(self):
        try:
            pyautogui.hotkey('win', 'left')
            return "Window snapped left."
        except Exception as e:
            return f"Could not snap: {e}"

    def snap_right(self):
        try:
            pyautogui.hotkey('win', 'right')
            return "Window snapped right."
        except Exception as e:
            return f"Could not snap: {e}"

    def take_screenshot(self):
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            return f"Screenshot saved as {filename}."
        except Exception as e:
            return f"Could not take screenshot: {e}"

    def virtual_desktop_new(self):
        try:
            pyautogui.hotkey('win', 'ctrl', 'd')
            return "New virtual desktop created."
        except Exception as e:
            return f"Error: {e}"

    def task_view(self):
        try:
            pyautogui.hotkey('win', 'tab')
            return "Opening task view."
        except Exception as e:
            return f"Error: {e}"

    # ─────────────────────────────────────────
    # EXECUTE — VOICE COMMAND ROUTER
    # ─────────────────────────────────────────
    def execute(self, command):
        command_lower = command.lower()

        if any(w in command_lower for w in ["minimize all", "show desktop", "clear desktop"]):
            return self.minimize_all()

        if any(w in command_lower for w in ["maximize", "full screen", "fullscreen"]):
            return self.maximize_window()

        if "minimize" in command_lower and "all" not in command_lower:
            return self.minimize_window()

        if any(w in command_lower for w in ["close window", "close this"]):
            return self.close_window()

        if any(w in command_lower for w in ["switch window", "next window", "alt tab"]):
            return self.switch_window()

        if "snap left" in command_lower:
            return self.snap_left()

        if "snap right" in command_lower:
            return self.snap_right()

        if any(w in command_lower for w in ["screenshot", "screen capture", "capture screen"]):
            return self.take_screenshot()

        if any(w in command_lower for w in ["new desktop", "virtual desktop"]):
            return self.virtual_desktop_new()

        if any(w in command_lower for w in ["task view", "all windows"]):
            return self.task_view()

        return None