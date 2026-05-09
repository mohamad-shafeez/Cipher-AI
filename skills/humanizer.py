# skills/humanizer.py
import re
import ollama

class HumanizerSkill:
    """
    Cipher Skill — The Humanizer
    Removes AI artifacts, copula avoidance, significance inflation, and formulaic 
    structures based on the 29 Wikipedia 'Signs of AI writing' patterns.
    """
    def __init__(self):
        self.voice_sample = None
        self.model = "deepseek-r1:1.5b" # Fast and capable for text editing
        print(">> Humanizer Skill: ONLINE (Anti-AI Detection Active)")

    def execute(self, command: str):
        cmd_lower = command.lower().strip()

        # Route 1: Voice Calibration (Learning your style)
        if cmd_lower.startswith("calibrate voice") or "sample of my writing" in cmd_lower:
            return self._calibrate_voice(command)

        # Route 2: Humanize Text
        if cmd_lower.startswith("humanize text") or cmd_lower.startswith("humanize this"):
            # Extract the text to humanize by removing the command trigger
            text_to_humanize = re.sub(r'^(humanize text|humanize this text|humanize this:?)\s*', '', command, flags=re.IGNORECASE).strip()
            if not text_to_humanize:
                return "Sir, please provide the text you would like me to humanize."
            
            return self._humanize(text_to_humanize)

        return None

    def _calibrate_voice(self, text: str) -> str:
        """Saves a sample of your writing to mimic your tone."""
        # Strip out the command prefix
        sample = re.sub(r'^(calibrate voice|here is a sample of my writing|sample of my writing:?)\s*', '', text, flags=re.IGNORECASE).strip()
        
        if len(sample) < 20:
            return "Sir, that sample is too short. Please provide at least 2-3 paragraphs of your natural writing."
            
        self.voice_sample = sample
        return "✅ Voice calibration complete. I have mapped your sentence rhythm, word choices, and quirks. Future humanized text will match this style."

    # --- Block 2 (The Audit Engine) will go here ---
    def _humanize(self, text: str) -> str:
        return "Block 2 pending... I am ready to receive the Audit Engine."
    
    # ── Block 2: The Audit Engine ──────────────────────────────────────────────
    def _humanize(self, text: str) -> str:
        """Executes the 2-pass Humanizer protocol using local Ollama."""
        print(">> Humanizer: Initiating 2-Pass Rewrite Protocol...")
        
        # Prepare the voice calibration context if it exists
        voice_context = ""
        if self.voice_sample:
            voice_context = (
                f"\n\nCRITICAL DIRECTIVE: Match this exact writing style, sentence rhythm, "
                f"and vocabulary choices from the user's calibration sample:\n"
                f"[USER SAMPLE START]\n{self.voice_sample}\n[USER SAMPLE END]\n"
            )

        # ── PASS 1: The Rule Engine ──
        pass_1_prompt = f"""
        You are an expert human editor. Rewrite the following text to completely remove all signs of AI generation.
        {voice_context}

        Enforce these anti-AI rules strictly:
        1. NO Significance Inflation: Remove phrases like "marking a pivotal moment", "transformative potential", "delving into".
        2. NO Copula Avoidance: Stop using "serves as", "features", "boasts". Use "is" and "has".
        3. NO AI Vocabulary: Ban "testament to", "landscape", "showcasing", "crucial", "seamless", "tapestry".
        4. NO Rule of Three: Stop grouping adjectives in threes (e.g., "innovation, inspiration, and insights").
        5. NO Sycophantic Tone or Chatbot Artifacts: Remove "Great question!", "I hope this helps!", "In conclusion".
        6. NO Filler/Hedging: Change "In order to" -> "To", "Due to the fact that" -> "Because".
        7. NO "Let's dive in" or "At its core": Just state the point directly.
        8. USE Active Voice: Name the actor. Keep it punchy and direct.

        Text to rewrite:
        {text}

        Output ONLY the rewritten text. No introductory or concluding remarks.
        """

        try:
            # Pass 1 Execution
            response_1 = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": pass_1_prompt}],
                options={"temperature": 0.4} # Low temperature for strict editing
            )
            draft = response_1["message"]["content"].strip()

            # ── PASS 2: The Final Audit ──
            print(">> Humanizer: Pass 1 complete. Initiating Pass 2 Audit...")
            pass_2_prompt = f"""
            You are a cynical, highly critical human editor. Read this draft and strip out any remaining 
            "AI-sounding" fluff, corporate speak, or flowery transitions. Make it sound like a real, 
            slightly blunt human wrote it on a Tuesday morning.
            {voice_context}

            Draft to audit:
            {draft}

            Output ONLY the final, polished human text. No markdown formatting unless it was in the original text.
            """

            response_2 = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": pass_2_prompt}],
                options={"temperature": 0.5} 
            )
            final_text = response_2["message"]["content"].strip()
            
            return f"**[Humanized Output]**\n\n{final_text}"

        except Exception as e:
            return f"⚠ Humanizer Error: Could not connect to the local model. Ensure Ollama is running. ({e})"