import json
import os
import threading
from collections import defaultdict
from typing import Dict, List, Optional, Union
from statistics import mean, median, stdev
from datetime import datetime

from modern_benchmark.util.logging import log
from modern_benchmark.util.jsonutils import serialize_for_json
from modern_benchmark.struct.benchmarkresult import BenchmarkResult
from modern_benchmark.struct.benchmarkstats import BenchmarkStats


class BenchmarkCollector:
    """Central collector for benchmark data with thread-safe operations."""
    
    def __init__(self, max_history: int = 1000):
        self._results: Dict[str, List[BenchmarkResult]] = defaultdict(list)
        self._stats: Dict[str, BenchmarkStats] = defaultdict(lambda: BenchmarkStats(""))
        self._lock = threading.RLock()
        self._max_history = max_history
        self.logger = log()
        
    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result in a thread-safe manner."""
        with self._lock:
            func_name = result.function_name
            
            # Add to results history
            self._results[func_name].append(result)
            
            # Maintain max history limit
            if len(self._results[func_name]) > self._max_history:
                self._results[func_name] = self._results[func_name][-self._max_history:]
            
            # Update statistics
            self._update_stats(result)
    
    def _update_stats(self, result: BenchmarkResult) -> None:
        """Update statistics for a function."""
        stats = self._stats[result.function_name]
        stats.function_name = result.function_name
        stats.total_calls += 1
        
        if result.success:
            stats.total_time += result.execution_time
            stats.min_time = min(stats.min_time, result.execution_time)
            stats.max_time = max(stats.max_time, result.execution_time)
            stats.recent_times.append(result.execution_time)
            
            # Calculate averages and statistics
            times = list(stats.recent_times)
            if times:
                stats.avg_time = mean(times)
                stats.median_time = median(times)
                if len(times) > 1:
                    stats.std_dev = stdev(times)
        else:
            stats.error_count += 1
        
        stats.success_rate = (stats.total_calls - stats.error_count) / stats.total_calls * 100
    
    def get_stats(self, function_name: Optional[str] = None) -> Union[BenchmarkStats, Dict[str, BenchmarkStats]]:
        """Get statistics for a specific function or all functions."""
        with self._lock:
            if function_name:
                return self._stats.get(function_name, BenchmarkStats(function_name))
            return dict(self._stats)
    
    def get_results(self, function_name: str, limit: Optional[int] = None) -> List[BenchmarkResult]:
        """Get recent results for a function."""
        with self._lock:
            results = self._results.get(function_name, [])
            if limit:
                return results[-limit:]
            return results.copy()
    
    def get_slowest_functions(self, limit: int = 10) -> List[BenchmarkStats]:
        """Get the slowest functions by average execution time."""
        with self._lock:
            stats_list = [stats for stats in self._stats.values() if stats.total_calls > 0]
            return sorted(stats_list, key=lambda x: x.avg_time, reverse=True)[:limit]
    
    def get_most_called_functions(self, limit: int = 10) -> List[BenchmarkStats]:
        """Get the most frequently called functions."""
        with self._lock:
            stats_list = list(self._stats.values())
            return sorted(stats_list, key=lambda x: x.total_calls, reverse=True)[:limit]
    
    def export_to_json(self, filepath: str) -> None:
        """Export benchmark data to JSON file."""
        with self._lock:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'stats': {name: serialize_for_json(stats) for name, stats in self._stats.items()},
                'recent_results': {
                    name: [serialize_for_json(result) for result in results[-50:]]
                    for name, results in self._results.items()
                }
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
    
    def clear_stats(self, function_name: Optional[str] = None) -> None:
        """Clear statistics for a specific function or all functions."""
        with self._lock:
            if function_name:
                if function_name in self._stats:
                    del self._stats[function_name]
                if function_name in self._results:
                    del self._results[function_name]
            else:
                self._stats.clear()
                self._results.clear()
    
    def print_summary(self, top_n: int = 10) -> None:
        """Print a summary of benchmark statistics."""
        with self._lock:
            print("\n" + "="*80)
            print("BENCHMARK SUMMARY")
            print("="*80)
            
            if not self._stats:
                print("No benchmark data available.")
                return
            
            print(f"\nSlowest Functions (Top {top_n}):")
            print("-" * 50)
            for i, stats in enumerate(self.get_slowest_functions(top_n), 1):
                print(f"{i:2d}. {stats.function_name:<30} "
                      f"Avg: {stats.avg_time*1000:.2f}ms "
                      f"Calls: {stats.total_calls} "
                      f"Success: {stats.success_rate:.1f}%")
            
            print(f"\nMost Called Functions (Top {top_n}):")
            print("-" * 50)
            for i, stats in enumerate(self.get_most_called_functions(top_n), 1):
                print(f"{i:2d}. {stats.function_name:<30} "
                      f"Calls: {stats.total_calls} "
                      f"Avg: {stats.avg_time*1000:.2f}ms "
                      f"Success: {stats.success_rate:.1f}%")