import os

class AgentRouter:
    def __init__(self, base_dir=r"D:\Visual Studio\Cipher-AI"):
        self.base_dir = base_dir
        self.ecosystem_path = os.path.join(base_dir, "agent_ecosystem")
        
        # Mapping standard keywords directly to the folder names and file names we copied inside agent_ecosystem
        self.agent_map = {
            "backend": ("engineering", "engineering-backend-architect.md"),
            "frontend": ("engineering", "engineering-frontend-developer.md"),
            "security": ("engineering", "engineering-security-engineer.md"),
            "database": ("engineering", "engineering-database-optimizer.md"),
            "tester": ("testing", "testing-performance-benchmarker.md"),
            "product": ("product", "product-product-manager.md")
        }

    def load_agent_blueprint(self, keyword):
        """Reads the specialized markdown profile rules from the agent_ecosystem folder."""
        keyword = keyword.lower().strip()
        if keyword not in self.agent_map:
            print(f"⚠️ [ROUTER] Role '{keyword}' not explicitly found in map. Using standard developer criteria.")
            return "You are an expert full-stack software engineer."
            
        division, file_name = self.agent_map[keyword]
        blueprint_path = os.path.join(self.ecosystem_path, division, file_name)
        
        # Fallback handling if names inside the repo vary slightly
        if not os.path.exists(blueprint_path):
            # Scan directory for a partial matching file name string
            division_dir = os.path.join(self.ecosystem_path, division)
            if os.path.exists(division_dir):
                for f in os.listdir(division_dir):
                    if keyword in f.lower():
                        blueprint_path = os.path.join(division_dir, f)
                        break

        if os.path.exists(blueprint_path):
            with open(blueprint_path, "r", encoding="utf-8") as f:
                print(f"🧠 [ROUTER] Loaded Persona: {os.path.basename(blueprint_path).upper()}")
                return f.read()
        else:
            print(f"❌ [ROUTER] Error: Couldn't read blueprint file at {blueprint_path}")
            return "You are an expert full-stack software engineer."

    def compile_execution_payload(self, keyword, target_project_path, target_file_name):
        """Bundles the persona guidelines with your selected external project file contents."""
        absolute_file_path = os.path.join(target_project_path, target_file_name)
        
        if not os.path.exists(absolute_file_path):
            print(f"❌ [ROUTER] File not found on disk at: {absolute_file_path}")
            return None

        # Load role prompts
        agent_rules = self.load_agent_blueprint(keyword)

        # Read the file data
        with open(absolute_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        # Build clean execution payload template string block
        payload = f"""### SYSTEM INSTRUCTIONS & IDENTITY
{agent_rules}

### FILE CONTEXT
- Absolute Path: {absolute_file_path}
- Target Filename: {target_file_name}

### RAW SOURCE CODE
"""
        return payload

    def request_user_permission(self, changes_summary):
        """An interactive type-and-edit authorization gate to handle code edits safely."""
        print("\n" + "!"*50)
        print("🚨 [CIPHER INTERACTIVE SECURITY GATE]")
        print(f"Proposed Changes Summary:\n{changes_summary}")
        print("!"*50)
        
        while True:
            choice = input("\nAuthorize Execution? [Y] Yes | [N] No | [A] Approve All Remaining: ").strip().upper()
            if choice in ['Y', 'N', 'A']:
                return choice
            print("Invalid input. Type Y, N, or A.")

    def execute_terminal_interface(self):
        """Launches a raw CLI workspace loop inside your prompt window."""
        print("\n" + "="*60)
        print("💻 WELCOME TO THE CIPHER MULTI-AGENT ROUTER CENTER")
        print("="*60)
        
        while True:
            print("\nAvailable Core Agent Roles: backend, frontend, security, database, tester, product")
            role = input("Select Agent Role (or type 'exit' to leave): ").strip().lower()
            if role == 'exit':
                break
                
            project_dir = input(r"Target Project Absolute Path (e.g. D:\Visual Studio\eventeasefinalfinal): ").strip()
            file_target = input("Target File Name (e.g. base.html): ").strip()

            print("\n⌛ Processing files and generating compilation payload context...")
            payload = self.compile_execution_payload(role, project_dir, file_target)

            if payload:
                print("\n" + "-"*40)
                print("✅ PAYLOAD GENERATION COMPLETE")
                print(f"Context Payload Size: {len(payload)} characters.")
                print("-"*40)
                
                # Fire the confirmation block simulation step
                approval = self.request_user_permission(f"Load '{role}' persona context onto file '{file_target}'")
                if approval == 'Y' or approval == 'A':
                    print(f"\n🚀 [EXECUTION AUTHORIZED] Context successfully packaged. Handing payload off to local worker sandbox lane.")
                else:
                    print("\n🛑 [EXECUTION ABORTED] User denied file payload compilation.")

if __name__ == "__main__":
    router = AgentRouter()
    router.execute_terminal_interface()