"""Basic evolution strategies: Linear, Random, Tournament."""

import random
from typing import Any, Dict, List

from ..database import Program, ProgramDatabase
from .base import BaseEvolutionStrategy, StrategyFactory


class LinearStrategy(BaseEvolutionStrategy):
    """Linear selection - always selects the most recent program as parent."""

    def select_parents(self, database: ProgramDatabase, count: int = 1) -> List[Program]:
        """Select the most recent programs."""
        if not database.programs:
            raise ValueError("Cannot select from empty database")

        # Sort by ID (most recent first)
        sorted_programs = sorted(database.programs.values(), key=lambda p: int(p.id), reverse=True)

        # Return the most recent programs
        return sorted_programs[: min(count, len(sorted_programs))]


class RandomStrategy(BaseEvolutionStrategy):
    """Random selection - selects parents randomly from the population."""

    def select_parents(self, database: ProgramDatabase, count: int = 1) -> List[Program]:
        """Select random programs."""
        if not database.programs:
            raise ValueError("Cannot select from empty database")

        programs = list(database.programs.values())

        # Sample with replacement if count > population size
        if count > len(programs):
            return [random.choice(programs) for _ in range(count)]

        return random.sample(programs, count)


class TournamentStrategy(BaseEvolutionStrategy):
    """Tournament selection - runs tournaments to select parents based on fitness."""

    def initialize(self, config: Dict[str, Any], initial_program: Program) -> None:
        """Initialize with tournament-specific config."""
        super().initialize(config, initial_program)
        self.tournament_size = config.get("tournament_size", 3)
        self.selection_pressure = config.get("selection_pressure", 0.8)

    def select_parents(self, database: ProgramDatabase, count: int = 1) -> List[Program]:
        """Select parents using tournament selection."""
        if not database.programs:
            raise ValueError("Cannot select from empty database")

        programs = list(database.programs.values())
        parents = []

        for _ in range(count):
            # Run a tournament
            parent = self._run_tournament(programs)
            parents.append(parent)

        return parents

    def _run_tournament(self, programs: List[Program]) -> Program:
        """Run a single tournament to select a parent."""
        # Sample tournament participants
        tournament_size = min(self.tournament_size, len(programs))
        participants = random.sample(programs, tournament_size)

        # Apply selection pressure
        if random.random() < self.selection_pressure:
            # Select best by primary metric
            from ..config import get_config

            metric = get_config().primary_metric

            return max(participants, key=lambda p: p.metrics.get(metric, 0))
        else:
            # Random selection for diversity
            return random.choice(participants)

    def get_strategy_metrics(self) -> Dict[str, Any]:
        """Return tournament-specific metrics."""
        metrics = super().get_strategy_metrics()
        metrics.update({"tournament_size": self.tournament_size, "selection_pressure": self.selection_pressure})
        return metrics


# Register basic strategies
StrategyFactory.register("linear", LinearStrategy)
StrategyFactory.register("random", RandomStrategy)
StrategyFactory.register("tournament", TournamentStrategy)
