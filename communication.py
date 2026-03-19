# skills/communication.py
import webbrowser
import time
import pyautogui
import urllib.parse
import subprocess
import config

class CommunicationSkills:
    def __init__(self):
        print(">> Communication Skills: ONLINE")

        # Add your frequent contacts here
        self.contacts = {
            "mom": "+918217725385",
            "dad": "+919902752275",
            "shafeez": "+919513260316",
        }

    # ─────────────────────────────────────────
    # WHATSAPP
    # ─────────────────────────────────────────
    def send_whatsapp(self, contact, message):
        try:
            # Resolve contact name to number
            number = self.contacts.get(contact.lower())
            if not number:
                # Assume it's already a number
                number = contact.replace(" ", "")

            encoded_message = urllib.parse.quote(message)
            url = f"https://web.whatsapp.com/send?phone={number}&text={encoded_message}"
            webbrowser.open(url)

            # Wait for WhatsApp Web to load
            time.sleep(6)

            # Press Enter to send
            pyautogui.press("enter")
            return f"WhatsApp message sent to {contact}, sir."

        except Exception as e:
            return f"Could not send WhatsApp message: {e}"

    def open_whatsapp(self, contact=None):
        try:
            if contact:
                number = self.contacts.get(contact.lower(), contact)
                url = f"https://web.whatsapp.com/send?phone={number}"
            else:
                url = "https://web.whatsapp.com"
            webbrowser.open(url)
            return f"Opening WhatsApp{' for ' + contact if contact else ''}."
        except Exception as e:
            return f"Could not open WhatsApp: {e}"

    # ─────────────────────────────────────────
    # EMAIL
    # ─────────────────────────────────────────
    def open_gmail(self):
        try:
            webbrowser.open("https://mail.google.com")
            return "Opening Gmail, sir."
        except Exception as e:
            return f"Could not open Gmail: {e}"

    def compose_email(self, to=None, subject=None, body=None):
        try:
            params = []
            if to:
                params.append(f"to={urllib.parse.quote(to)}")
            if subject:
                params.append(f"subject={urllib.parse.quote(subject)}")
            if body:
                params.append(f"body={urllib.parse.quote(body)}")

            query = "&".join(params)
            url = f"https://mail.google.com/mail/?view=cm&{query}"
            webbrowser.open(url)
            return "Opening Gmail compose window, sir."
        except Exception as e:
            return f"Could not compose email: {e}"

    # ─────────────────────────────────────────
    # CALLS (WhatsApp Web)
    # ─────────────────────────────────────────
    def make_call(self, contact):
        try:
            number = self.contacts.get(contact.lower(), contact)
            url = f"https://web.whatsapp.com/send?phone={number}"
            webbrowser.open(url)
            time.sleep(6)
            # Click call button using keyboard shortcut
            pyautogui.hotkey("alt", "shift", "v")  # Video call shortcut
            return f"Initiating WhatsApp call to {contact}, sir."
        except Exception as e:
            return f"Could not make call: {e}"

    # ─────────────────────────────────────────
    # EXECUTE — VOICE COMMAND ROUTER
    # ─────────────────────────────────────────
    def execute(self, command):
        command_lower = command.lower()

        # Send WhatsApp message
        # "send message to mom saying I'll be late"
        if any(w in command_lower for w in ["send message", "whatsapp", "message to", "text"]):
            contact = None
            message = None

            # Extract contact
            for phrase in ["send message to", "whatsapp", "message to", "text"]:
                if phrase in command_lower:
                    rest = command_lower.split(phrase)[-1].strip()
                    # Split on "saying" or "that"
                    for splitter in ["saying", "that", "and say"]:
                        if splitter in rest:
                            parts = rest.split(splitter, 1)
                            contact = parts[0].strip()
                            message = parts[1].strip() if len(parts) > 1 else "Hello"
                            break
                    if not contact:
                        contact = rest.strip()
                        message = "Hello"
                    break

            if contact:
                return self.send_whatsapp(contact, message)

        # Make a call
        if any(w in command_lower for w in ["call", "phone", "ring"]):
            contact = command_lower
            for phrase in ["call", "phone", "ring", "whatsapp call to", "call to"]:
                contact = contact.replace(phrase, "").strip()
            if contact:
                return self.make_call(contact)

        # Open WhatsApp
        if "open whatsapp" in command_lower:
            contact = command_lower.replace("open whatsapp", "").strip()
            return self.open_whatsapp(contact if contact else None)

        # Gmail
        if any(w in command_lower for w in ["open gmail", "check email", "open email"]):
            return self.open_gmail()

        # Compose email
        # "compose email to someone@gmail.com"
        if any(w in command_lower for w in ["compose email", "write email", "send email"]):
            rest = command_lower
            for phrase in ["compose email to", "write email to", "send email to"]:
                rest = rest.replace(phrase, "").strip()
            return self.compose_email(to=rest if rest else None)

        return None