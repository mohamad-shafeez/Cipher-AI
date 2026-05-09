"""
Cipher Skill — WhatsApp Pro
Organ: The Communicator
Architecture: ADB Intent Engine + Regex NLP Parsing.
Bypasses the browser entirely to send messages silently via connected Android device.
"""

import os
import re
import urllib.parse
import json

class WhatsappProSkill:
    def __init__(self):
        self.contacts = {}
        self._load_contacts()
        print(">> WhatsApp Pro Skill: ONLINE (ADB Deep Link Active)")

    def _load_contacts(self):
        """Dynamically loads contacts from data/contacts.json if it exists."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, "data", "contacts.json")
        
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    self.contacts = json.load(f)
            else:
                # Fallback dictionary if JSON is missing
                self.contacts = {
                    "mom": "+91XXXXXXXXXX",
                    "dad": "+91XXXXXXXXXX",
                    "friend": "+91XXXXXXXXXX"
                }
        except Exception as e:
            print(f"[WhatsApp] Failed to load contacts JSON: {e}")

    def _extract_data(self, command: str):
        """User's superior regex parsing for natural conversational flow."""
        # Pattern 1: whatsapp [name/number] saying [message]
        match = re.search(r"whatsapp (.*?) saying (.*)", command)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Pattern 2: send whatsapp to [name/number] message [message]
        match = re.search(r"whatsapp to (.*?) message (.*)", command)
        if match:
            return match.group(1).strip(), match.group(2).strip()

        return None, None

    def execute(self, command: str) -> str | None:
        if not command:
            return None

        cmd = command.lower().strip()

        # Trigger check
        if "whatsapp" not in cmd:
            return None

        target, message = self._extract_data(cmd)

        if not target or not message:
            return "Sir, please specify the target and the message. For example: 'whatsapp mom saying hello'."

        # Resolve contact
        phone_number = self.contacts.get(target, target)

        if not phone_number.startswith("+") and not phone_number.isdigit():
            available = ", ".join(self.contacts.keys())
            return f"Sir, I do not have a contact saved for '{target}'. Available contacts are: {available}."

        print(f">> [WhatsApp Pro] Routing message to {target} via Mobile Bridge...")
        return self._send_via_adb(target, phone_number, message)

    def _send_via_adb(self, name: str, number: str, message: str) -> str:
        """Claude's instant, invisible ADB execution engine."""
        try:
            import subprocess
            
            clean_number = re.sub(r'[^\d+]', '', number)
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_number}&text={encoded_message}"

            adb_command = [
                "adb", "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", whatsapp_url
            ]

            # Fire the intent directly to the Android OS
            result = subprocess.run(adb_command, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                return f"Sir, I have routed the message to {name}. It is queued on your device."
            else:
                error = result.stderr.strip() or result.stdout.strip()
                return f"Sir, the ADB bridge failed: {error}. Please ensure your phone is connected."

        except subprocess.TimeoutExpired:
            return "Sir, the Mobile Bridge timed out. Your device may be sleeping."
        except FileNotFoundError:
            return "Sir, ADB is not installed or not in the system PATH."
        except Exception as e:
            return f"Sir, an unexpected error occurred in the Communicator protocol: {e}"