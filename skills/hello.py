# skills/hello.py
import datetime
import random
import config

class HelloSkills:
    def __init__(self):
        print(">> Hello Skills: ONLINE")

        self.greetings = [
            f"Online and ready, sir. What do you need?",
            f"At your service. What shall we do today?",
            f"Systems active. How can I assist you, sir?",
            f"Good to hear you. What's the mission?",
        ]

        self.compliments_responses = [
            "Thank you, sir. I was built to impress.",
            "Appreciated. Now, what can I do for you?",
            "Kind of you to say. Let's get to work.",
        ]

        self.jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "I would tell you a joke about UDP, but you might not get it.",
            "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
            "Why did the developer go broke? Because he used up all his cache.",
            "There are 10 types of people. Those who understand binary and those who don't.",
        ]

        self.motivations = [
            "Every expert was once a beginner. Keep pushing.",
            "Code. Break. Fix. Repeat. That's how legends are made.",
            "The best error message is the one that never shows up. Keep building.",
            "One bug at a time. You've got this, sir.",
        ]

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────
    def get_greeting_by_time(self):
        hour = datetime.datetime.now().hour
        if hour < 12:
            return "Good morning"
        elif hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"

    def get_time(self):
        return datetime.datetime.now().strftime("%I:%M %p")

    def get_date(self):
        return datetime.datetime.now().strftime("%A, %B %d, %Y")

    def get_uptime_greeting(self):
        period = self.get_greeting_by_time()
        return f"{period}, sir. {random.choice(self.greetings)}"

    # ─────────────────────────────────────────
    # EXECUTE — VOICE COMMAND ROUTER
    # ─────────────────────────────────────────
    def execute(self, command):
        command = command.lower()

        # Greetings
        if any(w in command for w in ["hello", "hi", "hey", "what's up", "wassup", "yo", "good morning", "good evening", "good afternoon"]):
            return self.get_uptime_greeting()

        # How are you
        if any(w in command for w in ["how are you", "how do you feel", "you okay", "you good"]):
            return random.choice([
                "Running at full capacity, sir. All systems nominal.",
                "Fully operational. Better than ever.",
                "No errors detected. I am functioning perfectly.",
            ])

        # Compliments
        if any(w in command for w in ["good job", "well done", "nice", "great", "awesome", "you're amazing", "smart"]):
            return random.choice(self.compliments_responses)

        # Jokes
        if any(w in command for w in ["joke", "funny", "make me laugh", "tell me something funny"]):
            return random.choice(self.jokes)

        # Motivation
        if any(w in command for w in ["motivate", "inspire", "encourage", "i give up", "i'm tired", "motivation"]):
            return random.choice(self.motivations)

        # Who are you
        if any(w in command for w in ["who are you", "what are you", "introduce yourself", "your name"]):
            return (
                f"I am {config.ASSISTANT_NAME}, your personal AI assistant. "
                "Built with Faster-Whisper, Ollama, and a modular skill system. "
                "I can control your system, search the web, write code, and much more."
            )

        # What can you do
        if any(w in command for w in ["what can you do", "your skills", "capabilities", "help", "features"]):
            return (
                f"I can control your system, search Wikipedia and Google, "
                "open websites, run code files, create boilerplate, take screenshots, "
                "check battery and time, and have intelligent conversations using a local AI brain."
            )

        # Goodbye
        if any(w in command for w in ["bye", "goodbye", "see you", "exit", "quit", "go offline", "shut down apex"]):
            return random.choice([
                f"Goodbye, sir. {config.ASSISTANT_NAME} going offline.",
                "Signing off. Call me when you need me.",
                "Offline mode activated. Stay sharp, sir.",
            ])

        # Thanks
        if any(w in command for w in ["thanks", "thank you", "appreciate"]):
            return random.choice([
                "Always, sir.",
                "That's what I'm here for.",
                "Anytime. What else do you need?",
            ])

        return None