#!/usr/bin/env python
"""Test evolution with configurable logging and parameters.

This is a convenience script for testing the evolution framework with enhanced logging.
It wraps the example.py file and provides better visibility into the evolution process.

Usage:
    EVOLVE=1 python test_evolution.py
    DEBUG=1 EVOLVE=1 python test_evolution.py  # For debug logging
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from examples
sys.path.insert(0, str(Path(__file__).parent.parent))


def setup_logging(level=logging.INFO):
    """Setup logging with reduced noise from external libraries."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("evolution.log", mode="w")],
    )

    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    logging.getLogger("modal").setLevel(logging.WARNING)
    logging.getLogger("aider").setLevel(logging.WARNING)


def main():
    """Run evolution test with current configuration."""
    # Setup logging
    log_level = logging.DEBUG if os.environ.get("DEBUG") else logging.INFO
    setup_logging(log_level)

    logger = logging.getLogger(__name__)

    # Check if evolution mode is enabled
    if not os.environ.get("EVOLVE"):
        logger.warning("EVOLVE environment variable not set - evolution mode disabled!")
        logger.warning("To enable evolution, run: EVOLVE=1 python test_evolution.py")

    # Log configuration
    logger.info("=" * 60)
    logger.info("Evolution Test Configuration:")
    logger.info(
        f"  EVOLVE: {os.environ.get('EVOLVE', 'not set')} {'⚠️ EVOLUTION DISABLED!' if not os.environ.get('EVOLVE') else '✓'}"
    )
    logger.info(f"  EXECUTOR_TYPE: {os.environ.get('EVOLVE_EXECUTOR_TYPE', 'modal')}")
    logger.info(f"  ITERATIONS: {os.environ.get('EVOLVE_ITERATIONS', '3')}")
    logger.info(f"  PARALLEL_VARIANTS: {os.environ.get('EVOLVE_PARALLEL', '4')}")
    logger.info(f"  PRIMARY_METRIC: {os.environ.get('PRIMARY_METRIC', 'fitness')}")
    logger.info(f"  DEBUG: {os.environ.get('DEBUG', 'not set')}")
    logger.info("=" * 60)

    # Import and run example
    try:
        # Get example to run from command line or default
        if len(sys.argv) > 1:
            example_file = sys.argv[1]
            logger.info(f"Running example from: {example_file}")

            # Import the example dynamically
            import importlib.util

            spec = importlib.util.spec_from_file_location("example_module", example_file)
            example_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(example_module)
            example_main = example_module.main
        else:
            # Default to breast_cancer_example
            logger.info("No example specified, using default: examples/breast_cancer_example.py")
            from examples.breast_cancer_example import main as example_main

        logger.info("Starting evolution process...")
        result = example_main()
        logger.info(f"Evolution completed with result: {result}")

        # Also log to console for visibility
        print("\n" + "=" * 60)
        print("Evolution completed successfully!")
        print("Check evolution.log for details")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Evolution failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
