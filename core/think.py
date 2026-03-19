# core/think.py
import ollama
import config
import psutil
import datetime

class Brain:
    def __init__(self):
        self.model = config.LLM_MODEL
        self.history = []

    def get_system_context(self):
        battery = psutil.sensors_battery()
        battery_info = (
            f"{battery.percent:.0f}% {'charging' if battery.power_plugged else 'not charging'}"
            if battery else "unavailable"
        )
        time_now = datetime.datetime.now().strftime("%I:%M %p")
        date_now = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Current time: {time_now}. Today: {date_now}. Battery: {battery_info}."

    def think(self, user_text):
        system_prompt = (
            f"You are {config.ASSISTANT_NAME}, a voice assistant on a Windows PC. "
            "Answer in ONE short sentence only. English only. "
            "Never make up information. Never roleplay. "
            "If you don't know something, say I don't know. "
            "Never use punctuation marks like semicolons colons or dashes. "
            f"{self.get_system_context()}"
        )

        options = {
            'num_predict': 30,
            'temperature': 0.1,
            'top_k': 10,
            'top_p': 0.3
        }

        try:
            self.history.append({'role': 'user', 'content': user_text})
            recent_history = self.history[-6:]

            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    *recent_history
                ],
                options=options
            )

            reply = response['message']['content']
            # Clean punctuation before returning
            import re
            reply = re.sub(r'[;:\-\*\#\|]', ' ', reply)
            reply = re.sub(r'\s+', ' ', reply).strip()
            self.history.append({'role': 'assistant', 'content': reply})
            return reply

        except Exception as e:
            return f"Brain Error. Is Ollama running?"