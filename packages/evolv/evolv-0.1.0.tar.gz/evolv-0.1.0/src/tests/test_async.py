"""Tests for async evolution components."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from evolve.database import Program, ProgramDatabase
from evolve.dspy_async import AsyncDSPyModule
from evolve.executor_async import AsyncLocalExecutor


@pytest.fixture
def sample_program():
    """Create a sample program."""
    return Program(
        program_code="def test(): return 42",
        evolve_code="def test(): return 42",
        success=True,
        metrics={"fitness": 0.8},
        id="1",
    )


@pytest.fixture
def mock_evolution_target():
    """Create a mock evolution target."""
    target = MagicMock()
    target.name = "test_function"
    target.goal = "Maximize performance"
    target.source = "def test_function(): return 42"
    target.original_full_code = "def test_function(): return 42"
    target.original_file_path = "/tmp/test.py"
    target.is_class = False
    target.mount_dir = None
    target.extra_packages = None
    return target


class TestAsyncDSPyModule:
    """Test the async DSPy module."""

    @pytest.mark.asyncio
    async def test_suggest_improvement(self, sample_program):
        """Test async improvement suggestion using real DSPy."""
        from evolve.config import EvolveConfig

        config = EvolveConfig(
            openrouter_api_key="test_key",
            openrouter_model="test_model",
        )

        # Create a mock async predictor
        mock_predictor = AsyncMock()
        mock_result = MagicMock()
        mock_result.improvement = "Optimize the algorithm"
        mock_predictor.return_value = mock_result

        # Mock the AsyncDSPyModule's setup to avoid real DSPy calls
        with patch.object(AsyncDSPyModule, "_setup_dspy"):
            module = AsyncDSPyModule(config)
            module.async_predictor = mock_predictor  # Inject our mock

            improvement = await module.suggest_improvement_async(
                sample_program,
                {"goal": "Improve performance", "primary_metric": "fitness"},
            )

            assert improvement == "Optimize the algorithm"
            assert module.request_count == 1

            # Verify the predictor was called with correct args
            mock_predictor.assert_called_once()
            call_args = mock_predictor.call_args[1]
            assert call_args["goal"] == "Improve performance"
            assert call_args["primary_metric"] == "fitness"
            # Check that current_program is a ProgramInfo object
            assert hasattr(call_args["current_program"], "code")
            assert hasattr(call_args["current_program"], "metrics")

    # TODO: This test needs to be updated for the new Pydantic-based implementation
    # @pytest.mark.asyncio
    # async def test_context_aware_code_building(self, sample_program):
    #     """Test context-aware code building for DSPy."""
    #     from evolve.config import EvolveConfig

    #     config = EvolveConfig()

    #     # Mock DSPy setup
    #     with patch.object(AsyncDSPyModule, "_setup_dspy"):
    #         module = AsyncDSPyModule(config)

    #         # Add some history
    #         module._track_improvement("Previous improvement 1", 0.7)
    #         module._track_improvement("Previous improvement 2", 0.8)

    #         code_with_context = module._build_context_aware_code(
    #             sample_program,
    #             {"goal": "Maximize fitness", "primary_metric": "fitness"},
    #         )

    #         assert "# Evolution Context:" in code_with_context
    #         assert "# Goal: Maximize fitness" in code_with_context
    #         assert "fitness" in code_with_context
    #         assert "Previous:" in code_with_context
    #         assert sample_program.program_code in code_with_context


class TestAsyncExecutors:
    """Test async executors."""

    @pytest.mark.asyncio
    async def test_local_executor_success(self, mock_evolution_target):
        """Test successful local execution."""

        executor = AsyncLocalExecutor()

        # Create a simple program that writes metrics
        code = """
import json
metrics = {"fitness": 0.95, "accuracy": 0.88}
with open("metrics.json", "w") as f:
    json.dump(metrics, f)
"""

        result = await executor.run_async(code, mock_evolution_target, timeout=5)

        assert result.success
        assert result.metrics["fitness"] == 0.95
        assert result.metrics["accuracy"] == 0.88

    @pytest.mark.asyncio
    async def test_local_executor_failure(self, mock_evolution_target):
        """Test failed local execution."""

        executor = AsyncLocalExecutor()

        # Code with syntax error
        code = "def broken("

        result = await executor.run_async(code, mock_evolution_target, timeout=5)

        assert not result.success
        assert "SyntaxError" in result.stderr

    @pytest.mark.asyncio
    async def test_local_executor_timeout(self, mock_evolution_target):
        """Test timeout handling."""

        executor = AsyncLocalExecutor()

        # Code that hangs
        code = """
