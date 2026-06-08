import os
import sys

# Ensure terminal output can safely render or replace Unicode on Windows consoles.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.event_bus import EventBus, Event
from core.hud_server import HUDServer
from evaluation.framework import EvaluationFramework


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    HUDServer.set_agent("EVALUATION")
    HUDServer.push_log("🚀 Evaluation runner started.")
    bus = EventBus()
    bus.publish(Event("evaluation.runner.started", "run_evaluation", {}))
    try:
        framework = EvaluationFramework()
        metrics = framework.run_all()
        HUDServer.push_log("🏁 Evaluation runner finished.")
        print("Evaluation complete.")
        print(f"Report path: {metrics['summary'].get('report_path')}")
    except Exception as exc:
        HUDServer.push_log(f"❌ Evaluation runner failed: {exc}")
        print("Evaluation failed:", str(exc))
        raise


if __name__ == "__main__":
    main()
