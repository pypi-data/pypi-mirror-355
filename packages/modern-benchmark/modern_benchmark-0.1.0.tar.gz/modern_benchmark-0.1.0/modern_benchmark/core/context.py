import time
import threading
from typing import Optional
from datetime import datetime

from modern_benchmark.util.logging import log
from modern_benchmark.struct.benchmarkresult import BenchmarkResult
from .collector import BenchmarkCollector
from .globals import get_global_collector


class BenchmarkContext:
    """Context manager for benchmarking code blocks."""
    
    def __init__(self, name: str, collector: Optional[BenchmarkCollector] = None):
        self.name = name
        self.collector = collector or get_global_collector()
        self.start_time = None
        self.logger = log()
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            execution_time = time.perf_counter() - self.start_time
            
            result = BenchmarkResult(
                function_name=self.name,
                execution_time=execution_time,
                timestamp=datetime.now(),
                args_count=0,
                kwargs_count=0,
                success=exc_type is None,
                error_message=str(exc_val) if exc_val else None,
                thread_id=threading.get_ident()
            )
            
            self.collector.add_result(result)


def benchmark_context(name: str, collector: Optional[BenchmarkCollector] = None) -> BenchmarkContext:
    """Create a benchmark context manager for timing code blocks."""
    return BenchmarkContext(name, collector)