# core/skills_manager.py
# ============================================================
#   CIPHER SKILL MANAGER  (Full Registry)
#   All skills registered here. Order = priority.
#   FastSkillLoader (core/fast_loader.py) runs these in
#   parallel at boot — this file stays as the canonical
#   ordered list and fallback loader.
# ============================================================

# ── Core Skills ─────────────────────────────────────────────
from skills.vision             import VisionSkill
from skills.clock              import ClockSkill
from skills.hello              import HelloSkill
from skills.notes              import NotesSkill
from skills.system             import SystemSkill
from skills.browser            import BrowserSkill
from skills.apps               import AppsSkill
from skills.files              import FilesSkill
from skills.mobile             import MobileSkill
from skills.window             import WindowSkill
from skills.media              import MediaSkill
from skills.coding             import CodingSkill
from skills.research           import ResearchSkill

# ── Advanced Skills ──────────────────────────────────────────
from skills.media_forge        import MediaForgeSkill
from skills.web_scout          import WebScoutSkill
from skills.market_analyst     import MarketAnalystSkill
from skills.email_pro          import EmailProSkill
from skills.document_intel     import DocumentIntelSkill
from skills.vector_memory      import VectorMemorySkill
from skills.autonomous_debugger import AutonomousDebuggerSkill
from skills.security_guardian  import SecurityGuardianSkill
from skills.knowledge_forge    import KnowledgeForgeSkill
from skills.network_pro        import NetworkProSkill
from skills.system_monitor     import SystemMonitorSkill
from skills.whatsapp_pro       import WhatsappProSkill
from skills.scheduler          import SchedulerSkill
from skills.study_vault        import StudyVaultSkill
from skills.file_vault         import FileVaultSkill
from skills.voice_neural       import VoiceNeuralSkill
from skills.research_v2        import ResearchV2Skill

# ── NEW Skills (Phase 4) ─────────────────────────────────────
from skills.mobile_hotspot     import MobileBridgeSkill      # phone ↔ laptop bridge
from skills.git_commander      import GitCommanderSkill      # full git by voice
from skills.process_manager    import ProcessManagerSkill    # kill/list/restart procs
from skills.env_manager        import EnvManagerSkill        # .env CRUD by voice
from skills.clipboard_sync     import ClipboardSyncSkill     # clipboard phone ↔ laptop
from skills.turbo_brain        import TurboBrainSkill        # cache + speed control


class SkillManager:
    def __init__(self):
        self.skills = [

            # ── Core (high priority — fast match) ───────────
            VisionSkill(),
            ClockSkill(),
            HelloSkill(),
            NotesSkill(),
            SystemSkill(),
            BrowserSkill(),
            AppsSkill(),
            FilesSkill(),
            MobileSkill(),
            WindowSkill(),
            MediaSkill(),
            CodingSkill(),
            ResearchSkill(),

            # ── Advanced ─────────────────────────────────────
            MediaForgeSkill(),
            WebScoutSkill(),
            MarketAnalystSkill(),
            EmailProSkill(),
            DocumentIntelSkill(),
            VectorMemorySkill(),
            AutonomousDebuggerSkill(),
            SecurityGuardianSkill(),
            KnowledgeForgeSkill(),
            NetworkProSkill(),
            SystemMonitorSkill(),
            WhatsappProSkill(),
            SchedulerSkill(),
            StudyVaultSkill(),
            FileVaultSkill(),
            VoiceNeuralSkill(),
            ResearchV2Skill(),
            VisionSkill(),

            # ── New Phase 4 ───────────────────────────────────
            MobileBridgeSkill(),
            GitCommanderSkill(),
            ProcessManagerSkill(),
            EnvManagerSkill(),
            ClipboardSyncSkill(),
            TurboBrainSkill(),
        ]

    def run_skills(self, command: str) -> str | None:
        for skill in self.skills:
            try:
                result = skill.execute(command)
                if result:
                    return result
            except Exception as e:
                print(f"[Skill Error] {skill.__class__.__name__}: {e}")
        return None