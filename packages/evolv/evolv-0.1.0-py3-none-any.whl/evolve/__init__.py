"""Evolve - AI-powered code improvement made simple."""

__version__ = "0.1.0"

from .config import EvolveConfig, get_config, set_config
from .coordinator import EvolutionCoordinator, EvolutionTarget
from .errors import ConfigurationError, EvolutionError, EvolveError, ExecutionError

default_coordinator = EvolutionCoordinator()

evolve = default_coordinator.evolve
main_entrypoint = default_coordinator.main_entrypoint

__all__ = [
    "ConfigurationError",
    "EvolutionCoordinator",
    "EvolutionError",
    "EvolutionTarget",
    "EvolveConfig",
    "EvolveError",
    "ExecutionError",
    "__version__",
    "default_coordinator",
    "evolve",
    "get_config",
    "main_entrypoint",
    "set_config",
]
