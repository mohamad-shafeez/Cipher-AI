"""
Inference Pipeline Telemetry

Tracks performance metrics across all inference stages:
- Latency per stage (memory injection, routing, model execution, response processing)
- Port utilization and fallback rates
- Model degradation tracking
- Memory overhead measurement
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import time
import json
import os

@dataclass
class InferenceMetrics:
    """Tracks metrics for a single inference call."""
    request_id: str
    timestamp: str
    model: str
    port: int
    
    # Latencies (seconds)
    memory_injection_time: float = 0.0
    routing_time: float = 0.0
    model_execution_time: float = 0.0
    response_processing_time: float = 0.0
    total_latency: float = 0.0
    
    # Status tracking
    status: str = "pending"  # pending, success, fallback, error
    fallback_count: int = 0
    fallback_ports: List[int] = field(default_factory=list)
    
    # Memory integration
    memory_context_injected: bool = False
    semantic_memory_queries: int = 0
    recent_interactions_retrieved: int = 0
    
    # Response metadata
    response_length: int = 0
    mock_response: bool = False
    
    def to_dict(self) -> Dict:
        """Serializes metrics to dictionary."""
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "model": self.model,
            "port": self.port,
            "latencies": {
                "memory_injection_ms": round(self.memory_injection_time * 1000, 2),
                "routing_ms": round(self.routing_time * 1000, 2),
                "model_execution_ms": round(self.model_execution_time * 1000, 2),
                "response_processing_ms": round(self.response_processing_time * 1000, 2),
                "total_ms": round(self.total_latency * 1000, 2)
            },
            "status": self.status,
            "fallback_count": self.fallback_count,
            "fallback_ports": self.fallback_ports,
            "memory": {
                "context_injected": self.memory_context_injected,
                "semantic_queries": self.semantic_memory_queries,
                "interactions_retrieved": self.recent_interactions_retrieved
            },
            "response": {
                "length": self.response_length,
                "mock": self.mock_response
            }
        }


class InferenceTelemetry:
    """
    Collects and aggregates inference telemetry.
    Persists metrics to JSON for analysis and reporting.
    """
    
    def __init__(self):
        self.db_dir = "storage"
        self.metrics_path = os.path.join(self.db_dir, "inference_telemetry.json")
        self.metrics_buffer: List[Dict] = []
        self.aggregate_stats: Dict = {
            "total_calls": 0,
            "successful_calls": 0,
            "fallback_calls": 0,
            "error_calls": 0,
            "average_latency_ms": 0.0,
            "port_11434_usage": 0,
            "port_11435_usage": 0,
            "memory_injection_overhead_ms": 0.0,
            "mock_response_rate": 0.0
        }
        
        os.makedirs(self.db_dir, exist_ok=True)
        self._load_historical_metrics()
        print(">> Inference Telemetry: ONLINE")
    
    def _load_historical_metrics(self):
        """Loads previously collected metrics."""
        try:
            if os.path.exists(self.metrics_path):
                with open(self.metrics_path, 'r') as f:
                    data = json.load(f)
                    self.metrics_buffer = data.get("metrics", [])
                    self.aggregate_stats = data.get("stats", self.aggregate_stats)
        except Exception as e:
            print(f"[Telemetry] Warning: Could not load historical metrics: {e}")
    
    def record_inference(self, metrics: InferenceMetrics):
        """Records metrics for a single inference call."""
        # Add to buffer
        self.metrics_buffer.append(metrics.to_dict())
        
        # Update aggregates
        self.aggregate_stats["total_calls"] += 1
        
        if metrics.status == "success":
            self.aggregate_stats["successful_calls"] += 1
        elif metrics.status == "fallback":
            self.aggregate_stats["fallback_calls"] += 1
        elif metrics.status == "error":
            self.aggregate_stats["error_calls"] += 1
        
        # Port usage
        if metrics.port == 11434:
            self.aggregate_stats["port_11434_usage"] += 1
        elif metrics.port == 11435:
            self.aggregate_stats["port_11435_usage"] += 1
        
        # Latency aggregation
        total_calls = self.aggregate_stats["total_calls"]
        old_avg = self.aggregate_stats["average_latency_ms"]
        new_latency = metrics.total_latency * 1000
        self.aggregate_stats["average_latency_ms"] = (
            (old_avg * (total_calls - 1) + new_latency) / total_calls
        )
        
        # Memory injection overhead
        self.aggregate_stats["memory_injection_overhead_ms"] = metrics.memory_injection_time * 1000
        
        # Mock response rate
        mock_count = sum(1 for m in self.metrics_buffer if m.get("response", {}).get("mock", False))
        self.aggregate_stats["mock_response_rate"] = (mock_count / len(self.metrics_buffer)) * 100
        
        # Persist periodically (every 10 calls)
        if len(self.metrics_buffer) % 10 == 0:
            self.flush()
    
    def flush(self):
        """Persists metrics to disk."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "metrics": self.metrics_buffer[-100:],  # Keep last 100 for rotation
                "stats": self.aggregate_stats
            }
            with open(self.metrics_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Telemetry] Warning: Could not flush metrics: {e}")
    
    def get_report(self) -> str:
        """Generates a human-readable telemetry report."""
        stats = self.aggregate_stats
        
        report = """
╔════════════════════════════════════════════════════════════╗
║          INFERENCE PIPELINE TELEMETRY REPORT              ║
╚════════════════════════════════════════════════════════════╝

📊 OVERALL STATISTICS
  Total Inferences: {total_calls}
  Successful: {successful_calls}
  Fallback Used: {fallback_calls}
  Failed: {error_calls}
  Success Rate: {success_rate:.1f}%

⏱️ LATENCY METRICS
  Average Latency: {avg_latency:.2f}ms
  Memory Injection Overhead: {memory_overhead:.2f}ms
  Memory % of Total: {memory_percent:.1f}%

🔌 PORT UTILIZATION
  Port 11434 (Fast): {port_11434_usage} calls ({fast_pct:.1f}%)
  Port 11435 (Heavy): {port_11435_usage} calls ({heavy_pct:.1f}%)

⚙️ RELIABILITY METRICS
  Fallback Rate: {fallback_rate:.1f}%
  Mock Response Rate: {mock_rate:.1f}%

""".format(
            total_calls=stats["total_calls"],
            successful_calls=stats["successful_calls"],
            fallback_calls=stats["fallback_calls"],
            error_calls=stats["error_calls"],
            success_rate=(stats["successful_calls"] / max(stats["total_calls"], 1)) * 100,
            avg_latency=stats["average_latency_ms"],
            memory_overhead=stats["memory_injection_overhead_ms"],
            memory_percent=(stats["memory_injection_overhead_ms"] / max(stats["average_latency_ms"], 1)) * 100,
            port_11434_usage=stats["port_11434_usage"],
            port_11435_usage=stats["port_11435_usage"],
            fast_pct=(stats["port_11434_usage"] / max(stats["total_calls"], 1)) * 100,
            heavy_pct=(stats["port_11435_usage"] / max(stats["total_calls"], 1)) * 100,
            fallback_rate=(stats["fallback_calls"] / max(stats["total_calls"], 1)) * 100,
            mock_rate=stats["mock_response_rate"]
        )
        
        return report