import time
time.sleep(10)
"""

        result = await executor.run_async(code, mock_evolution_target, timeout=1)

        assert not result.success
        assert result.error and "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_local_executor_memory_error(self, mock_evolution_target):
        """Test handling of memory errors."""

        executor = AsyncLocalExecutor()

        # Code that will raise MemoryError
        code = """
# Force a MemoryError by allocating too much
raise MemoryError("Out of memory")
"""

        result = await executor.run_async(code, mock_evolution_target, timeout=5)

        # Should fail with MemoryError
        assert not result.success
        assert "MemoryError" in result.stderr


@pytest_asyncio.fixture
async def async_database():
    """Create an async-ready database."""
    from evolve.database import LinearSamplingStrategy

    db = ProgramDatabase(LinearSamplingStrategy())
    # Add some test programs
    for i in range(5):
        db.add(
            Program(
                program_code=f"def func{i}(): return {i}",
                evolve_code=f"def func{i}(): return {i}",
                success=True,
                metrics={"fitness": 0.5 + i * 0.1},
                id=str(i),
            )
        )
    return db


class TestAsyncCoordinator:
    """Test async coordinator functionality."""

    @pytest.mark.asyncio
    async def test_parallel_variant_generation(self, async_database, mock_evolution_target):
        """Test parallel generation of variants."""
        from evolve.coordinator import EvolutionCoordinator

        # Mock the necessary components
        with (
            patch("evolve.dspy_async.AsyncDSPyModule") as mock_dspy_class,
            patch("evolve.aider_async.AsyncAiderModule") as mock_aider_class,
            patch("evolve.executor_async.create_async_executor") as mock_executor_factory,
        ):
            # Setup mocks
            mock_dspy = AsyncMock()
            mock_dspy.suggest_improvement_async = AsyncMock(return_value="Improve this")
            mock_dspy_class.return_value = mock_dspy

            mock_aider = AsyncMock()
            mock_aider.apply_changes_async = AsyncMock(return_value="def improved(): pass")
            mock_aider_class.return_value = mock_aider

            mock_executor = AsyncMock()
            mock_executor.run = AsyncMock(return_value=MagicMock(success=True, metrics={"fitness": 0.9}))
            mock_executor_factory.return_value = mock_executor

            # Create coordinator with config
            from evolve.config import EvolveConfig, set_config

            config = EvolveConfig(parallel_variants=3)
            set_config(config)

            coordinator = EvolutionCoordinator()
            coordinator.database = async_database
            coordinator.target = mock_evolution_target

            # Track timing
            start_time = time.time()

            # Generate variants in parallel
            results = await coordinator._generate_variants_parallel(
                database=async_database,
                strategy=None,
                llm_module=mock_dspy,
                aider_module=mock_aider,
                executor=mock_executor,
                count=3,
            )

            duration = time.time() - start_time

            # Should have generated 3 variants
            assert len(results) == 3

            # All should be successful
            assert all(r.success for r in results)

            # Should have been called in parallel (check timing is reasonable)
            assert duration < 2.0  # Should be much faster than sequential

            # Verify parallel calls
            assert mock_dspy.suggest_improvement_async.call_count == 3

    @pytest.mark.asyncio
    async def test_semaphore_limiting(self):
        """Test that semaphores properly limit concurrency."""
        from evolve.coordinator import EvolutionCoordinator

        call_times = []
        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def mock_llm_call():
            nonlocal current_concurrent, max_concurrent

            async with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
                call_times.append(time.time())

            # Simulate API call
            await asyncio.sleep(0.1)

            async with lock:
                current_concurrent -= 1

            return "result"

        # Create coordinator with limited concurrency
        from evolve.config import EvolveConfig, set_config

        config = EvolveConfig(max_concurrent_llm_calls=2)
        set_config(config)
        coordinator = EvolutionCoordinator()

        # Test semaphore limiting directly
        semaphore = asyncio.Semaphore(2)

        async def limited_call():
            async with semaphore:
                return await mock_llm_call()

        # Run all tasks with semaphore
        results = await asyncio.gather(*[limited_call() for _ in range(10)])

        # Check that max concurrent never exceeded limit
        assert max_concurrent <= 2
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_error_handling_in_parallel_generation(self, async_database, mock_evolution_target):
        """Test that errors in one variant don't affect others."""
        from evolve.coordinator import EvolutionCoordinator

        call_count = 0

        async def mock_suggest_improvement(program, context, inspirations=None):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Simulated API error")
            return f"Improvement {call_count}"

        with (
            patch("evolve.dspy_async.AsyncDSPyModule") as mock_dspy_class,
            patch("evolve.aider_async.AsyncAiderModule") as mock_aider_class,
            patch("evolve.executor_async.create_async_executor") as mock_executor_factory,
        ):
            # Setup mocks
            mock_dspy = AsyncMock()
            mock_dspy.suggest_improvement_async = mock_suggest_improvement
            mock_dspy_class.return_value = mock_dspy

            mock_aider = AsyncMock()
            mock_aider.apply_changes_async = AsyncMock(return_value="def improved(): pass")
            mock_aider_class.return_value = mock_aider

            mock_executor = AsyncMock()
            mock_executor.run = AsyncMock(return_value=MagicMock(success=True, metrics={"fitness": 0.9}))
            mock_executor_factory.return_value = mock_executor

            # Create coordinator
            coordinator = EvolutionCoordinator()
            coordinator.database = async_database
            coordinator.target = mock_evolution_target

            # Generate variants (one will fail)
            results = await coordinator._generate_variants_parallel(
                database=async_database,
                strategy=None,
                llm_module=mock_dspy,
                aider_module=mock_aider,
                executor=mock_executor,
                count=3,
            )

            # Should still get results for successful variants
            assert len(results) >= 2  # At least 2 should succeed
            assert any(r.success for r in results)  # Some should be successful


