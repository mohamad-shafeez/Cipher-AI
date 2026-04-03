# core/fast_loader.py
# ============================================================
#   CIPHER FAST BOOT LOADER
#   Weaponizes multi-threading to boot the entire skill matrix
#   in parallel. Also pre-warms the LLM for instant response.
#
#   Usage in main.py:
#       from core.fast_loader import FastSkillLoader
#       skills = FastSkillLoader(max_workers=14)
#       skills.prewarm_ollama()
# ============================================================

import time
import threading
import importlib
import requests
import config
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Configuration ───────────────────────────────────────────
OLLAMA_URL   = f"{config.OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = config.LLM_MODEL
PREWARM_MSG  = "hi" # Minimal token payload to trigger VRAM load


# ── Skill Registry (Path, ClassName) ────────────────────────
# Order here determines priority in the command loop.
SKILL_REGISTRY = [
    # ── Core Skills ─────────────────────────────────────────
    ("skills.clock",               "ClockSkill"),
    ("skills.hello",               "HelloSkill"),
    ("skills.notes",               "NotesSkill"),
    ("skills.system",              "SystemSkill"),
    ("skills.browser",             "BrowserSkill"),
    ("skills.apps",                "AppsSkill"),
    ("skills.files",               "FilesSkill"),
    ("skills.mobile",              "MobileSkill"),
    ("skills.window",              "WindowSkill"),
    ("skills.media",               "MediaSkill"),
    ("skills.coding",              "CodingSkill"),
    ("skills.research",            "ResearchSkill"),

    # ── Advanced Skills ─────────────────────────────────────
    ("skills.media_forge",         "MediaForgeSkill"),
    ("skills.web_scout",           "WebScoutSkill"),
    ("skills.market_analyst",      "MarketAnalystSkill"),
    ("skills.email_pro",           "EmailProSkill"),
    ("skills.document_intel",      "DocumentIntelSkill"),
    ("skills.vector_memory",       "VectorMemorySkill"),
    ("skills.autonomous_debugger", "AutonomousDebuggerSkill"),
    ("skills.security_guardian",   "SecurityGuardianSkill"),
    ("skills.knowledge_forge",     "KnowledgeForgeSkill"),
    ("skills.network_pro",         "NetworkProSkill"),
    ("skills.system_monitor",      "SystemMonitorSkill"),
    ("skills.whatsapp_pro",        "WhatsappProSkill"),
    ("skills.scheduler",           "SchedulerSkill"),
    ("skills.study_vault",         "StudyVaultSkill"),
    ("skills.file_vault",          "FileVaultSkill"),
    ("skills.vision",              "VisionSkill"),
    ("skills.voice_neural",        "VoiceNeuralSkill"),
    ("skills.research_v2",         "ResearchV2Skill"),

    # ── Phase 4 Skills ──────────────────────────────────────
    ("skills.mobile_hotspot",      "MobileBridgeSkill"),
    ("skills.git_commander",       "GitCommanderSkill"),
    ("skills.process_manager",     "ProcessManagerSkill"),
    ("skills.env_manager",         "EnvManagerSkill"),
    ("skills.clipboard_sync",      "ClipboardSyncSkill"),
    ("skills.turbo_brain",         "TurboBrainSkill"),
]


def _load_one(module_path: str, class_name: str) -> object | None:
    """Helper: Dynamic import and instantiation."""
    try:
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        return cls()
    except Exception as e:
        print(f"  [FastLoader] ⚠ Failed to load {class_name}: {e}")
        return None


class FastSkillLoader:
    """
    The Parallel Brain. Replaces sequential loading to ensure
    Cipher is ready for action in under 2 seconds.
    """

    def __init__(self, max_workers: int = 12):
        self.skills: list = []
        self._load(max_workers)

    def _load(self, max_workers: int):
        t0 = time.perf_counter()
        print(f">> FastLoader: firing up {len(SKILL_REGISTRY)} skill modules...")

        results: dict[int, object] = {}

        # Utilizing ThreadPool to bypass I/O wait times during imports
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(_load_one, mod, cls): idx
                for idx, (mod, cls) in enumerate(SKILL_REGISTRY)
            }
            for future in as_completed(futures):
                idx = futures[future]
                obj = future.result()
                if obj is not None:
                    results[idx] = obj

        # Re-sort to maintain the priority order defined in the registry
        self.skills = [results[i] for i in sorted(results.keys())]

        elapsed = time.perf_counter() - t0
        print(f">> FastLoader: {len(self.skills)} skills synced in {elapsed:.2f}s")

    def run_skills(self, command: str) -> str | None:
        """Main skill execution loop with error isolation."""
        for skill in self.skills:
            try:
                result = skill.execute(command)
                if result:
                    return result
            except Exception as e:
                print(f"[Skill Error] {skill.__class__.__name__}: {e}")
        return None

    def prewarm_ollama(self):
        """Background thread to load the LLM weights into VRAM."""
        def _warm():
            try:
                t0 = time.perf_counter()
                print(f">> Ollama: Pre-warming {OLLAMA_MODEL}...")
                requests.post(
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": PREWARM_MSG,
                        "stream": False
                    },
                    timeout=60
                )
                print(f">> Ollama: Model weights cached in RAM ({time.perf_counter()-t0:.1f}s)")
            except Exception as e:
                print(f">> Ollama Pre-warm skipped: {e}")

        threading.Thread(target=_warm, daemon=True).start()

    def skill_names(self) -> list[str]:
        return [s.__class__.__name__ for s in self.skills]