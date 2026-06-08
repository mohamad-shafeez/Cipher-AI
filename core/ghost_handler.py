import keyboard
import speech_recognition as sr
import threading
from core.speak import CipherSpeak
from core.agent import CipherAgent

class GhostAssistant:
    def __init__(self):
        self.active = False
        self.wake_word = "cipher"
        self.speaker = CipherSpeak()
        self.agent = CipherAgent()
        self.hotkey = "ctrl+space"
        
    def listen_for_hotkey(self):
        # The 2-key combo trigger
        keyboard.add_hotkey(self.hotkey, self.activate_cipher)
        keyboard.wait()

    def listen_for_wake_word(self):
        # Battery-efficient background listening
        r = sr.Recognizer()
        r.dynamic_energy_threshold = False
        r.energy_threshold = 1500
        with sr.Microphone() as source:
            while True:
                try:
                    audio = r.listen(source, phrase_time_limit=2)
                    text = r.recognize_google(audio).lower()
                    if self.wake_word in text:
                        self.activate_cipher()
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    pass
                except Exception:
                    pass

    def activate_cipher(self):
        if not self.active:
            self.active = True
            try:
                from skills.hello import HelloSkill
            except ModuleNotFoundError:
                from skills._archived.hello import HelloSkill
            royal_welcome = HelloSkill().get_royal_greeting()
            greeting = royal_welcome.get('clean', '') if isinstance(royal_welcome, dict) else str(royal_welcome)
            self.speaker.speak(greeting)
            
            # Now transition to full voice loop
            self.start_voice_session()

    def start_voice_session(self):
        from core.listen import Listener
        ear = Listener()
        # This keeps the mic open until you say "Close" or "Go to sleep"
        print(">> Ghost Mode: ACTIVE")
        while self.active:
            command = ear.listen()
            if any(w in command.lower() for w in ["close cipher", "go to sleep", "dismissed"]):
                self.speaker.speak("Understood, Shafeez. Returning to the shadows.")
                self.active = False
            elif command.strip():
                response = self.agent.run(command)
                if response:
                    text_to_speak = response.get("message", "") if isinstance(response, dict) else response
                    self.speaker.speak(text_to_speak)

# Launch both triggers in background threads
ghost = GhostAssistant()
threading.Thread(target=ghost.listen_for_hotkey, daemon=True).start()
threading.Thread(target=ghost.listen_for_wake_word, daemon=True).start()