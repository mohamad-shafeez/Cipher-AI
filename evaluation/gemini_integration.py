import os

import config
from core.hud_server import HUDServer
from core.llm_interface import LocalLLM


class GeminiBridge:
    @staticmethod
    def generate(system_prompt: str, prompt: str, model: str = None) -> str:
        if not getattr(config, "GEMINI_ENABLED", False):
            return LocalLLM.generate(system_prompt, prompt, model=model or getattr(config, "FRONTIER_MODEL", None))

        api_key = getattr(config, "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
        if not api_key:
            HUDServer.push_log("⚠️ Gemini integration disabled: missing API key. Falling back to Ollama frontier model.")
            return LocalLLM.generate(system_prompt, prompt, model=model or getattr(config, "FRONTIER_MODEL", None))

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            model_name = model or getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")
            if model_name == "gemini-1.5":
                model_name = "gemini-1.5-flash"

            model_instance = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            response = model_instance.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:
            HUDServer.push_log(f"⚠️ Gemini integration failed: {exc}. Falling back to local Ollama frontier model.")
            return LocalLLM.generate(system_prompt, prompt, model=model or getattr(config, "FRONTIER_MODEL", None))

    @staticmethod
    def generate_json(system_prompt: str, prompt: str, model: str = None) -> dict:
        import json
        if not getattr(config, "GEMINI_ENABLED", False):
            return None

        api_key = getattr(config, "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
        if not api_key:
            return None

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            model_name = model or getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")
            if model_name == "gemini-1.5":
                model_name = "gemini-1.5-flash"

            model_instance = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model_instance.generate_content(prompt)
            return json.loads(response.text.strip())
        except Exception as exc:
            HUDServer.push_log(f"⚠️ Gemini JSON generation failed: {exc}")
            return None
