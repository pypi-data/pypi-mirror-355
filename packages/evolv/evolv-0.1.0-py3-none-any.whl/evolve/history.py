"""Simple evolution history tracking for enhanced prompting."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EvolutionRecord:
    """Simple record of evolution attempt."""

    generation: int
    fitness: float
    success: bool
    improvement: Optional[str] = None
    error: Optional[str] = None


class EvolutionHistory:
    """Lightweight history tracking for better prompting."""

    def __init__(self):
        from .config import get_config

        self.config = get_config()
        self.records: List[EvolutionRecord] = []
        self.generation = 0
        self.best_fitness = 0.0
        self.plateau_count = 0
        self.last_fitness = 0.0

    def add_record(self, fitness: float, success: bool, improvement: Optional[str] = None, error: Optional[str] = None):
        """Add evolution record and update stats."""
        self.generation += 1

        record = EvolutionRecord(
            generation=self.generation, fitness=fitness, success=success, improvement=improvement, error=error
        )
        self.records.append(record)

        # Keep only last history_record_limit records
        if len(self.records) > self.config.history_record_limit:
            self.records.pop(0)

        # Update stats
        if fitness > self.best_fitness:
            self.best_fitness = fitness
            self.plateau_count = 0
        else:
            self.plateau_count += 1

        self.last_fitness = fitness

    def get_context_summary(self, primary_metric: str) -> str:
        """Get a simple context summary for prompting."""
        if not self.records:
            return "Generation 1: Starting evolution"

        lines = [f"Generation {self.generation}"]

        # Add recent improvements
        lookback = self.config.history_lookback_window
        recent_successes = [r for r in self.records[-lookback:] if r.success and r.improvement]
        if recent_successes:
            lines.append("Recent successful improvements:")
            for r in recent_successes:
                lines.append(f"  - {r.improvement[:60]}... (fitness: {r.fitness:.4f})")

        # Add error patterns if any
        recent_errors = [r for r in self.records[-lookback:] if not r.success and r.error]
        if recent_errors:
            lines.append("Avoid these error patterns:")
            error_types = set()
            for r in recent_errors:
                error_type = r.error.split(":")[0] if r.error else "Unknown"
                error_types.add(error_type)
            for et in error_types:
                lines.append(f"  - {et}")

        # Add plateau warning
        if self.plateau_count > self.config.history_lookback_window:
            lines.append(f"Progress plateauing ({self.plateau_count} generations) - try different approaches")

        return "\n".join(lines)
