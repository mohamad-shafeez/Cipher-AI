# skills/mobile.py
import subprocess
import webbrowser
import urllib.parse
import time
import pyautogui
import config

class MobileSkill:
    def __init__(self):
        self.adb = "adb"
        self.contacts = {
            "mom": "+91XXXXXXXXXX",
            "dad": "+91XXXXXXXXXX",
        }
        print(">> Mobile Skills: ONLINE")

    # ─────────────────────────────────────────
    # ADB HELPERS
    # ─────────────────────────────────────────
    def adb_command(self, command):
        try:
            result = subprocess.run(
                f"{self.adb} {command}",
                shell=True, capture_output=True, text=True
            )
            return result.stdout.strip()
        except Exception as e:
            return f"ADB Error: {e}"

    def adb_tap(self, x, y):
        self.adb_command(f"shell input tap {x} {y}")

    def adb_swipe(self, x1, y1, x2, y2, duration=300):
        self.adb_command(f"shell input swipe {x1} {y1} {x2} {y2} {duration}")

    def adb_key(self, keycode):
        self.adb_command(f"shell input keyevent {keycode}")

    def adb_text(self, text):
        text = text.replace(" ", "%s")
        self.adb_command(f"shell input text '{text}'")

    # ─────────────────────────────────────────
    # APPS LAUNCHER
    # ─────────────────────────────────────────
    def launch_app(self, app_name):
        apps = {
            "whatsapp":   "com.whatsapp",
            "instagram":  "com.instagram.android",
            "youtube":    "com.google.android.youtube",
            "spotify":    "com.spotify.music",
            "gmail":      "com.google.android.gm",
            "maps":       "com.google.android.apps.maps",
            "chrome":     "com.android.chrome",
            "camera":     "com.android.camera2",
            "settings":   "com.android.settings",
            "facebook":   "com.facebook.katana",
            "twitter":    "com.twitter.android",
            "telegram":   "org.telegram.messenger",
            "snapchat":   "com.snapchat.android",
            "netflix":    "com.netflix.mediaclient",
            "phone":      "com.google.android.dialer",
            "messages":   "com.google.android.apps.messaging",
            "photos":     "com.google.android.apps.photos",
            "files":      "com.google.android.documentsui",
            "clock":      "com.google.android.deskclock",
            "calculator": "com.google.android.calculator",
        }
        package = apps.get(app_name.lower())
        if package:
            self.adb_command(f"shell monkey -p {package} -c android.intent.category.LAUNCHER 1")
            return f"Opening {app_name} on your phone."
        return None  # ← returns None so other skills can try

    # ─────────────────────────────────────────
    # CALLS
    # ─────────────────────────────────────────
    def make_call(self, contact):
        number = self.contacts.get(contact.lower(), contact)
        self.adb_command(f"shell am start -a android.intent.action.CALL -d tel:{number}")
        return f"Calling {contact} on your phone."

    def end_call(self):
        self.adb_key("6")
        return "Call ended."

    # ─────────────────────────────────────────
    # SMS
    # ─────────────────────────────────────────
    def send_sms(self, contact, message):
        number = self.contacts.get(contact.lower(), contact)
        self.adb_command(
            f"shell am start -a android.intent.action.SENDTO "
            f"-d sms:{number} --es sms_body '{message}' --ez exit_on_sent true"
        )
        time.sleep(2)
        self.adb_key("66")
        return f"SMS sent to {contact}."

    # ─────────────────────────────────────────
    # WHATSAPP (Web)
    # ─────────────────────────────────────────
    def whatsapp_message(self, contact, message):
        number = self.contacts.get(contact.lower(), contact)
        encoded = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?phone={number}&text={encoded}"
        webbrowser.open(url)
        time.sleep(6)
        pyautogui.press("enter")
        return f"WhatsApp message sent to {contact}."

    # ─────────────────────────────────────────
    # CAMERA
    # ─────────────────────────────────────────
    def open_camera(self):
        return self.launch_app("camera")

    def take_photo(self):
        self.open_camera()
        time.sleep(2)
        self.adb_key("27")
        return "Photo taken on your phone."

    def start_video(self):
        self.open_camera()
        time.sleep(2)
        self.adb_tap(540, 1800)
        return "Video recording started."

    # ─────────────────────────────────────────
    # PHONE CONTROLS
    # ─────────────────────────────────────────
    def set_volume(self, level):
        level = max(0, min(15, int(int(level) * 15 / 100)))
        for _ in range(15):
            self.adb_key("25")
        for _ in range(level):
            self.adb_key("24")
        return f"Phone volume set to {level * 7}%."

    def flashlight_on(self):
        self.adb_command("shell cmd flashlight enable 1")
         # Alternative method if above fails
        self.adb_command("shell settings put secure flashlight_enabled 1")
        return "Flashlight turned on."

    def flashlight_off(self):
         self.adb_command("shell cmd flashlight disable 0")
         self.adb_command("shell settings put secure flashlight_enabled 0")
         return "Flashlight turned off."

    def set_alarm(self, time_str):
        hour, minute = time_str.split(":")
        self.adb_command(
            f"shell am start -a android.intent.action.SET_ALARM "
            f"--ei android.intent.extra.alarm.HOUR {hour} "
            f"--ei android.intent.extra.alarm.MINUTES {minute} "
            f"--ez android.intent.extra.alarm.SKIP_UI true"
        )
        return f"Alarm set for {time_str} on your phone."

    def hotspot_on(self):
        self.adb_command("shell svc wifi enable")
        return "Hotspot toggled. Check your phone settings."

    def get_battery(self):
        result = self.adb_command("shell dumpsys battery")
        for line in result.splitlines():
            if "level" in line:
                level = line.strip().split(":")[-1].strip()
                return f"Phone battery is at {level} percent."
        return "Could not read phone battery."

    def lock_phone(self):
        self.adb_command("shell input keyevent KEYCODE_SLEEP")
        return "Phone locked."

    def unlock_phone(self):
        self.adb_key("26")
        time.sleep(0.5)
        self.adb_swipe(540, 1500, 540, 800, 300)
        return "Phone unlocked."

    def navigate_maps(self, destination):
        encoded = urllib.parse.quote(destination)
        self.adb_command(
            f"shell am start -a android.intent.action.VIEW "
            f"-d 'google.navigation:q={encoded}'"
        )
        return f"Navigating to {destination} on your phone."

    # ─────────────────────────────────────────
    # EXECUTE — VOICE COMMAND ROUTER
    # ─────────────────────────────────────────
    def execute(self, command):
        command_lower = command.lower()

        # ── 1. BATTERY FIRST (before call triggers) ──
        if any(w in command_lower for w in [
    "phone battery", "mobile battery", "battery phone",
    "one battery", "fo battery", "on battery"  # ← mic mishearing aliases
]):
            return self.get_battery()

        # ── 2. FLASHLIGHT (expanded aliases for mic mishearing) ──
        if any(w in command_lower for w in [
            "flashlight", "torch", "flash light",
            "last light", "flesh light", "fast light",
            "past light", "flash"
        ]):
            if "off" in command_lower:
                return self.flashlight_off()
            return self.flashlight_on()

        # ── 3. PHONE APPS (always open on phone) ──
        phone_apps = [
            "instagram", "whatsapp", "telegram", "snapchat",
            "tiktok", "spotify", "netflix", "maps", "camera",
            "youtube", "gmail", "facebook", "twitter", "calculator",
            "clock", "messages", "photos", "files", "settings"
        ]
        if any(w in command_lower for w in ["open", "launch", "start"]):
            for app in phone_apps:
                if app in command_lower:
                    return self.launch_app(app)

        # ── 4. CALLS (removed "phone" to avoid battery conflict) ──
        if any(w in command_lower for w in ["call", "ring", "dial"]):
            if "end" in command_lower or "hang" in command_lower:
                return self.end_call()
            contact = command_lower
            for phrase in ["call", "ring", "dial", "mobile"]:
                contact = contact.replace(phrase, "").strip()
            # Clean punctuation from contact name
            contact = contact.replace(",", "").replace(".", "").strip()
            if contact:
                return self.make_call(contact)

        # ── 5. SMS ──
        if any(w in command_lower for w in ["sms", "text message", "send sms"]):
            parts = command_lower.split("to")
            if len(parts) > 1:
                rest = parts[1].strip()
                for splitter in ["saying", "that", "message"]:
                    if splitter in rest:
                        contact, message = rest.split(splitter, 1)
                        return self.send_sms(contact.strip(), message.strip())
            return "Who should I SMS and what message?"

        # ── 6. WHATSAPP ──
        if any(w in command_lower for w in ["whatsapp", "send message"]):
            parts = command_lower.split("to")
            if len(parts) > 1:
                rest = parts[1].strip()
                for splitter in ["saying", "that"]:
                    if splitter in rest:
                        contact, message = rest.split(splitter, 1)
                        return self.whatsapp_message(contact.strip(), message.strip())

        # ── 7. CAMERA ──
        if "take photo" in command_lower or "take picture" in command_lower:
            return self.take_photo()
        if "record video" in command_lower or "start video" in command_lower:
            return self.start_video()
        if "camera" in command_lower:
            return self.open_camera()

        # ── 8. ALARM ──
        if "alarm" in command_lower or "wake me" in command_lower:
            words = command_lower.split()
            for word in words:
                if ":" in word:
                    return self.set_alarm(word)
            return "What time should I set the alarm for?"

        # ── 9. NAVIGATION ──
        if any(w in command_lower for w in ["navigate", "directions to", "take me to"]):
            dest = command_lower
            for phrase in ["navigate to", "directions to", "take me to", "navigate"]:
                dest = dest.replace(phrase, "").strip()
            if dest:
                return self.navigate_maps(dest)

        # ── 10. OTHER PHONE CONTROLS ──
        if "lock phone" in command_lower:
            return self.lock_phone()
        if "unlock phone" in command_lower:
            return self.unlock_phone()
        if "hotspot" in command_lower:
            return self.hotspot_on()
        if "phone volume" in command_lower:
            words = command_lower.split()
            for word in words:
                if word.isdigit():
                    return self.set_volume(word)

        return None