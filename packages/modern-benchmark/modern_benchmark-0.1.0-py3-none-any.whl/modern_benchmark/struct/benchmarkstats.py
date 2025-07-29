from collections import defaultdict, deque
from dataclasses import dataclass, field

@dataclass
class BenchmarkStats:
    """Statistics for a benchmarked function."""
    function_name: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    median_time: float = 0.0
    std_dev: float = 0.0
    success_rate: float = 0.0
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_count: int = 0