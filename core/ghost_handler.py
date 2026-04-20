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
        with sr.Microphone() as source:
            while True:
                try:
                    audio = r.listen(source, phrase_time_limit=2)
                    text = r.recognize_google(audio).lower()
                    if self.wake_word in text:
                        self.activate_cipher()
                except:
                    pass

    def activate_cipher(self):
        if not self.active:
            self.active = True
            greeting = get_royal_greeting() # The badass welcome
            self.speaker.speak(greeting)
            
            # Now transition to full voice loop
            self.start_voice_session()

    def start_voice_session(self):
        # This keeps the mic open until you say "Close" or "Go to sleep"
        print(">> Ghost Mode: ACTIVE")
        while self.active:
            command = self.agent.listen_voice() # Use your existing voice listener
            if any(w in command for w in ["close cipher", "go to sleep", "dismissed"]):
                self.speaker.speak("Understood, Shafeez. Returning to the shadows.")
                self.active = False
            else:
                self.agent.execute(command)

# Launch both triggers in background threads
ghost = GhostAssistant()
threading.Thread(target=ghost.listen_for_hotkey, daemon=True).start()
threading.Thread(target=ghost.listen_for_wake_word, daemon=True).start()