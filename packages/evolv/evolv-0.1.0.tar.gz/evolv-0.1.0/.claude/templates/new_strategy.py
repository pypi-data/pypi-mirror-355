"""Template for creating a new evolution strategy."""

from typing import Any, Dict, List, Optional

from ..database import Database, Program
from .base import BaseStrategy


class NewStrategy(BaseStrategy):
    """
    Brief description of the strategy.

    This strategy selects parents by [DESCRIBE SELECTION METHOD].

    Args:
        config: Strategy configuration with keys:
            - key1: Description (default: value)
            - key2: Description (default: value)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the strategy with configuration."""
        super().__init__(config or {})
        # Extract configuration with defaults
        self.key1 = self.config.get("key1", "default_value")
        self.key2 = self.config.get("key2", 0.5)

    def select_parents(self, database: Database, n_parents: int, primary_metric: str = "fitness") -> List[Program]:
        """
        Select parent programs for the next generation.

        Args:
            database: Program database
            n_parents: Number of parents to select
            primary_metric: Metric to optimize

        Returns:
            List of selected parent programs
        """
        # Get all programs
        programs = database.get_all_programs()
        if not programs:
            return []

        # TODO: Implement selection logic
        # Example: Select top performers
        sorted_programs = sorted(programs, key=lambda p: p.metrics.get(primary_metric, 0), reverse=True)

        return sorted_programs[:n_parents]

    def should_terminate(
        self, database: Database, generation: int, best_score: float, no_improvement_generations: int
    ) -> bool:
        """
        Determine if evolution should terminate.

        Args:
            database: Program database
            generation: Current generation number
            best_score: Best score achieved so far
            no_improvement_generations: Generations without improvement

        Returns:
            True if evolution should stop
        """
        # Add custom termination logic if needed
        return super().should_terminate(database, generation, best_score, no_improvement_generations)
