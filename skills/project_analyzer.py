import os
import re
import requests
import config

class ProjectAnalyzerSkill:
    """
    Project Vault Architecture: Analyzes entire project directories, 
    generates permanent markdown ledgers, and initiates iterative swarm bug-fixing.
    """
    def __init__(self):
        self.projects_dir = "projects"
        os.makedirs(self.projects_dir, exist_ok=True)
        print(">> ProjectAnalyzerSkill: ONLINE (Vault Architecture Ready)")

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()
        
        # --- TRIGGER 1: Analyze Project ---
        if cmd.startswith("analyze project"):
            project_name = cmd[len("analyze project"):].strip()
            if not project_name:
                return "Sir, please specify a project name to analyze."
            
            # Directory Traversal
            target_dir = None
            if os.path.exists("cipher_projects"):
                for root_dir, dirs, files in os.walk("cipher_projects"):
                    if project_name.lower() in os.path.basename(root_dir).lower():
                        target_dir = root_dir
                        break
            
            if not target_dir:
                print(f"[PROJECT ANALYZER] Cannot find project '{project_name}' automatically.")
                target_dir = input(">>> Please provide the absolute path to the project: ").strip()
                
            if not target_dir or not os.path.exists(target_dir):
                return "Analysis aborted. Valid project path not provided."
                
            return self._analyze_project(project_name, target_dir)

        # --- TRIGGER 2: Iterative Fix Loop ---
        if cmd.startswith("fix project") or cmd.startswith("repair project"):
            project_name = cmd.replace("fix project", "").replace("repair project", "").strip()
            return self._execute_iterative_fix(project_name)

        return None

    def _analyze_project(self, name: str, path: str) -> str:
        code_content = []
        for root_dir, dirs, files in os.walk(path):
            if any(skip in root_dir for skip in ["node_modules", ".git", "venv", "__pycache__"]):
                continue
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.py', '.js', '.ts', '.html', '.css', '.java', '.cpp', '.c']:
                    filepath = os.path.join(root_dir, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        code_content.append(f"--- File: {filepath} ---\n{content}")
                    except Exception:
                        pass
        
        if not code_content:
            return "No valid code files found in the specified directory."

        combined_code = "\n".join(code_content)
        prompt = (
            f"You are an expert system architect and bug hunter. Analyze the following project files:\n"
            f"{combined_code[:30000]}\n\n"
            "Generate a markdown ledger strictly containing:\n"
            "A) Architecture Summary\n"
            "B) Checklist of Detected Errors/Bugs. YOU MUST USE EXACTLY THIS FORMAT: '- [ ] [Filename]: [Error Description]'\n"
            "C) Proposed Fix Logic\n"
        )

        try:
            print(f">> [Analyzer] Analyzing project '{name}' with 7B Model...")
            response = requests.post(f"{config.OLLAMA_BASE_URL}/api/generate", json={
                "model": "qwen2.5-coder:7b",
                "prompt": prompt,
                "stream": False,
                "keep_alive": "2m"
            }, timeout=120)
            
            ledger = response.json().get("response", "").strip()
            
            proj_folder = os.path.join(self.projects_dir, name)
            os.makedirs(proj_folder, exist_ok=True)
            ledger_path = os.path.join(proj_folder, f"{name}_project_fix.md")
            
            with open(ledger_path, "w", encoding="utf-8") as f:
                f.write(ledger)
                
            return f"Project analyzed successfully. Ledger saved to {ledger_path}. Say 'fix project {name}' to begin repairs."
        except Exception as e:
            return f"Project analysis failed: {e}"

    def _execute_iterative_fix(self, name: str) -> str:
        ledger_path = os.path.join(self.projects_dir, name, f"{name}_project_fix.md")
        if not os.path.exists(ledger_path):
            return f"No ledger found for project '{name}'. Please analyze it first."

        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger_content = f.read()

        # Parse tasks
        tasks = re.findall(r'- \[ \] \[(.+?)\]: (.+)', ledger_content)
        if not tasks:
            return "No pending bugs found in the ledger."

        print(f">> [Swarm] Iterative Execution Initiated for {name}.")
        
        fixed_count = 0
        from skills.autonomous_coder import SurgicalExecutor, ContextEngine, MemoryVault
        # We temporarily mock the Vault and Engine for the 7B execution loop
        vault = MemoryVault(name)
        ctx = ContextEngine("cipher_projects") # generic root
        executor = SurgicalExecutor(vault=vault)

        for filepath, error_desc in tasks:
            print(f"\n[ITERATIVE SWARM] Sir, I have formulated a fix for: {filepath}")
            print(f"Detected Error: {error_desc}")
            approval = input(">>> Shall I apply it? (yes/no): ").strip().lower()
            
            if approval in ['y', 'yes', 'proceed', 'allow all']:
                print(f">> Applying patch via 7B coder...")
                result = executor.fix_single({
                    "file": filepath,
                    "error": error_desc
                }, ctx)
                
                print(f">> Result: {result}")
                
                if "Fixed" in result or "✅" in result:
                    # Mark as fixed in ledger
                    ledger_content = ledger_content.replace(
                        f"- [ ] [{filepath}]: {error_desc}",
                        f"- [X] [{filepath}]: {error_desc} (FIXED)"
                    )
                    fixed_count += 1
            else:
                print(">> Patch rejected. Skipping to next file.")

        # Save updated ledger
        with open(ledger_path, "w", encoding="utf-8") as f:
            f.write(ledger_content)

        return f"Iterative loop complete. {fixed_count} file(s) repaired and ledger updated."
