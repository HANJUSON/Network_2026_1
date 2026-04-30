import time
import statistics
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


def get_time_ns() -> int:
    return time.perf_counter_ns()


def get_timestamp_ns() -> int:
    return time.time_ns()


def format_ns(ns: int) -> str:
    if ns >= 1_000_000_000:
        return f"{ns / 1_000_000_000:.3f}s"
    elif ns >= 1_000_000:
        return f"{ns / 1_000_000:.3f}ms"
    elif ns >= 1_000:
        return f"{ns / 1_000:.3f}us"
    else:
        return f"{ns}ns"


class LatencyStats:
    def __init__(self, latencies: List[int]):
        self.latencies = sorted(latencies)
        self.count = len(latencies)
        
    @property
    def min_ns(self) -> int:
        return self.latencies[0] if self.latencies else 0
    
    @property
    def max_ns(self) -> int:
        return self.latencies[-1] if self.latencies else 0
    
    @property
    def mean_ns(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0
    
    @property
    def median_ns(self) -> float:
        return statistics.median(self.latencies) if self.latencies else 0
    
    @property
    def std_ns(self) -> float:
        return statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0
    
    def percentile(self, p: float) -> float:
        if not self.latencies:
            return 0
        idx = int(len(self.latencies) * p / 100)
        idx = min(idx, len(self.latencies) - 1)
        return self.latencies[idx]
    
    @property
    def p50(self) -> float:
        return self.percentile(50)
    
    @property
    def p75(self) -> float:
        return self.percentile(75)
    
    @property
    def p90(self) -> float:
        return self.percentile(90)
    
    @property
    def p95(self) -> float:
        return self.percentile(95)
    
    @property
    def p99(self) -> float:
        return self.percentile(99)
    
    @property
    def p999(self) -> float:
        return self.percentile(99.9)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "min_ns": self.min_ns,
            "max_ns": self.max_ns,
            "mean_ns": self.mean_ns,
            "median_ns": self.median_ns,
            "std_ns": self.std_ns,
            "p50_ns": self.p50,
            "p75_ns": self.p75,
            "p90_ns": self.p90,
            "p95_ns": self.p95,
            "p99_ns": self.p99,
            "p999_ns": self.p999,
        }
    
    def summary(self) -> str:
        return (
            f"LatencyStats(n={self.count}):\n"
            f"  Min:    {format_ns(self.min_ns)}\n"
            f"  Mean:   {format_ns(self.mean_ns)}\n"
            f"  Median: {format_ns(self.median_ns)}\n"
            f"  Std:    {format_ns(self.std_ns)}\n"
            f"  Max:    {format_ns(self.max_ns)}\n"
            f"  P50:    {format_ns(self.p50)}\n"
            f"  P75:    {format_ns(self.p75)}\n"
            f"  P90:    {format_ns(self.p90)}\n"
            f"  P95:    {format_ns(self.p95)}\n"
            f"  P99:    {format_ns(self.p99)}\n"
            f"  P99.9:  {format_ns(self.p999)}"
        )


class ResultLogger:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = results_dir
        self.results: List[Dict[str, Any]] = []
    
    def add_result(
        self,
        protocol: str,
        num_orders: int,
        interval_us: float,
        stats: LatencyStats,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        result = {
            "timestamp": datetime.now().isoformat(),
            "protocol": protocol,
            "num_orders": num_orders,
            "interval_us": interval_us,
            "stats": stats.to_dict(),
        }
        if metadata:
            result["metadata"] = metadata
        self.results.append(result)
    
    def save(self, filename: Optional[str] = None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_{timestamp}.json"
        
        filepath = f"{self.results_dir}/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def print_summary(self):
        for result in self.results:
            print(f"\n{'='*60}")
            print(f"Protocol: {result['protocol']}")
            print(f"Orders: {result['num_orders']}, Interval: {result['interval_us']}us")
            print(f"{'='*60}")
            stats = LatencyStats([])
            stats.__dict__.update(result['stats'])
            print(stats.summary())
