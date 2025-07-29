"""Program storage and retrieval."""

import itertools
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple


@dataclass
class Program:
    """A version of a program being evolved."""

    program_code: str
    evolve_code: str
    success: Optional[bool] = None
    stdout: str = ""
    stderr: str = ""
    metrics: Dict[str, float] = field(default_factory=dict)
    parent_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(next(Program._id_counter)))
    _id_counter = itertools.count(1)

    def __str__(self) -> str:
        evolve_snippet = self.evolve_code.split("\n")[0] if self.evolve_code else "N/A"
        return f"ID: {self.id} | {evolve_snippet}... | Metrics: {self.metrics} | Success: {self.success}"

    @property
    def score(self) -> float:
        """Get the primary metric score (used by strategies)."""
        from .config import get_config

        primary_metric = get_config().primary_metric
        return self.metrics.get(primary_metric, 0.0)


class SamplingStrategy(Protocol):
    """Interface for program selection strategies."""

    def add(self, program: Program) -> None: ...
    def select_parent(self, programs: Dict[str, Program]) -> Program: ...
    def select_inspirations(self, programs: Dict[str, Program], parent: Program, n: int) -> List[Program]: ...


class ProgramDatabase:
    """Manages program collection and evolution."""

    def __init__(self, sampling_strategy: SamplingStrategy):
        self.programs: Dict[str, Program] = {}
        self.sampling_strategy: SamplingStrategy = sampling_strategy
        self.best_program_id: Optional[str] = None

    def add(self, program: Program) -> Optional[str]:
        """Adds a successful program to the database."""
        if not program.success:
            return None
        self.programs[program.id] = program
        self.sampling_strategy.add(program)
        self._update_best_program(program)
        return program.id

    def sample(self) -> Tuple[Program, List[Program]]:
        """Samples a parent and inspiration programs."""
        if not self.programs:
            raise ValueError("Cannot sample from empty database.")
        from .config import get_config

        config = get_config()
        parent = self.sampling_strategy.select_parent(self.programs)
        inspirations = self.sampling_strategy.select_inspirations(
            self.programs, parent, config.sampling_num_inspirations
        )
        return parent, inspirations

    def get_best_program(self) -> Optional[Program]:
        """Retrieves the best program found so far."""
        return self.programs.get(self.best_program_id) if self.best_program_id else None

    def _update_best_program(self, program: Program) -> None:
        """Updates best program if current is better."""
        from .config import get_config

        config = get_config()
        metric = config.primary_metric
        current_best = self.get_best_program()

        if not current_best or program.metrics.get(metric, 0) > current_best.metrics.get(metric, 0):
            self.best_program_id = program.id


class RandomSamplingStrategy:
    """Random selection strategy."""

    def add(self, program: Program) -> None:
        pass

    def select_parent(self, programs: Dict[str, Program]) -> Program:
        if not programs:
            raise ValueError("No programs available for sampling.")
        return random.choice(list(programs.values()))

    def select_inspirations(self, programs: Dict[str, Program], parent: Program, n: int) -> List[Program]:
        candidates = [p for p in programs.values() if p.id != parent.id]
        return random.sample(candidates, min(n, len(candidates))) if candidates else []


class LinearSamplingStrategy:
    """Most recent program as parent."""

    def add(self, program: Program) -> None:
        pass

    def select_parent(self, programs: Dict[str, Program]) -> Program:
        if not programs:
            raise ValueError("No programs available for sampling.")
        return max(programs.values(), key=lambda p: int(p.id))

    def select_inspirations(self, programs: Dict[str, Program], parent: Program, n: int) -> List[Program]:
        candidates = [p for p in programs.values() if p.id != parent.id]
        return candidates[: min(n, len(candidates))]
