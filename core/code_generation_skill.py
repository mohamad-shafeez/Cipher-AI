import os
import ast
from core.llm_interface import LocalLLM
from core.hud_server import HUDServer

class CodeGenerationSkill:
    def __init__(self):
        self.base_folder = "D:/Visual Studio/Cipher-AI/generated_code/"

    def execute(self, payload):
        user_command = payload.get("command", "").lower()

        # 1. Dynamically target the file from your voice text
        filename = "test.py"
        words = user_command.split()
        for word in words:
            if word.endswith(".py") or word.endswith(".js") or word.endswith(".html"):
                filename = word
                break

        target_file_path = os.path.join(self.base_folder, filename).replace("\\", "/")

        if not os.path.exists(target_file_path):
            HUDServer.push_log(f"❌ REPAIR ERROR: File not found at {target_file_path}")
            return False

        # 2. Read raw file content
        with open(target_file_path, 'r', encoding='utf-8') as file:
            source_code = file.read()

        # 3. Use local Python interpreter to scan for syntax errors
        is_syntax_error = False
        syntax_exception_details = ""

        try:
            ast.parse(source_code)
            HUDServer.push_log(f"🔍 [AST COMPILER]: Structure compiles perfectly. Checking for logical flaws...")
        except SyntaxError as syntax_err:
            is_syntax_error = True
            syntax_exception_details = f"Line {syntax_err.lineno}: {syntax_err.msg}\nCode block: {syntax_err.text}"
            HUDServer.push_log(f"⚠️ [AST COMPILER]: Found broken syntax on line {syntax_err.lineno}!")

        # 4. Give explicit, un-bottlenecked system instructions to the model
        if is_syntax_error:
            # Use 1.5b for fast syntax fixing with absolute rule constraint
            chosen_model = "qwen2.5-coder:1.5b"
            system_instruction = (
                "You are an automated code repair assistant. Your ONLY job is to output the corrected code. "
                "Fix the specific syntax error or typos provided. "
                "CRITICAL: Do not write a script to check for errors. Output the actual corrected code block. "
                "Return ONLY the executable code inside markdown code fences. No chat text."
            )
            prompt_payload = f"Syntax Error Details:\n{syntax_exception_details}\n\nOriginal Code:\n{source_code}"
        else:
            # If no syntax error, use 1.5b for logical thinking (fast demo mode)
            chosen_model = "qwen2.5-coder:1.5b"
            system_instruction = (
                "You are a code optimization assistant. The code has no syntax errors. "
                "Analyze the user's request and improve the code if needed. "
                "Return ONLY the executable code inside markdown code fences. No chat text."
            )
            prompt_payload = f"User Instruction: {user_command}\n\nSource Code Context:\n{source_code}"

        HUDServer.push_log(f"⚡ [ROUTING DIRECT]: Sending payload to {chosen_model}...")

        # 5. Call the local LLM directly, bypassing the complex multi-agent planner loops
        ai_raw_response = LocalLLM.generate(system_instruction, prompt_payload, model=chosen_model)

        if ai_raw_response:
            clean_code = ai_raw_response.replace("```python", "").replace("```", "").strip()

            with open(target_file_path, 'w', encoding='utf-8') as file:
                file.write(clean_code)

            HUDServer.push_log(f"💾 [FILE SYSTEM]: {filename} successfully patched and saved!")
            return True

        return False
