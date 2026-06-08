import json
import os
import time

import config
from core.cognitive_memory import CognitiveMemory
from core.event_bus import EventBus, Event
from core.hud_server import HUDServer

from evaluation.comparison_engine import compare_models
from evaluation.report_generator import ReportGenerator
from evaluation.tests import (
    run_benchmark_suite,
    run_hallucination_tests,
    run_bias_tests,
    run_safety_tests,
)


class EvaluationFramework:
    """Runs the assignment evaluation pipeline and produces structured results."""

    def __init__(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_path = getattr(config, "EVALUATION_OUTPUT_PATH", "evaluation/reports")
        self.prompts = self._load_prompts()
        self.metrics = {
            "benchmark": {},
            "hallucination": {},
            "bias": {},
            "safety": {},
            "comparison": {},
            "summary": {},
        }
        self.event_bus = EventBus()
        self.memory = CognitiveMemory()
        os.makedirs(self.output_path, exist_ok=True)

    def _load_prompts(self):
        prompt_path = os.path.join(self.root_dir, "evaluation", "fixtures", "prompts.json")
        try:
            with open(prompt_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            raise RuntimeError(f"Unable to load evaluation prompts: {exc}")

    def run_all(self) -> dict:
        HUDServer.set_agent("EVALUATION")
        HUDServer.push_log("🔎 Evaluation: Starting framework run.")
        self.event_bus.publish(Event("evaluation.started", "EvaluationFramework", {"output": self.output_path}))
        self.metrics["errors"] = []

        self.metrics["benchmark"] = self._run_stage("benchmark", run_benchmark_suite, self.prompts.get("benchmark", []))
        self.metrics["hallucination"] = self._run_stage("hallucination", run_hallucination_tests, self.prompts.get("hallucination", []))
        self.metrics["bias"] = self._run_stage("bias", run_bias_tests, self.prompts.get("bias", []))
        self.metrics["safety"] = self._run_stage("safety", run_safety_tests, self.prompts.get("safety", []))
        self.metrics["comparison"] = self._run_stage("comparison", compare_models, self.prompts.get("comparison", []))

        self.metrics["summary"] = self._summarize()
        self.event_bus.publish(Event("evaluation.completed", "EvaluationFramework", self.metrics["summary"]))

        report_path = ReportGenerator.generate(self.metrics, self.output_path)
        self.metrics["summary"]["report_path"] = report_path

        HUDServer.push_log("✅ Evaluation: Completed successfully.")
        HUDServer.set_agent("IDLE")
        return self.metrics

    def _run_stage(self, name: str, func, *args, **kwargs) -> dict:
        try:
            result = func(*args, **kwargs)
            self.event_bus.publish(Event("evaluation.stage.completed", "EvaluationFramework", {"stage": name}))
            return result
        except Exception as exc:
            error_message = f"Evaluation stage '{name}' failed: {exc}"
            HUDServer.push_log(f"⚠️ {error_message}")
            self.event_bus.publish(Event("evaluation.stage.failed", "EvaluationFramework", {"stage": name, "error": str(exc)}))
            self.metrics["errors"].append({"stage": name, "error": str(exc)})
            return {"results": [], "total_latency": 0.0, "error": str(exc)}

    def _summarize(self) -> dict:
        benchmark_results = self.metrics["benchmark"].get("results", [])
        hallucination_results = self.metrics["hallucination"].get("results", [])
        bias_results = self.metrics["bias"].get("results", [])
        safety_results = self.metrics["safety"].get("results", [])
        
        benchmark_tests = len(benchmark_results)
        benchmark_passed = sum(1 for c in benchmark_results if c.get("passed", False))
        
        hallucination_tests = len(hallucination_results)
        hallucination_passed = sum(1 for c in hallucination_results if c.get("passed", False))
        
        bias_tests = len(bias_results)
        bias_passed = sum(1 for c in bias_results if c.get("passed", False))
        
        safety_tests = len(safety_results)
        safety_passed = sum(1 for c in safety_results if c.get("passed", False))
        
        total_tests = benchmark_tests + hallucination_tests + bias_tests + safety_tests
        total_passed = benchmark_passed + hallucination_passed + bias_passed + safety_passed
        overall_score = int((total_passed / total_tests) * 100) if total_tests > 0 else 0

        summary = {
            "benchmark_tests": benchmark_tests,
            "benchmark_passed": benchmark_passed,
            "hallucination_tests": hallucination_tests,
            "hallucination_passed": hallucination_passed,
            "bias_tests": bias_tests,
            "bias_passed": bias_passed,
            "safety_tests": safety_tests,
            "safety_passed": safety_passed,
            "comparison_cases": len(self.metrics["comparison"].get("results", [])),
            "overall_score": overall_score,
            "total_latency_seconds": sum([
                self.metrics["benchmark"].get("total_latency", 0),
                self.metrics["hallucination"].get("total_latency", 0),
                self.metrics["bias"].get("total_latency", 0),
                self.metrics["safety"].get("total_latency", 0),
                self.metrics["comparison"].get("total_latency", 0),
            ]),
            "gemini_enabled": getattr(config, "GEMINI_ENABLED", False),
            "oss_model": getattr(config, "OSS_MODEL", getattr(config, "LLM_MODEL", "qwen2.5-coder:7b")),
            "frontier_model": getattr(config, "GEMINI_MODEL", None) if getattr(config, "GEMINI_ENABLED", False) else getattr(config, "FRONTIER_MODEL", None),
        }
        return summary
