# core/live_mode.py — CIPHER OS (Fast Path Engine)
# ============================================================

from core.hud_server import HUDServer
from core.llm_interface import LocalLLM
import config

class LiveTalkEngine:
    def __init__(self, orchestrator_callback, tts_engine):
        self.orchestrator_callback = orchestrator_callback
        self.tts = tts_engine
        self.memory = []
        # Use fastest local model
        self.fast_model = "qwen2.5-coder:1.5b"
        
    def process_voice(self, transcript, active_directory=None):
        """The ultra-low-latency conversation loop."""
        print(f"⚡ [LIVETALK]: Hearing -> '{transcript}'")
        HUDServer.push_log(f"💬 LIVETALK: {transcript}")
        
        clean_text = transcript.lower().strip()

        # 💻 PC App Automation Hook
        if "open" in clean_text and "phone" not in clean_text and "mobile" not in clean_text:
            # Extracts the app name right after the word 'open'
            app_target = clean_text.split("open")[-1].strip().replace(",", "").replace(".", "")
            print(f"🦾 [FAST PATH]: Executing local system shortcut target: {app_target}")
            HUDServer.push_log(f"🦾 FAST PATH: Opening local app: {app_target}")

            # 1. TALK INSTANTLY: High-priority voice event for immediate response
            from core.event_bus import EventBus, Event
            EventBus().publish(Event("voice.speak", {"text": f"Opening {app_target}"}))

            # 2. Execute the app launcher instantly
            from skills.system_operator_skill import SystemOperatorSkill
            SystemOperatorSkill().execute({"intent": "system.app.open", "target": app_target})

            # 3. Return immediately so the heavy LLM never processes this command
            return

        # 📱 Mobile ADB Automation Hook
        if "phone open" in clean_text or "mobile open" in clean_text:
            # Extracts the mobile app target name
            app_target = clean_text.split("open")[-1].strip().replace(".", "")
            print(f"🦾 [FAST PATH]: Routing ADB mobile package target: {app_target}")
            HUDServer.push_log(f"🦾 FAST PATH: Opening mobile app package: {app_target}")

            # 1. TALK INSTANTLY: High-priority voice event for immediate response
            from core.event_bus import EventBus, Event
            EventBus().publish(Event("voice.speak", {"text": f"Opening {app_target} on mobile"}))

            # 2. Execute the mobile app launcher instantly
            from skills.system_operator_skill import SystemOperatorSkill
            SystemOperatorSkill().execute({"intent": "mobile.app.open", "target": app_target})

            # 3. Return immediately so the heavy LLM never processes this command
            return
        
        # 1. SMART INTENT ESCALATION (The Bridge)
        # We do a micro-check: Is this a command or a chat?
        escalation_keywords = ["open", "play", "schedule", "code", "search", "fix", "launch"]
        if any(word in transcript.lower() for word in escalation_keywords):
            print("🔄 [LIVETALK]: Command detected. Escalating to Sovereign Mode...")

            # Speak immediately while the heavy orchestrator boots up
            from core.event_bus import EventBus, Event
            EventBus().publish(Event("voice.speak", {"text": "On it."}))

            # Silently route to the heavy orchestrator without blocking
            self.orchestrator_callback(transcript, active_directory)
            return

        # 2. FAST CHAT (No Swarm, No Graph, Just Talk)
        self.memory.append({"role": "user", "content": transcript})
        
        # Keep context window strictly to the last 10 exchanges for speed
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]
            
        system_prompt = (
            "You are Cipher, an ultra-fast, conversational AI. "
            "Keep responses extremely concise, natural, and conversational. "
            "Do not use markdown. Speak like a human."
        )
        
        # Fast LLM Call
        response = LocalLLM.generate(
            prompt=str(self.memory),
            system_prompt=system_prompt,
            model=self.fast_model
        )
        
        self.memory.append({"role": "assistant", "content": response})
        
        # 3. STREAM TO VOICE
        print(f"🗣️ [CIPHER]: {response}")
        self.tts.speak(response)
