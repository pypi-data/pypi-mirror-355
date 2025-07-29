"""
Centralized error handling for the Evolv framework.
"""

import functools
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class EvolveError(Exception):
    """Base exception for all Evolv-related errors."""

    pass


class ConfigurationError(EvolveError):
    """Raised when configuration is invalid or missing."""

    pass


class EvolutionError(EvolveError):
    """Raised when evolution process fails."""

    pass


class ExecutionError(EvolveError):
    """Raised when program execution fails."""

    pass


class AiderError(EvolveError):
    """Raised when Aider fails to apply changes."""

    pass


def handle_errors(operation: str) -> Callable[[F], F]:
    """
    Decorator for consistent error handling across the framework.

    Args:
        operation: Description of the operation being performed

    Example:
        @handle_errors("initializing evolution")
        def _initialize_evolution_run(self, ...):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except EvolveError:
                # Re-raise our own errors
                raise
            except FileNotFoundError as e:
                logger.error(f"File not found during {operation}: {e}")
                raise ConfigurationError(f"Required file missing: {e}") from e
            except ValueError as e:
                logger.error(f"Invalid value during {operation}: {e}")
                raise ConfigurationError(f"Invalid configuration: {e}") from e
            except Exception as e:
                logger.error(f"Unexpected error during {operation}: {e}", exc_info=True)
                raise EvolutionError(f"Failed to {operation}: {e}") from e

        return wrapper

    return decorator


def provide_suggestions(error: Exception) -> str:
    """
    Provide helpful suggestions based on the error type.

    Args:
        error: The exception that occurred

    Returns:
        A helpful suggestion string
    """
    if isinstance(error, ConfigurationError):
        if "API key" in str(error):
            return (
                "To fix this:\n"
                "1. Set OPEN_ROUTER_API_KEY environment variable\n"
                "2. Or create evolve.json with your configuration\n"
                "3. Or use set_config() to configure programmatically"
            )
        elif "file missing" in str(error):
            return "Make sure you're running from the correct directory and all required files are present."
    elif isinstance(error, ExecutionError):
        return (
            "Check that:\n"
            "1. Your Modal token is configured (run: modal token new)\n"
            "2. Required packages are available\n"
            "3. Your code has no syntax errors"
        )
    elif isinstance(error, EvolutionError):
        return (
            "The evolution process failed. Check:\n"
            "1. Your @evolve decorated function/class is valid\n"
            "2. Your @main_entrypoint returns a dict with metrics\n"
            "3. All dependencies are properly configured"
        )

    return "Check the logs above for more details."
