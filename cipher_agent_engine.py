import os
import time
import re
import pygetwindow as gw

class CipherAgentEngine:
    def __init__(self, base_dir=r"D:\Visual Studio\Cipher-AI"):
        self.base_dir = base_dir
        self.ecosystem_path = os.path.join(base_dir, "agent_ecosystem")
        
        # Matrix of search roots where you keep your development files
        self.search_roots = [
            r"D:\Visual Studio",
            r"D:",
            r"C:\Users\MOHAMAD SHAFEEZ\Desktop"
        ]
        
        self.current_project_name = None
        self.current_project_path = None
        self.current_active_file = None

        # FULL 144-AGENT ECOSYSTEM MATRIX (All 12 Divisions)
        self.agent_universe = {
            # 1. ENGINEERING DIVISION
            "frontend": ("engineering", "engineering-frontend-developer.md"),
            "backend": ("engineering", "engineering-backend-architect.md"),
            "mobile": ("engineering", "engineering-mobile-app-builder.md"),
            "ai_engineer": ("engineering", "engineering-ai-engineer.md"),
            "devops": ("engineering", "engineering-devops-automator.md"),
            "prototyper": ("engineering", "engineering-rapid-prototyper.md"),
            "senior_dev": ("engineering", "engineering-senior-developer.md"),
            "filament": ("engineering", "engineering-filament-optimization-specialist.md"),
            "security": ("engineering", "engineering-security-engineer.md"),
            "autonomous": ("engineering", "engineering-autonomous-optimization-architect.md"),
            "firmware": ("engineering", "engineering-embedded-firmware-engineer.md"),
            "incident": ("engineering", "engineering-incident-response-commander.md"),
            "solidity": ("engineering", "engineering-solidity-smart-contract-engineer.md"),
            "onboarding": ("engineering", "engineering-codebase-onboarding-engineer.md"),
            "writer": ("engineering", "engineering-technical-writer.md"),
            "threat": ("engineering", "engineering-threat-detection-engineer.md"),
            "wechat": ("engineering", "engineering-wechat-mini-program-developer.md"),
            "reviewer": ("engineering", "engineering-code-reviewer.md"),
            "database": ("engineering", "engineering-database-optimizer.md"),
            "git": ("engineering", "engineering-git-workflow-master.md"),
            "architect": ("engineering", "engineering-software-architect.md"),
            "sre": ("engineering", "engineering-sre.md"),
            "remediation": ("engineering", "engineering-ai-data-remediation-engineer.md"),
            "data_eng": ("engineering", "engineering-data-engineer.md"),
            "feishu": ("engineering", "engineering-feishu-integration-developer.md"),
            "cms": ("engineering", "engineering-cms-developer.md"),
            "email": ("engineering", "engineering-email-intelligence-engineer.md"),
            "voice_ai": ("engineering", "engineering-voice-ai-integration-engineer.md"),

            # 2. DESIGN DIVISION
            "ui": ("design", "design-ui-designer.md"),
            "ux_research": ("design", "design-ux-researcher.md"),
            "ux_architect": ("design", "design-ux-architect.md"),
            "brand": ("design", "design-brand-guardian.md"),
            "storyteller": ("design", "design-visual-storyteller.md"),
            "whimsy": ("design", "design-whimsy-injector.md"),
            "prompt_eng": ("design", "design-image-prompt-engineer.md"),
            "inclusive": ("design", "design-inclusive-visuals-specialist.md"),

            # 3. PAID MEDIA DIVISION
            "ppc": ("paid-media", "paid-media-ppc-campaign-strategist.md"),
            "query_analyst": ("paid-media", "paid-media-search-query-analyst.md"),
            "auditor": ("paid-media", "paid-media-paid-media-auditor.md"),
            "tracking": ("paid-media", "paid-media-tracking-measurement-specialist.md"),
            "creative": ("paid-media", "paid-media-ad-creative-strategist.md"),
            "programmatic": ("paid-media", "paid-media-programmatic-display-buyer.md"),
            "social_strat": ("paid-media", "paid-media-paid-social-strategist.md"),

            # 4. SALES DIVISION
            "outbound": ("sales", "sales-outbound-strategist.md"),
            "discovery": ("sales", "sales-discovery-coach.md"),
            "deal": ("sales", "sales-deal-strategist.md"),
            "sales_eng": ("sales", "sales-sales-engineer.md"),
            "proposal": ("sales", "sales-proposal-strategist.md"),
            "pipeline": ("sales", "sales-pipeline-analyst.md"),
            "account_strat": ("sales", "sales-account-strategist.md"),
            "sales_coach": ("sales", "sales-sales-coach.md"),
            "outreach": ("sales", "sales-sales-outreach.md"),

            # 5. MARKETING DIVISION
            "growth": ("marketing", "marketing-growth-hacker.md"),
            "content": ("marketing", "marketing-content-creator.md"),
            "twitter": ("marketing", "marketing-twitter-engager.md"),
            "tiktok": ("marketing", "marketing-tiktok-strategist.md"),
            "instagram": ("marketing", "marketing-instagram-curator.md"),
            "reddit": ("marketing", "marketing-reddit-community-builder.md"),
            "aso": ("marketing", "marketing-app-store-optimizer.md"),
            "social_media": ("marketing", "marketing-social-media-strategist.md"),
            "seo": ("marketing", "marketing-seo-specialist.md"),
            "linkedin": ("marketing", "marketing-linkedin-content-creator.md"),

            # 6. PRODUCT DIVISION
            "sprint": ("product", "product-sprint-prioritizer.md"),
            "trend": ("product", "product-trend-researcher.md"),
            "feedback": ("product", "product-feedback-synthesizer.md"),
            "nudge": ("product", "product-behavioral-nudge-engine.md"),
            "product_manager": ("product", "product-product-manager.md"),

            # 7. PROJECT MANAGEMENT DIVISION
            "producer": ("project-management", "project-management-studio-producer.md"),
            "shepherd": ("project-management", "project-management-project-shepherd.md"),
            "operations": ("project-management", "project-management-studio-operations.md"),
            "experiment": ("project-management", "project-management-experiment-tracker.md"),
            "pm": ("project-management", "project-management-senior-project-manager.md"),
            "jira": ("project-management", "project-management-jira-workflow-steward.md"),

            # 8. TESTING DIVISION
            "evidence": ("testing", "testing-evidence-collector.md"),
            "checker": ("testing", "testing-reality-checker.md"),
            "analyzer": ("testing", "testing-test-results-analyzer.md"),
            "benchmarker": ("testing", "testing-performance-benchmarker.md"),
            "api_tester": ("testing", "testing-api-tester.md"),
            "accessibility": ("testing", "testing-accessibility-auditor.md"),

            # 9. SUPPORT DIVISION
            "responder": ("support", "support-support-responder.md"),
            "reporter": ("support", "support-analytics-reporter.md"),
            "finance_track": ("support", "support-finance-tracker.md"),
            "maintainer": ("support", "support-infrastructure-maintainer.md"),
            "compliance": ("support", "support-legal-compliance-checker.md"),

            # 10. SPATIAL COMPUTING DIVISION
            "xr_ui": ("spatial-computing", "spatial-computing-xr-interface-architect.md"),
            "metal": ("spatial-computing", "spatial-computing-macos-spatial-metal-engineer.md"),
            "webxr": ("spatial-computing", "spatial-computing-xr-immersive-developer.md"),
            "visionos": ("spatial-computing", "spatial-computing-visionos-spatial-engineer.md"),

            # 11. SPECIALIZED DIVISION
            "orchestrator": ("specialized", "specialized-agents-orchestrator.md"),
            "mcp": ("specialized", "specialized-mcp-builder.md"),
            "doc_gen": ("specialized", "specialized-document-generator.md"),
            "advocate": ("specialized", "specialized-developer-advocate.md"),

            # 12. FINANCE DIVISION
            "controller": ("finance", "finance-bookkeeper-controller.md"),
            "analyst": ("finance", "finance-financial-analyst.md"),
            "fpa": ("finance", "finance-fpa-analyst.md"),
            "tax": ("finance", "finance-tax-strategist.md")
        }

    def scan_active_window(self):
        """Scans the active OS title layout and updates workspace targets."""
        try:
            active_window = gw.getActiveWindow()
            if not active_window:
                return

            window_title = active_window.title

            if "Visual Studio Code" in window_title:
                parts = window_title.split(" - ")
                if len(parts) >= 2:
                    project_name = parts[-2].strip().replace("● ", "")
                    active_file = parts[0].strip() if len(parts) > 2 else "Empty Workspace"

                    if project_name != self.current_project_name:
                        for root in self.search_roots:
                            potential_path = os.path.join(root, project_name)
                            if os.path.isdir(potential_path):
                                self.current_project_name = project_name
                                self.current_project_path = potential_path
                                self.current_active_file = active_file
                                return
        except Exception:
            pass

    def load_agent_blueprint(self, role_key):
        """Loads static rules from the ecosystem folder."""
        if role_key not in self.agent_universe:
            return "You are an expert full-stack developer architecture module."
            
        division, file_name = self.agent_universe[role_key]
        blueprint_path = os.path.join(self.ecosystem_path, division, file_name)
        
        if os.path.exists(blueprint_path):
            with open(blueprint_path, "r", encoding="utf-8") as f:
                print(f"🧠 [ENGINE] Context Loaded: {file_name.upper()}")
                return f.read()
        return "You are an expert software engineer."

    def automate_file_scaffolding(self, raw_model_response):
        """Parses response markers to physically write folders and files to your drive."""
        print(f"\n📁 [SCAFFOLDING] Writing code assets inside: {self.current_project_path}")
        
        pattern = re.compile(r"\[CREATE_FILE:\s*(.*?)\](.*?)\[END_FILE\]", re.DOTALL)
        matches = pattern.findall(raw_model_response)

        if not matches:
            print("⚠️ [SCAFFOLDING] Error: No valid [CREATE_FILE] code blocks found in response payload.")
            return

        for file_rel_path, content in matches:
            file_rel_path = file_rel_path.strip()
            absolute_dest_path = os.path.join(self.current_project_path, file_rel_path)
            
            dest_directory = os.path.dirname(absolute_dest_path)
            if not os.path.exists(dest_directory):
                os.makedirs(dest_directory, exist_ok=True)

            with open(absolute_dest_path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            print(f"⚡ [CREATED FILE FROM SCRATCH] -> {file_rel_path}")

    def execute_agent_task(self, role, prompt_input):
        """Processes target path confirmation and compiles real markdown execution payload maps."""
        # Force a fresh active window lookup check
        self.scan_active_window()

        print(f"\n🔍 Currently Tracked Location: {self.current_project_path}")
        confirm_path = input("Press [Enter] to use this path, or paste an explicit destination folder path: ").strip()
        
        if confirm_path:
            self.current_project_path = confirm_path
            self.current_project_name = os.path.basename(confirm_path)

        if not self.current_project_path or not os.path.exists(self.current_project_path):
            print("❌ [SYSTEM ERROR] Invalid target folder path location.")
            return

        agent_rules = self.load_agent_blueprint(role)

        # COMPILED MARKDOWN PAYLOAD MATRIX (Ready for your local inference call)
        compiled_payload = f"""
### AGENT OPERATIONAL PERSONA RULES
{agent_rules}

### USER AUTOMATION PROMPT
Instruction: {prompt_input}

### RUNTIME ENVIRONMENT FOCUS
- Target Directory: {self.current_project_path}

### MANDATORY REWRITING CONSTRAINTS
You must encapsulate code blocks using this exact format:
[CREATE_FILE: filename.ext]
// Code here
[END_FILE]
"""
        print(f"\n📝 [ROUTER] Context payload successfully compiled ({len(compiled_payload)} characters).")
        
        # NOTE: Once your local Ollama/Gemini API is ready, you will trade this mock string out 
        # for your live `response = ollama.generate(model='qwen', prompt=compiled_payload)` call!
        print("🤖 Generating code architecture setup block patterns...")
        
        mock_response_portfolio = """
Sure! Generating your custom responsive portfolio website design parameters:

[CREATE_FILE: index.html]
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Developer Portfolio Dashboard</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <header>
        <h2>Mohamad Shafeez</h2>
        <nav>📁 System Core Components</nav>
    </header>
    <section class="hero">
        <h1>Local Multi-Agent Orchestration Runtime</h1>
        <p>Production sandboxing, concurrent watchdog isolation loops, and predictive telemetry HUD pipelines.</p>
    </section>
    <section class="projects">
        <div class="card">🤖 Cipher OS Engine Core Dashboard</div>
        <div class="card">🛡️ SafeNav Predictive Hazard Router</div>
    </section>
</body>
</html>
[END_FILE]

[CREATE_FILE: css/styles.css]
body {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
}
header { display: flex; justify-content: space-between; border-bottom: 1px solid #30363d; }
.hero { text-align: center; padding: 60px 20px; }
.projects { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 40px; }
.card { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 6px; }
[END_FILE]
"""

        print("\n" + "!"*50)
        print("🚨 [CIPHER INTERACTIVE SECURITY GATE]")
        print(f"Agent '{role}' wants permission to build files inside '{self.current_project_path}'")
        print("!"*50)
        
        choice = input("\nAuthorize Complete Workspace Scaffolding? [Y] Yes | [N] No: ").strip().upper()
        if choice == "Y":
            self.automate_file_scaffolding(mock_response_portfolio)
        else:
            print("🛑 [ABORTED] File overwrite blocked by user.")

    def run_studio_terminal(self):
        print("\n" + "="*60)
        print("🎭 CIPHER OS: UNIFIED LOCAL MULTI-AGENT STUDIO RUNTIME")
        print("="*60)
        
        while True:
            self.scan_active_window()
            print(f"\n📡 Auto-Track Target: {self.current_project_name} -> {self.current_project_path}")
            
            role = input("Enter Agent Role (e.g. frontend, backend, security, whimsy) [or 'exit']: ").strip().lower()
            if role == "exit":
                break
                
            prompt_text = input("What do you want to build from scratch? (Prompt): ").strip()
            self.execute_agent_task(role, prompt_text)

if __name__ == "__main__":
    engine = CipherAgentEngine()
    engine.run_studio_terminal()