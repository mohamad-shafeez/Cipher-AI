"""Contract tests for Cipher's core runtime pieces.

These tests exercise the memory tiers, watchdog callback path, dynamic skill
loader, persona catalog, and the credential-handling regression that removed a
hard-coded Telegram token from the entrypoint.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cognitive_memory_working_and_episodic_tiers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from core.cognitive_memory import CognitiveMemory
    from core.event_bus import Event

    CognitiveMemory._instance = None
    memory = CognitiveMemory()

    memory.update_working_context("current_focus", "unit-test")
    assert memory.get_working_context()["current_focus"] == "unit-test"

    memory.log_episode(
        Event(
            type="os.app.launched",
            source="pytest",
            data={"application": "notepad"},
        )
    )

    assert memory.get_working_context()["last_launched_app"] == "notepad"
    episodes = memory.recall_recent_episodes(limit=5)
    assert any(row[1] == "os.app.launched" for row in episodes)
    assert (tmp_path / "storage" / "cognitive_timeline.db").is_file()


def test_memory_sql_round_trip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from core.memory_sql import MemorySQL

    memory = MemorySQL()
    memory.add_log("what is running?", "system_operator", "notepad is open")
    context = memory.get_recent_context(limit=3)

    assert "what is running?" in context
    assert "notepad is open" in context


def test_watchdog_triggers_stale_callback(monkeypatch):
    from core import watchdog as watchdog_module

    watchdog_module.Watchdog._instance = None
    watchdog = watchdog_module.Watchdog()
    triggered: list[str] = []

    def on_stale() -> None:
        triggered.append("worker")
        watchdog.started = False

    watchdog.register("worker", on_stale)
    watchdog.registry["worker"] = 0
    watchdog.started = True

    monkeypatch.setattr(watchdog_module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(watchdog_module.time, "time", lambda: 100.0)
    monkeypatch.setattr(watchdog_module.HUDServer, "push_log", lambda _message: None)

    watchdog._monitor()

    assert triggered == ["worker"]


def test_plugin_manager_loads_dynamic_skill(tmp_path, monkeypatch):
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills" / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    from core.plugin_manager import PluginManager

    result = PluginManager.synthesize_and_load_skill(
        "demo",
        "class DemoSkill:\n    def run(self):\n        return 'ok'\n",
        base_workspace=str(tmp_path),
    )

    try:
        assert result["success"] is True, result["error"]
        assert result["module_object"].run() == "ok"
        assert (tmp_path / "skills" / "dynamic_demo_skill.py").is_file()
    finally:
        sys.modules.pop("skills.dynamic_demo_skill", None)


def test_persona_catalog_covers_declared_domains():
    root = REPO_ROOT / "agent_ecosystem"
    domains = sorted(path.name for path in root.iterdir() if path.is_dir())
    personas = list(root.rglob("*.md"))

    assert len(domains) == 13, domains
    assert len(personas) >= 150
    for domain in domains:
        assert any(path.parent.name == domain for path in personas), domain


def test_entrypoint_reads_telegram_credentials_from_environment():
    source = (REPO_ROOT / "main.py").read_text(encoding="utf-8")

    assert 'os.environ.get("TELEGRAM_BOT_TOKEN"' in source
    assert 'os.environ.get("TELEGRAM_CHAT_ID"' in source
    assert re.search(r'TELEGRAM_BOT_TOKEN\s*=\s*"[0-9]{8,}:AA', source) is None
