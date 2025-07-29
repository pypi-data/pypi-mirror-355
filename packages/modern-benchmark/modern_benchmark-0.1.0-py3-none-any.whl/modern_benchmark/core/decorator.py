import time
import functools
import threading
from typing import Callable, Any, Optional
from datetime import datetime

from modern_benchmark.util.logging import log
from modern_benchmark.struct.benchmarkresult import BenchmarkResult
from .collector import BenchmarkCollector
from .globals import get_global_collector


def benchmark(
    name: Optional[str] = None,
    enabled: bool = True,
    log_slow_calls: bool = True,
    slow_threshold_ms: float = 1000.0,
    collect_memory: bool = False,
    collector: Optional[BenchmarkCollector] = None
):
    """
    Decorator to benchmark function execution time and collect performance metrics.
    
    Args:
        name: Custom name for the benchmark (defaults to function name)
        enabled: Whether benchmarking is enabled
        log_slow_calls: Whether to log calls that exceed the slow threshold
        slow_threshold_ms: Threshold in milliseconds for considering a call slow
        collect_memory: Whether to collect memory usage (requires psutil)
        collector: Custom collector instance (defaults to global collector)
    
    Usage:
        @benchmark()
        def my_function():
            pass
        
        @benchmark(name="custom_name", slow_threshold_ms=500)
        def another_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        if not enabled:
            return func
        
        func_name = name or f"{func.__module__}.{func.__qualname__}"
        benchmark_collector = collector or get_global_collector()
        logger = log()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            thread_id = threading.get_ident()
            memory_before = None
            
            if collect_memory:
                try:
                    import psutil
                    process = psutil.Process()
                    memory_before = process.memory_info().rss / 1024 / 1024  # MB
                except ImportError:
                    logger.warning("psutil not available for memory collection")
            
            success = True
            error_message = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                
                memory_usage = None
                if collect_memory and memory_before is not None:
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_after = process.memory_info().rss / 1024 / 1024  # MB
                        memory_usage = memory_after - memory_before
                    except ImportError:
                        pass
                
                # Create benchmark result
                benchmark_result = BenchmarkResult(
                    function_name=func_name,
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                    args_count=len(args),
                    kwargs_count=len(kwargs),
                    success=success,
                    error_message=error_message,
                    thread_id=thread_id,
                    memory_usage=memory_usage
                )
                
                # Add to collector
                benchmark_collector.add_result(benchmark_result)
                
                # Log slow calls
                if log_slow_calls and execution_time * 1000 > slow_threshold_ms:
                    logger.warning(
                        f"Slow function call detected: {func_name} "
                        f"took {execution_time*1000:.2f}ms "
                        f"(threshold: {slow_threshold_ms}ms)"
                    )
        
        return wrapper
    return decorator