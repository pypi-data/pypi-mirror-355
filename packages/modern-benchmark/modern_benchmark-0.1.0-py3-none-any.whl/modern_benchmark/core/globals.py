from .collector import BenchmarkCollector

# Global benchmark collector instance
_global_collector = None


def get_global_collector() -> BenchmarkCollector:
    """Get the global benchmark collector instance."""
    global _global_collector
    if _global_collector is None:
        _global_collector = BenchmarkCollector()
    return _global_collector


def set_global_collector(collector: BenchmarkCollector) -> None:
    """Set a new global benchmark collector instance."""
    global _global_collector
    _global_collector = collector