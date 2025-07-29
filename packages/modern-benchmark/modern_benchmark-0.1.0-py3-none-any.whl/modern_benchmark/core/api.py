from typing import Optional
from .globals import get_global_collector
from .collector import BenchmarkCollector


def get_benchmark_collector() -> BenchmarkCollector:
    """Get the global benchmark collector instance."""
    return get_global_collector()


def print_benchmark_summary(top_n: int = 10) -> None:
    """Print benchmark summary using the global collector."""
    get_global_collector().print_summary(top_n)


def export_benchmarks(filepath: str = "benchmarks/benchmark_data.json") -> None:
    """Export benchmark data to JSON file."""
    get_global_collector().export_to_json(filepath)


def clear_benchmarks(function_name: Optional[str] = None) -> None:
    """Clear benchmark data."""
    get_global_collector().clear_stats(function_name)