# skills/coding.py
import re
import subprocess
import os
import webbrowser
import json
from pathlib import Path
from typing import Optional

import config
from google import genai


class CodingSkill:
    """
    Neural-powered coding assistant with AI-driven code generation, 
    auto‑scanning, and bug fixing using Gemini 1.5 Flash.
    """

    def __init__(self):
        # Initialise Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(">> CodingSkill WARNING: GEMINI_API_KEY environment variable not set.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)

        # Keep original boilerplates and snippets for backward compatibility
        self.boilerplates = {
            "python": '# Python Script\n\ndef main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()\n',
            "javascript": '// JavaScript File\n\nfunction main() {\n    console.log("Hello, World!");\n}\n\nmain();\n',
            "react": 'import React from "react";\n\nconst App = () => {\n    return (\n        <div>\n            <h1>Hello World</h1>\n        </div>\n    );\n};\n\nexport default App;\n',
            "node": 'const express = require("express");\nconst app = express();\nconst PORT = 3000;\n\napp.get("/", (req, res) => {\n    res.send("Hello World");\n});\n\napp.listen(PORT, () => console.log(`Server running on port ${PORT}`));\n',
            "html": '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Document</title>\n</head>\n<body>\n    <h1>Hello World</h1>\n</body>\n</html>\n',
            "fastapi": 'from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"message": "Hello World"}\n',
            "django": 'from django.http import HttpResponse\n\ndef index(request):\n    return HttpResponse("Hello World")\n',
        }

        self.code_snippets = {
            "for loop": "for i in range(10):\n    print(i)",
            "while loop": "while True:\n    break",
            "function": "def my_function(param):\n    return param",
            "class": "class MyClass:\n    def __init__(self):\n        pass",
            "api request": 'import requests\n\nresponse = requests.get("https://api.example.com")\nprint(response.json())',
            "read file": 'with open("file.txt", "r") as f:\n    content = f.read()\nprint(content)',
            "write file": 'with open("file.txt", "w") as f:\n    f.write("Hello World")',
            "list comprehension": "result = [x for x in range(10) if x % 2 == 0]",
            "try except": "try:\n    pass\nexcept Exception as e:\n    print(f'Error: {e}')",
            "dictionary": 'my_dict = {"key": "value"}\nprint(my_dict.get("key"))',
        }

    # ========== NEW NEURAL METHODS ==========

    def execute_swarm(self, prompt: str) -> str:
        """
        Sends a prompt to Gemini 1.5 Flash, expecting a JSON object
        where keys are filenames and values are code content.
        Creates every file listed in the JSON.
        """
        if self.client is None:
            return "Error: Gemini API key not configured. Please set GEMINI_API_KEY."

        system_instruction = (
            "Return a JSON object where keys are filenames and values are the code content. "
            "Only output valid JSON, no extra text."
        )
        full_prompt = f"{system_instruction}\n\nUser request: {prompt}"

        try:
            print(">> [Swarm] Consulting the Neural Architect...")
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )
            
            raw = response.text.strip()
            # Surgical JSON extraction
            json_match = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
            if json_match:
                raw = json_match.group(0)
            else:
                return f"Neural Error: Could not parse project structure."

            files_map = json.loads(raw)
            if not isinstance(files_map, dict):
                return "AI did not return a valid project map."

            created = []
            print(f">> [Swarm] Generating {len(files_map)} files...")
            
            for filename, code in files_map.items():
                # --- FIX: Directory creation MUST be inside the loop ---
                directory = os.path.dirname(filename)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(code)
                created.append(filename)

            if created:
                return f"Successfully created {len(created)} file(s): {', '.join(created)}"
            else:
                return "No files were generated."

        except json.JSONDecodeError as e:
            return f"Failed to parse AI response as JSON: {e}\nRaw response: {raw[:200]}"
        except Exception as e:
            return f"Error during swarm generation: {e}"

    def auto_scan(self) -> str:
        """
        Lists all files and directories in the current working directory.
        """
        try:
            items = os.listdir('.')
            files = [f for f in items if os.path.isfile(f)]
            dirs = [d for d in items if os.path.isdir(d)]

            result = f"📁 Current directory: {os.getcwd()}\n"
            if dirs:
                result += f"\n📂 Directories ({len(dirs)}):\n  " + "\n  ".join(dirs)
            if files:
                result += f"\n\n📄 Files ({len(files)}):\n  " + "\n  ".join(files)
            if not files and not dirs:
                result += "\nDirectory is empty."
            return result
        except Exception as e:
            return f"Error scanning directory: {e}"

    def fix_my_code(self, filename: str) -> str:
        """
        Reads the content of the given file, sends it to Gemini for bug fixing,
        and overwrites the file with the corrected version.
        """
        if self.client is None:
            return "Error: Gemini API key not configured. Please set GEMINI_API_KEY."

        path = Path(filename)
        if not path.exists():
            return f"File '{filename}' not found."

        try:
            with open(filename, "r", encoding="utf-8") as f:
                original_code = f.read()

            fix_prompt = (
                f"Fix the bugs in the following code. Return only the corrected code, "
                f"no explanations, no markdown formatting.\n\n```\n{original_code}\n```"
            )

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=fix_prompt
            )
            fixed_code = response.text.strip()

            # Remove possible markdown code fences
            if fixed_code.startswith("```"):
                lines = fixed_code.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                fixed_code = "\n".join(lines).strip()

            # Overwrite the file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(fixed_code)

            return f"✅ Fixed '{filename}' and saved corrections."

        except Exception as e:
            return f"Error fixing code: {e}"

    # ========== LEGACY METHODS (kept for compatibility) ==========

    def open_vscode(self, target=None):
        try:
            if target:
                path = Path(target)
                if path.exists():
                    subprocess.Popen(["code", str(path)])
                    return f"Opening {target} in VS Code."
                else:
                    subprocess.Popen(["code", "."])
                    return f"Could not find {target}. Opening current directory in VS Code."
            else:
                subprocess.Popen(["code", "."])
                return "Opening VS Code."
        except Exception as e:
            return f"Could not open VS Code: {e}"

    def run_file(self, filename):
        try:
            path = Path(filename)
            if not path.exists():
                return f"File {filename} not found."
            
            if filename.endswith(".py"):
                result = subprocess.run(
                    ["python", filename],
                    capture_output=True, text=True, timeout=30
                )
                output = result.stdout or result.stderr
                return f"Ran {filename}. Output: {output[:100] if output else 'No output.'}"
            
            elif filename.endswith(".js"):
                result = subprocess.run(
                    ["node", filename],
                    capture_output=True, text=True, timeout=30
                )
                output = result.stdout or result.stderr
                return f"Ran {filename}. Output: {output[:100] if output else 'No output.'}"
            
            else:
                return f"I can only run Python and JavaScript files right now."
        except subprocess.TimeoutExpired:
            return "Script timed out after 30 seconds."
        except Exception as e:
            return f"Error running file: {e}"

    def create_file(self, command):
        try:
            # Extract language and filename from command
            language = None
            filename = None

            for lang in self.boilerplates:
                if lang in command:
                    language = lang
                    break

            # Extract filename if mentioned
            words = command.split()
            for i, word in enumerate(words):
                if word in ["called", "named", "file"]:
                    if i + 1 < len(words):
                        filename = words[i + 1]
                        break

            if not language:
                return "Please specify a language. Say: create a python file called main."

            # Build filename
            extensions = {
                "python": ".py", "javascript": ".js", "react": ".jsx",
                "node": ".js", "html": ".html", "fastapi": ".py", "django": ".py"
            }
            ext = extensions.get(language, ".txt")
            filename = filename if filename else f"new_file{ext}"
            if not filename.endswith(ext):
                filename += ext

            # Write boilerplate
            with open(filename, "w") as f:
                f.write(self.boilerplates[language])

            subprocess.Popen(["code", filename])
            return f"Created {filename} with {language} boilerplate and opened in VS Code."

        except Exception as e:
            return f"Error creating file: {e}"

    def search_stackoverflow(self, query):
        try:
            search_url = f"https://stackoverflow.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return f"Searching Stack Overflow for {query}."
        except Exception as e:
            return f"Error searching Stack Overflow: {e}"

    def write_code(self, command):
        for snippet_name, code in self.code_snippets.items():
            if snippet_name in command:
                # Copy to clipboard
                try:
                    import pyperclip
                    pyperclip.copy(code)
                    return f"Copied {snippet_name} to your clipboard. Paste it anywhere."
                except:
                    return f"Here is the {snippet_name}: {code}"
        return None

    def execute(self, command):
        command_lower = command.lower()

        # Route to neural swarm if user asks for code generation
        if any(w in command_lower for w in ["generate code", "create project", "build an app", "write multiple files"]):
            # Extract the actual prompt after the command words
            prompt = command
            for prefix in ["generate code", "create project", "build an app", "write multiple files"]:
                if command_lower.startswith(prefix):
                    prompt = command[len(prefix):].strip()
                    break
            return self.execute_swarm(prompt)

        # Auto-scan command
        if any(w in command_lower for w in ["scan directory", "list files", "what files", "auto scan"]):
            return self.auto_scan()

        # Fix my code command
        if any(w in command_lower for w in ["fix my code", "debug file", "correct errors in"]):
            words = command.split()
            for i, w in enumerate(words):
                if w.endswith(".py") or w.endswith(".js") or w.endswith(".html") or w.endswith(".css"):
                    return self.fix_my_code(w)
            return "Please specify a file to fix, e.g., 'fix my code main.py'"

        # Open VS Code
        if any(w in command_lower for w in ["open vs code", "open vscode", "launch vs code", "open editor"]):
            target = command.replace("open vs code", "").replace("open vscode", "").replace("launch vs code", "").replace("open editor", "").strip()
            return self.open_vscode(target if target else None)

        # Run a file
        if any(w in command_lower for w in ["run", "execute", "start"]):
            words = command.split()
            for word in words:
                if word.endswith(".py") or word.endswith(".js"):
                    return self.run_file(word)

        # Create a file (legacy boilerplate)
        if any(w in command_lower for w in ["create", "make", "new"]) and any(w in command_lower for w in ["file", "script", "component"]):
            return self.create_file(command)

        # Search Stack Overflow
        if any(w in command_lower for w in ["stack overflow", "stackoverflow", "search error", "how to fix"]):
            query = command.replace("search stack overflow for", "").replace("stack overflow", "").replace("how to fix", "").strip()
            return self.search_stackoverflow(query)

        # Write code snippet (legacy)
        if any(w in command_lower for w in ["write", "give me", "show me", "code for"]):
            result = self.write_code(command)
            if result:
                return result

        return None