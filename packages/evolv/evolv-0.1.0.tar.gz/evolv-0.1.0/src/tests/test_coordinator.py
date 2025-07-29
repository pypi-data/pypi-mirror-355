"""Tests for the unified evolution coordinator."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from evolve.coordinator import EvolutionCoordinator
from evolve.database import Program
from evolve.executor_async import ExecutionResult


@pytest.fixture
def temp_script():
    """Create a temporary Python script for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
def optimize_me(x):
    return x * 2

@main_entrypoint
def main():
    result = optimize_me(10)
    return {"fitness": result}

if __name__ == "__main__":
    main()
""")
        yield f.name
    os.unlink(f.name)


class TestUnifiedCoordinator:
    """Test the unified evolution coordinator."""

    def test_evolve_decorator(self):
        """Test the @evolve decorator."""
        coordinator = EvolutionCoordinator()

        @coordinator.evolve(goal="Maximize performance", strategy="linear", iterations=5)
        def test_function(x):
            return x * 2

        assert coordinator.target is not None
        assert coordinator.target.name == "test_function"
        assert coordinator.target.goal == "Maximize performance"
        assert coordinator.target.iterations == 5
        assert coordinator.target.sampling_strategy_name == "linear"

    def test_main_entrypoint_decorator(self):
        """Test the @main_entrypoint decorator."""
        coordinator = EvolutionCoordinator()

        @coordinator.main_entrypoint
        def main():
            return {"fitness": 42}

        assert coordinator.main_func_reference is not None
        assert coordinator.main_script_path is not None

        # Test normal execution (no EVOLVE env var)
        result = main()
        assert result == {"fitness": 42}

        # Check metrics.json was created
        assert Path("metrics.json").exists()
        with open("metrics.json") as f:
            metrics = json.load(f)
        assert metrics == {"fitness": 42}

        # Clean up
        os.unlink("metrics.json")

    @pytest.mark.asyncio
    async def test_evolve_async_basic(self):
        """Test basic async evolution."""
        coordinator = EvolutionCoordinator()

        # Setup target
        @coordinator.evolve(goal="Optimize performance")
        def test_func():
            return 42

        # Mock components
        mock_llm = AsyncMock()
        mock_llm.suggest_improvement_async.return_value = "Improve algorithm"

        mock_aider = AsyncMock()
        mock_aider.apply_changes_async.return_value = "def test_func(): return 84"

        mock_executor = AsyncMock()
        mock_executor.run.return_value = ExecutionResult(
            success=True,
            metrics={"fitness": 0.9},
            stdout="Success",
            stderr="",
        )

        # Patch imports and run evolution
        with patch("evolve.aider_async.AsyncAiderModule") as mock_aider_class:
            with patch("evolve.dspy_async.AsyncDSPyModule") as mock_dspy_class:
                with patch("evolve.executor_async.create_async_executor") as mock_exec_factory:
                    # Setup mocks
                    mock_dspy_class.return_value.__aenter__.return_value = mock_llm
                    mock_aider_class.return_value.__aenter__.return_value = mock_aider
                    mock_exec_factory.return_value = mock_executor

                    # Run evolution
                    await coordinator._evolve_async()

        # Verify calls
        assert mock_llm.suggest_improvement_async.called
        assert mock_aider.apply_changes_async.called
        assert mock_executor.run.called

    @pytest.mark.asyncio
    async def test_parallel_variant_generation(self):
        """Test that variants are generated in parallel."""
        coordinator = EvolutionCoordinator()

        # Setup target
        @coordinator.evolve(goal="Optimize")
        def test_func():
            return 42

        # Track timing of variant creation
        variant_times = []

        async def mock_create_variant(parent, inspirations, llm, aider, executor, name):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)  # Simulate work
            end = asyncio.get_event_loop().time()
            variant_times.append((name, start, end))
            return Program(
                program_code=f"def test(): return {name}",
                evolve_code=f"def test(): return {name}",
                success=True,
                metrics={"fitness": 0.8},
            )

        # Mock database with programs
        mock_db = MagicMock()
        mock_db.sample.return_value = (
            Program(program_code="def test(): return 1", evolve_code="def test(): return 1"),
            [],
        )

        # Test parallel generation
        with patch.object(coordinator, "_create_variant", side_effect=mock_create_variant):
            variants = await coordinator._generate_variants_parallel(mock_db, None, None, None, None, 4)

        assert len(variants) == 4

        # Check that variants were created in parallel (overlapping times)
        # If sequential, total time would be ~0.4s
        # If parallel, total time should be ~0.1s
        total_time = max(t[2] for t in variant_times) - min(t[1] for t in variant_times)
        assert total_time < 0.2  # Allow some overhead

    def test_evolution_mode_integration(self):
        """Test full evolution mode integration."""
        coordinator = EvolutionCoordinator()

        # Setup decorators
        @coordinator.evolve(goal="Optimize", iterations=1)
        def optimize_me(x):
            return x * 2

        @coordinator.main_entrypoint
        def main():
            result = optimize_me(10)
            return {"fitness": result}

        # Mock async evolution
        with patch.object(coordinator, "_evolve_async") as mock_evolve:
            mock_evolve.return_value = None

            # Trigger evolution mode
            os.environ["EVOLVE"] = "1"
            try:
                result = main()
                assert result == {"status": "Evolution process initiated and concluded."}
                mock_evolve.assert_called_once()
            finally:
                del os.environ["EVOLVE"]

    def test_extract_entity(self):
        """Test entity extraction from code."""
        coordinator = EvolutionCoordinator()

        code = """
def helper():
    return 1

def target_func(x):
    return x * helper()

class NotThis:
    pass
"""

        extracted = coordinator._extract_entity(code, "target_func")
        assert "def target_func(x):" in extracted
        assert "return x * helper()" in extracted
        assert "class NotThis" not in extracted
