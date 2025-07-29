from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BenchmarkResult:
    """Represents a single benchmark measurement."""
    function_name: str
    execution_time: float
    timestamp: datetime
    args_count: int
    kwargs_count: int
    success: bool
    error_message: Optional[str] = None
    thread_id: Optional[int] = None
    memory_usage: Optional[float] = None