# Global telemetry instance
_telemetry_instance: Optional[InferenceTelemetry] = None


def get_telemetry() -> InferenceTelemetry:
    """Gets or creates the global telemetry instance."""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = InferenceTelemetry()
    return _telemetry_instance


class TelemetryContext:
    """Context manager for tracking inference metrics."""
    
    def __init__(self, model: str, port: int = 11434):
        self.metrics = InferenceMetrics(
            request_id=f"inf_{int(time.time() * 1000000)}",
            timestamp=datetime.now().isoformat(),
            model=model,
            port=port
        )
        self.stage_start = 0
    
    def start_stage(self, stage_name: str):
        """Marks the start of a measurement stage."""
        self.stage_start = time.perf_counter()
        self._current_stage = stage_name
    
    def end_stage(self):
        """Marks the end of a measurement stage and records latency."""
        elapsed = time.perf_counter() - self.stage_start
        
        if self._current_stage == "memory_injection":
            self.metrics.memory_injection_time = elapsed
        elif self._current_stage == "routing":
            self.metrics.routing_time = elapsed
        elif self._current_stage == "model_execution":
            self.metrics.model_execution_time = elapsed
        elif self._current_stage == "response_processing":
            self.metrics.response_processing_time = elapsed
    
    def finalize(self):
        """Finalizes metrics and records them."""
        self.metrics.total_latency = (
            self.metrics.memory_injection_time +
            self.metrics.routing_time +
            self.metrics.model_execution_time +
            self.metrics.response_processing_time
        )
        
        telemetry = get_telemetry()
        telemetry.record_inference(self.metrics)
