import os
import re
import ollama
from global_workspace_watcher import GlobalWorkspaceWatcher

class CipherHUDOrchestrator:
    def __init__(self, base_dir=r"D:\Visual Studio\Cipher-AI"):
        self.base_dir = base_dir
        self.ecosystem_path = os.path.join(base_dir, "agent_ecosystem")
        
        # Initialize our system-wide workspace watchdog tracking system
        self.watcher = GlobalWorkspaceWatcher()
        
        # We target your strongest local asset for high-end code generation loops
        self.model_name = "qwen2.5-coder:7b"
        
        # Basic mapping of division blueprints for the collaborative assembly line
        self.agent_profiles = {
            "product": os.path.join(self.ecosystem_path, "product", "product-product-manager.md"),
            "backend": os.path.join(self.ecosystem_path, "engineering", "engineering-backend-architect.md"),
            "frontend": os.path.join(self.ecosystem_path, "engineering", "engineering-frontend-developer.md"),
            "security": os.path.join(self.ecosystem_path, "engineering", "engineering-security-engineer.md")
        }

    def fetch_agent_rules(self, role):
        """Reads static system prompt guardrails out of the agent_ecosystem registry."""
        path = self.agent_profiles.get(role)
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return "You are an expert full-stack developer software agent."

    def execute_local_inference(self, system_prompt, user_prompt):
        """Streams raw generation contexts directly through your offline Ollama setup."""
        try:
            print(f"🤖 [OLLAMA] Processing task with {self.model_name}...")
            response = ollama.generate(
                model=self.model_name,
                system=system_prompt,
                prompt=user_prompt,
                options={
                    "temperature": 0.2, 
                    "num_ctx": 8192  # Expanded context window limits for large file frameworks
                }
            )
            return response['response']
        except Exception as e:
            return f"❌ [OLLAMA EXCEPTION] Pipeline processing failed: {str(e)}"

    def run_collaborative_chain(self, raw_user_prompt):
        """Runs an autonomous sequential round-table across multiple specialized expert roles."""
        # Force tracker loop to grab whatever project window you are currently working on in VS Code
        self.watcher.scan_active_window()
        target_path = self.watcher.current_project_path
        
        if not target_path:
            print("❌ [ORCHESTRATOR ERROR] No active workspace directory detected by the Watchdog.")
            return None

        print(f"\n🚀 [ENGINE] Starting Orchestrator Chain inside workspace: {target_path}")
        
        # STEP 1: Product Manager builds structural architecture strategies
        print("\n📋 [1/4] Consulting Product Manager for workspace setup parameters...")
        pm_rules = self.fetch_agent_rules("product")
        pm_prompt = f"Analyze the user's request and build a detailed list of required application files and folders to build: {raw_user_prompt}"
        blueprint_plan = self.execute_local_inference(pm_rules, pm_prompt)
        
        # STEP 2: Backend Architect constructs server code based on the layout blueprint
        print("\n⚙️ [2/4] Deploying Backend Architect to build core architecture APIs...")
        backend_rules = self.fetch_agent_rules("backend")
        backend_prompt = f"Using this development blueprint:\n{blueprint_plan}\n\nGenerate the complete backend source architecture files. You MUST wrap every file using the format: [CREATE_FILE: path/filename.ext] ...code... [END_FILE]"
        backend_output = self.execute_local_inference(backend_rules, backend_prompt)
        
        # STEP 3: Frontend Developer constructs client layout blocks attached to backend data structures
        print("\n🎨 [3/4] Deploying Frontend Developer to construct client-side interface components...")
        frontend_rules = self.fetch_agent_rules("frontend")
        frontend_prompt = f"Using these server elements as your data hooks:\n{backend_output}\n\nGenerate the matching frontend user interface layout files. Wrap files cleanly using: [CREATE_FILE: path/filename.ext] ...code... [END_FILE]"
        frontend_output = self.execute_local_inference(frontend_rules, frontend_prompt)
        
        # STEP 4: Security Engineer audits performance patterns and patches exploits
        print("\n🛡️ [4/4] Activating Security Engineer for syntax checks and patch hardening...")
        security_rules = self.fetch_agent_rules("security")
        security_prompt = f"Review the generated code assets for vulnerabilities or bugs. Deliver the final, polished code payload keeping our strict formatting tokens intact.\n\nBackend files:\n{backend_output}\n\nFrontend files:\n{frontend_output}"
        finalized_package = self.execute_local_inference(security_rules, security_prompt)

        # Bundle everything into a state telemetry map block ready to feed directly into your Telemetry HUD UI layout
        telemetry_payload = {
            "target_path": target_path,
            "project_name": self.watcher.current_project_name,
            "proposed_plan": blueprint_plan,
            "final_source_code": finalized_package
        }
        return telemetry_payload

    def commit_package_to_disk(self, telemetry_payload):
        """Parses response data fields and writes directories and file streams straight onto your drive partitions."""
        target_path = telemetry_payload["target_path"]
        payload_data = telemetry_payload["final_source_code"]
        
        print(f"\n📁 [SCAFFOLDING LAYER] Writing files cleanly inside target path: {target_path}")
        
        pattern = re.compile(r"\[CREATE_FILE:\s*(.*?)\](.*?)\[END_FILE\]", re.DOTALL)
        matches = pattern.findall(payload_data)

        if not matches:
            print("⚠️ [SCAFFOLDING ERROR] No structural code markers detected in model processing outputs.")
            return False

        for file_rel_path, content in matches:
            file_rel_path = file_rel_path.strip()
            absolute_dest_path = os.path.join(target_path, file_rel_path)
            
            # Auto-generate nested directories if they do not exist
            dest_directory = os.path.dirname(absolute_dest_path)
            os.makedirs(dest_directory, exist_ok=True)

            with open(absolute_dest_path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            print(f"🧱 [CREATED ASSET SUCCESSFULLY] Written: {file_rel_path}")
        return True

    def run_studio_loop(self):
        print("\n" + "="*60)
        print("🎭 CIPHER OS: INTERACTIVE MULTI-AGENT RUNTIME HUB")
        print("="*60)
        print("💡 Open any target folder in VS Code, then run commands here.")
        
        while True:
            # Continually update window detection flags
            self.watcher.scan_active_window()
            print(f"\n📡 Active Target Project Window: {self.watcher.current_project_name}")
            
            user_input = input("What complex application do you want to build? (or type 'exit'): ").strip()
            if user_input.lower() == 'exit':
                break
                
            if not user_input:
                continue
                
            # Fire off the complete backend multi-agent chain across your Ollama engine parameters
            hud_state_data = self.run_collaborative_chain(user_input)
            
            if hud_state_data:
                print("\n" + "-"*50)
                print("📋 GENERATED BLUEPRINT STRATEGY METRICS:")
                print(hud_state_data["proposed_plan"])
                print("-"*50)
                
                # Interactive UI confirmation simulation gate block
                choice = input(f"\nAuthorize Cipher to write this multi-agent code structure into '{hud_state_data['project_name']}'? [Y/N]: ").strip().upper()
                if choice == "Y":
                    self.commit_package_to_disk(hud_state_data)
                else:
                    print("🔒 Write protection active. No code parameters touched on disk storage arrays.")

if __name__ == "__main__":
    orchestrator = CipherHUDOrchestrator()
    orchestrator.run_studio_loop()