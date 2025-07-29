"""
Configuration management for the Evolv framework.
Provides a unified interface for all configuration options.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


@dataclass
class EvolveConfig:
    """Centralized configuration for the Evolv framework."""

    # API Configuration
    api_base: str = "https://openrouter.ai/api/v1"
    model: str = "openrouter/openai/gpt-4.1"
    temperature: float = 0.8

    # OpenRouter specific
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "openrouter/openai/gpt-4.1"

    # Evolution Configuration
    default_iterations: int = 3
    primary_metric: str = "fitness"
    sampling_strategy: str = "linear"

    # Execution Configuration
    modal_timeout: int = 600
    sandbox_packages: list[str] = field(
        default_factory=lambda: ["pandas", "scikit-learn", "numpy", "modal", "python-dotenv"]
    )

    # Aider Configuration
    aider_auto_commits: bool = False
    aider_yes_always: bool = True
    aider_ignore_file: Optional[str] = None
    aider_timeout: int = 60  # Aider command timeout in seconds

    # Async Configuration
    parallel_variants: int = 4
    max_concurrent_llm_calls: int = 5
    max_concurrent_executions: int = 10
    async_timeout: int = 300
    enable_progress_bar: bool = True

    # Executor Configuration
    executor_type: str = "modal"  # "modal", "local", "docker"

    # Local executor settings
    local_executor_timeout: int = 30

    # DSPy Configuration
    dspy_async_max_workers: int = 8
    max_inspiration_samples: int = 3

    # Sampling Configuration
    sampling_num_inspirations: int = 5  # Maintains original behavior and ensures enough samples

    # History Configuration
    history_record_limit: int = 20
    history_lookback_window: int = 5

    @classmethod
    def from_env(cls) -> "EvolveConfig":
        """Create config from environment variables with sensible defaults."""
        api_key = os.getenv("OPEN_ROUTER_API_KEY")
        return cls(
            openrouter_api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", cls.model),
            openrouter_model=os.getenv("OPENROUTER_MODEL", cls.openrouter_model),
            default_iterations=int(os.getenv("EVOLVE_ITERATIONS", "3")),
            primary_metric=os.getenv("PRIMARY_METRIC", cls.primary_metric),
            temperature=float(os.getenv("EVOLVE_TEMPERATURE", "0.8")),
            modal_timeout=int(os.getenv("MODAL_TIMEOUT", "600")),
            parallel_variants=int(os.getenv("EVOLVE_PARALLEL", "4")),
            executor_type=os.getenv("EVOLVE_EXECUTOR_TYPE", "modal"),
            local_executor_timeout=int(os.getenv("LOCAL_EXECUTOR_TIMEOUT", "30")),
        )

    @classmethod
    def from_file(cls, path: str = "evolve.json") -> "EvolveConfig":
        """Load config from JSON file."""
        config_path = Path(path)
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
                return cls(**data)
        return cls()

    def to_file(self, path: str = "evolve.json") -> None:
        """Save config to JSON file."""
        config_dict = {
            k: v
            for k, v in self.__dict__.items()
            if v is not None and k != "openrouter_api_key"  # Don't save API key
        }
        with open(path, "w") as f:
            json.dump(config_dict, f, indent=2)

    def validate(self) -> None:
        """Validate configuration and raise errors for missing required fields."""
        if not self.openrouter_api_key:
            raise ValueError(
                "API key not configured. Set OPEN_ROUTER_API_KEY environment variable or provide it in config file."
            )


# Global config instance
_config: Optional[EvolveConfig] = None


def get_config() -> EvolveConfig:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        # Try loading from file first, then fall back to env vars
        if Path("evolve.json").exists():
            _config = EvolveConfig.from_file()
        else:
            _config = EvolveConfig.from_env()
    return _config


def set_config(config: EvolveConfig) -> None:
    """Set the global config instance."""
    global _config
    _config = config
