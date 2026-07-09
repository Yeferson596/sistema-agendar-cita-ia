from dataclasses import dataclass, field
from time import perf_counter
from typing import Dict, List


@dataclass
class AgentMetrics:
    total_calls: int = 0
    valid_extractions: int = 0
    fallbacks: int = 0
    errors: Dict[str, int] = field(default_factory=dict)
    latencies_ms: List[float] = field(default_factory=list)

    @property
    def precision_rate(self) -> float:
        return (self.valid_extractions / self.total_calls * 100) if self.total_calls else 0.0

    @property
    def fallback_rate(self) -> float:
        return (self.fallbacks / self.total_calls * 100) if self.total_calls else 0.0


metrics = AgentMetrics()


def record_call(latency_ms: float, valid_extraction: bool = False, fallback: bool = False, error: str | None = None) -> None:
    metrics.total_calls += 1
    if valid_extraction:
        metrics.valid_extractions += 1
    if fallback:
        metrics.fallbacks += 1
    if error:
        metrics.errors[error] = metrics.errors.get(error, 0) + 1
    metrics.latencies_ms.append(latency_ms)
    # keep sliding window
    if len(metrics.latencies_ms) > 500:
        metrics.latencies_ms.pop(0)
