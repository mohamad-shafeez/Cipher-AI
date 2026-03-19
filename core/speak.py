# core/speak.py
import pyttsx3
import re
import config

class Speaker:
    def __init__(self):
        print(f">> Loading Voice for {config.ASSISTANT_NAME}...")
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 210)
        self.engine.setProperty('volume', 1.0)
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id)
        print(f">> Voice: ONLINE")

    def clean_text(self, text):
        # Remove punctuation that causes TTS pauses
        text = re.sub(r'[;:\-\*\#\|]', ' ', text)
        # Replace multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def speak(self, text):
        if not text:
            return
        print(f">> {config.ASSISTANT_NAME} speaking...")
        try:
            cleaned = self.clean_text(text)
            self.engine.say(cleaned)
            self.engine.runAndWait()
        except Exception as e:
            print(f">> Speech Error: {e}")