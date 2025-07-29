"""Base evolution strategy protocol and factory."""

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Protocol, Type

from ..database import Program, ProgramDatabase

logger = logging.getLogger(__name__)


class EvolutionStrategy(Protocol):
    """Protocol for pluggable evolution strategies.

    This defines the interface that all evolution strategies must implement.
    Strategies control how parents are selected, whether candidates are accepted,
    and how internal state is updated during evolution.
    """

    def initialize(self, config: Dict[str, Any], initial_program: Program) -> None:
        """Initialize strategy with configuration and initial program.

        Args:
            config: Strategy-specific configuration parameters
            initial_program: The starting program for evolution
        """
        ...

    def select_parents(self, database: ProgramDatabase, count: int = 1) -> List[Program]:
        """Select parent programs for generating new variants.

        Args:
            database: The program database containing all evaluated programs
            count: Number of parents to select

        Returns:
            List of parent programs
        """
        ...

    def should_accept(self, candidate: Program, database: ProgramDatabase) -> bool:
        """Decide whether a candidate program should be added to the population.

        Args:
            candidate: The candidate program to evaluate
            database: The program database for comparison

        Returns:
            True if the candidate should be accepted
        """
        ...

    def update_state(self, new_program: Program, database: ProgramDatabase) -> None:
        """Update internal strategy state after accepting a new program.

        Args:
            new_program: The newly accepted program
            database: The program database
        """
        ...

    def get_strategy_metrics(self) -> Dict[str, Any]:
        """Return strategy-specific metrics for monitoring.

        Returns:
            Dictionary of strategy metrics
        """
        ...


class BaseEvolutionStrategy(ABC):
    """Base class providing common functionality for evolution strategies."""

    def __init__(self):
        self.generation = 0
        self.config: Dict[str, Any] = {}
        self.initial_program: Optional[Program] = None
        self.metrics: Dict[str, Any] = {}

    def initialize(self, config: Dict[str, Any], initial_program: Program) -> None:
        """Initialize strategy with configuration."""
        self.config = config
        self.initial_program = initial_program
        self.generation = 0
        logger.info(f"Initialized {self.__class__.__name__} with config: {config}")

    @abstractmethod
    def select_parents(self, database: ProgramDatabase, count: int = 1) -> List[Program]:
        """Select parent programs."""
        pass

    def should_accept(self, candidate: Program, database: ProgramDatabase) -> bool:
        """Default: accept all successful programs."""
        return candidate.success

    def update_state(self, new_program: Program, database: ProgramDatabase) -> None:
        """Update generation counter."""
        self.generation += 1

    def get_strategy_metrics(self) -> Dict[str, Any]:
        """Return basic metrics."""
        return {"type": self.__class__.__name__, "generation": self.generation, **self.metrics}


class StrategyFactory:
    """Factory for creating evolution strategy instances."""

    _strategies: ClassVar[Dict[str, Type[EvolutionStrategy]]] = {}

    @classmethod
    def register(cls, name: str, strategy_class: Type[EvolutionStrategy]) -> None:
        """Register a strategy class.

        Args:
            name: Name to register the strategy under
            strategy_class: The strategy class to register
        """
        cls._strategies[name] = strategy_class
        logger.debug(f"Registered strategy: {name}")

    @classmethod
    def create(cls, name: str, **kwargs) -> EvolutionStrategy:
        """Create a strategy instance.

        Args:
            name: Name of the strategy to create
            **kwargs: Additional arguments for strategy initialization

        Returns:
            Strategy instance

        Raises:
            ValueError: If strategy name is not registered
        """
        if name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(f"Unknown strategy: {name}. Available: {available}")

        strategy_class = cls._strategies[name]
        return strategy_class(**kwargs)

    @classmethod
    def list_strategies(cls) -> List[str]:
        """List all registered strategy names."""
        return list(cls._strategies.keys())
