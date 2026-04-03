import ollama
import config
import psutil
import datetime
import os
import re
import google.generativeai as genai  # NEW: Gemini Import
from dotenv import load_dotenv       # NEW: To read your .env

load_dotenv()

class Brain:
    def __init__(self):
        self.model = config.LLM_MODEL
        self.history = []
        
        # --- NEW: GEMINI INITIALIZATION ---
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            # Using Gemini 1.5 Flash for the fastest response in 2026
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            print(">> Neural Brain: Gemini Cloud Fallback ACTIVE")
        else:
            self.gemini_model = None
            print(">> Neural Brain: Gemini Key missing in .env. Fallback DISABLED.")

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

        # 1. ADD USER TO HISTORY
        self.history.append({'role': 'user', 'content': user_text})
        recent_history = self.history[-6:]

        # 2. ATTEMPT LOCAL THINKING (OLLAMA)
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    *recent_history
                ],
                options=options
            )
            reply = response['message']['content']

        except Exception as e:
            # 3. FALLBACK TO CLOUD THINKING (GEMINI)
            if self.gemini_model:
                print(f">> [Brain] Ollama offline. Routing to Gemini Neural Link...")
                # Format a single prompt for Gemini since it handles history differently
                full_prompt = f"{system_prompt}\n\nRecent History:\n{recent_history}\n\nUser: {user_text}"
                
                try:
                    gemini_resp = self.gemini_model.generate_content(full_prompt)
                    reply = gemini_resp.text
                except Exception as g_err:
                    return f"Neural Error: Both Ollama and Gemini are unreachable. {g_err}"
            else:
                return "Brain Error. Is Ollama running? (No Gemini key found for fallback)"

        # 4. CLEAN AND STORE REPLY (Shared logic for both models)
        reply = re.sub(r'[;:\-\*\#\|]', ' ', reply)
        reply = re.sub(r'\s+', ' ', reply).strip()
        self.history.append({'role': 'assistant', 'content': reply})
        return reply