class TestAsyncPerformance:
    """Performance benchmarks for async vs sync operations."""

    @pytest.mark.asyncio
    async def test_async_vs_sync_performance(self):
        """Benchmark async parallel execution vs sequential."""

        async def async_operation(delay: float) -> float:
            start = time.time()
            await asyncio.sleep(delay)
            return time.time() - start

        def sync_operation(delay: float) -> float:
            start = time.time()
            time.sleep(delay)
            return time.time() - start

        # Test parallel async execution
        async_start = time.time()
        async_results = await asyncio.gather(*[async_operation(0.1) for _ in range(5)])
        async_duration = time.time() - async_start

        # Test sequential sync execution
        sync_start = time.time()
        sync_results = [sync_operation(0.1) for _ in range(5)]
        sync_duration = time.time() - sync_start

        # Async should be significantly faster
        assert async_duration < sync_duration / 2
        assert len(async_results) == len(sync_results) == 5

    @pytest.mark.asyncio
    async def test_thread_pool_for_blocking_io(self):
        """Test using thread pool for blocking I/O operations."""
        import os
        import tempfile

        # Simulate blocking I/O with file operations
        def blocking_io_operation(n: int) -> str:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(f"Data {n}\n" * 1000)
                name = f.name

            # Read it back
            with open(name, "r") as f:
                data = f.read()

            os.unlink(name)
            return f"Processed {len(data)} bytes"

        # Run in thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=4) as executor:
            start = time.time()
            results = await asyncio.gather(
                *[loop.run_in_executor(executor, blocking_io_operation, i) for i in range(10)]
            )
            duration = time.time() - start

        # Should complete reasonably fast with parallel execution
        assert len(results) == 10
        assert all("Processed" in r for r in results)
        assert duration < 2.0  # Should be fast with thread pool


class TestAsyncIntegration:
    """Integration tests for async components."""

    @pytest.mark.asyncio
    async def test_full_async_evolution_iteration(self, mock_evolution_target):
        """Test async evolution setup and module initialization."""
        from evolve.config import EvolveConfig
        from evolve.coordinator import EvolutionCoordinator

        # Create a minimal config
        config = EvolveConfig(
            openrouter_api_key="test_key",
            executor_type="local",
            parallel_variants=2,
            default_iterations=1,
        )

        with (
            patch("evolve.coordinator.get_config", return_value=config),
            patch("evolve.dspy_async.AsyncDSPyModule") as mock_dspy_class,
            patch("evolve.aider_async.AsyncAiderModule") as mock_aider_class,
            patch("evolve.executor_async.create_async_executor") as mock_executor_factory,
        ):
            # Setup executor mock
            mock_executor = AsyncMock()
            mock_executor.run = AsyncMock(return_value=MagicMock(success=True, metrics={"fitness": 0.9}))
            mock_executor_factory.return_value = mock_executor

            # Create coordinator
            coordinator = EvolutionCoordinator()
            coordinator.target = mock_evolution_target

            # Start evolution (this will initialize the modules)
            await coordinator._evolve_async()

            # Verify modules were created
            assert mock_dspy_class.called
            assert mock_aider_class.called
            assert mock_executor_factory.called
