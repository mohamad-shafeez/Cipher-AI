import os
import re
import requests
import json
import config
from core.hud_server import HUDServer

class GenerationCore:
    def __init__(self):
        self.model = getattr(config, "LLM_MODEL", "qwen2.5-coder:1.5b")
        self.url = f"{getattr(config, 'OLLAMA_URL', 'http://localhost:11434')}/api/generate"

    def generate_new_module(self, creation_intent: str, target_directory: str) -> bool:
        """
        Interprets a creation prompt, determines the ideal file structure, 
        and autonomously builds and writes the source code modules to disk.
        """
        print(f"🏗️ [CREATOR ENGINE]: Synthesizing new asset inside: {target_directory}")
        HUDServer.push_log(f"🏗️ CREATOR: Initiating asset synthesis for template request.")

        # 1. Ask the model to determine the perfect filename and extension for this intent
        naming_prompt = f"""Analyze this software creation intent: "{creation_intent}"
Determine the single best filename and extension for this script (e.g., scraper.py, server.js, index.html).
Output ONLY the raw filename string. No quotes, no markdown, no explanation."""

        try:
            name_response = requests.post(
                self.url,
                json={"model": self.model, "prompt": naming_prompt, "stream": False},
                timeout=30
            )
            if name_response.status_code != 200:
                return False

            filename = name_response.json().get("response", "").strip().replace("`", "").replace('"', '')
            if not filename or "." not in filename:
                filename = "generated_script.py"  # Safe defensive fallback

            filepath = os.path.join(target_directory, filename).replace("\\", "/")
            
            # 2. Generate the actual structural code contents
            generation_prompt = f"""You are Cipher's internal Creator Engine. Build a fully functional, production-ready source code file based on this user specifications request:

User Request: "{creation_intent}"
Target Filename: {filename}

Provide clean, secure, well-commented code. Output ONLY the raw source code block inside appropriate markdown code delimiters. No conversation, no introductory text."""

            print(f"🧠 [CREATOR INFERENCE]: Generating blueprint architecture tokens for {filename}...")
            code_response = requests.post(
                self.url,
                json={"model": self.model, "prompt": generation_prompt, "stream": False},
                timeout=120
            )

            if code_response.status_code == 200:
                raw_generated_text = code_response.json().get("response", "").strip()
                
                # Strip markdown wrappers cleanly to preserve structural language tokens
                file_ext = os.path.splitext(filename)[1].lower().replace(".", "")
                if f"```{file_ext}" in raw_generated_text:
                    clean_code = raw_generated_text.split(f"```{file_ext}")[1].split("```")[0].strip()
                elif "```" in raw_generated_text:
                    clean_code = raw_generated_text.split("```")[1].split("```")[0].strip()
                else:
                    clean_code = raw_generated_text

                # 3. Autonomously commit the freshly minted source code file to disk
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(clean_code)

                print(f"✨ [CREATOR SUCCESS]: Autonomous module built successfully at: {filepath}")
                HUDServer.push_log(f"✨ CREATOR SUCCESS: Dropped new module {filename} into workspace.")
                return True

        except Exception as e:
            print(f"❌ [CREATOR CRASH]: Failed to manifest asset generation loop: {str(e)}")
            HUDServer.push_log(f"🛑 CREATOR ERROR: Asset synthesis failed: {str(e)}")
            
        return False
