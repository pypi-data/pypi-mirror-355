"""Test the enhanced LLM prompting with inspiration programs."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from evolve.config import EvolveConfig
from evolve.database import LinearSamplingStrategy, Program, ProgramDatabase
from evolve.dspy_async import AsyncDSPyModule
from evolve.prompting import ProgramInfo


@pytest.fixture
def mock_config():
    """Create mock config."""
    config = MagicMock(spec=EvolveConfig)
    config.model = "test-model"
    config.openrouter_api_key = "test-key"
    config.api_base = "http://test"
    config.temperature = 0.7
    config.dspy_async_max_workers = 8
    config.max_inspiration_samples = 3
    return config


@pytest.fixture
def sample_programs():
    """Create sample programs with different scores."""
    programs = []
    for i in range(5):
        program = Program(
            program_code=f"def classify(X, y):\n    # Version {i}\n    return model.fit(X, y)",
            evolve_code=f"def classify(X, y):\n    # Version {i}\n    return model.fit(X, y)",
            parent_id=str(i - 1) if i > 0 else None,
            success=True,
            stdout="",
            stderr="",
            metrics={"fitness": 0.7 + i * 0.05, "time": 1.0 - i * 0.1},
        )
        program.id = str(i)
        programs.append(program)
    return programs


class TestInspirationPrompting:
    """Test inspiration program functionality."""

    def test_database_sampling_with_single_program(self):
        """Test that with only one program, no inspirations are returned."""
        database = ProgramDatabase(LinearSamplingStrategy())
        program = Program(
            program_code="def classify(X, y): return model.fit(X, y)",
            evolve_code="def classify(X, y): return model.fit(X, y)",
            parent_id=None,
            success=True,
            stdout="",
            stderr="",
            metrics={"fitness": 0.75},
        )
        database.add(program)

        parent, inspirations = database.sample()
        assert parent == program
        assert len(inspirations) == 0  # No other programs to inspire from

    def test_database_sampling_with_multiple_programs(self, sample_programs):
        """Test that with multiple programs, inspirations are returned."""
        database = ProgramDatabase(LinearSamplingStrategy())
        for program in sample_programs:
            database.add(program)

        parent, inspirations = database.sample()
        # Parent should be the most recent (highest ID)
        assert parent.id == "4"
        # Should have inspirations from other programs
        assert len(inspirations) > 0
        # Inspirations should not include the parent
        assert all(insp.id != parent.id for insp in inspirations)

    @pytest.mark.asyncio
    async def test_dspy_module_with_no_inspirations(self, mock_config):
        """Test DSPy module when no inspirations are available."""
        with patch("evolve.dspy_async.dspy") as mock_dspy:
            # Mock the async predictor
            mock_predictor = AsyncMock()
            mock_predictor.return_value = MagicMock(improvement="Add feature engineering to improve accuracy")
            mock_dspy.asyncify.return_value = mock_predictor

            module = AsyncDSPyModule(mock_config)
            parent = Program(
                program_code="def classify(X, y): return model.fit(X, y)",
                evolve_code="def classify(X, y): return model.fit(X, y)",
                parent_id=None,
                success=True,
                stdout="",
                stderr="",
                metrics={"fitness": 0.75},
            )

            result = await module.suggest_improvement_async(
                parent, {"goal": "Improve accuracy", "primary_metric": "fitness"}, inspirations=None
            )

            assert "feature engineering" in result
            # Check that empty list was passed for inspirations
            mock_predictor.assert_called_once()
            call_args = mock_predictor.call_args.kwargs
            assert isinstance(call_args["current_program"], ProgramInfo)
            assert call_args["current_program"].score == 0.75
            assert isinstance(call_args["inspiration_programs"], list)
            assert len(call_args["inspiration_programs"]) == 0

    @pytest.mark.asyncio
    async def test_dspy_module_with_inspirations(self, mock_config, sample_programs):
        """Test DSPy module when inspirations are available."""
        with patch("evolve.dspy_async.dspy") as mock_dspy:
            # Mock the async predictor
            mock_predictor = AsyncMock()
            mock_predictor.return_value = MagicMock(improvement="Use cross-validation like the high-scoring variants")
            mock_dspy.asyncify.return_value = mock_predictor

            module = AsyncDSPyModule(mock_config)
            parent = sample_programs[0]  # Lowest scoring
            inspirations = sample_programs[2:5]  # Higher scoring programs

            result = await module.suggest_improvement_async(
                parent, {"goal": "Improve accuracy", "primary_metric": "fitness"}, inspirations=inspirations
            )

            assert "cross-validation" in result
            # Check that inspirations were passed and sorted by score
            mock_predictor.assert_called_once()
            call_args = mock_predictor.call_args.kwargs
            assert isinstance(call_args["current_program"], ProgramInfo)
            assert call_args["current_program"].score == 0.7  # Parent score
            assert isinstance(call_args["inspiration_programs"], list)
            assert len(call_args["inspiration_programs"]) == 3  # All 3 inspirations
            # Check they're sorted by score (descending)
            scores = [prog.score for prog in call_args["inspiration_programs"]]
            assert scores == sorted(scores, reverse=True)
            assert abs(scores[0] - 0.9) < 0.0001  # Highest scoring program

    @pytest.mark.asyncio
    async def test_dspy_module_limits_inspirations(self, mock_config, sample_programs):
        """Test that DSPy module limits inspirations to top 3."""
        with patch("evolve.dspy_async.dspy") as mock_dspy:
            # Mock the async predictor
            mock_predictor = AsyncMock()
            mock_predictor.return_value = MagicMock(improvement="Improvement based on top performers")
            mock_dspy.asyncify.return_value = mock_predictor

            module = AsyncDSPyModule(mock_config)
            parent = sample_programs[0]
            inspirations = sample_programs[1:]  # 4 programs

            result = await module.suggest_improvement_async(
                parent, {"goal": "Improve accuracy", "primary_metric": "fitness"}, inspirations=inspirations
            )

            # Check that only top 3 were passed
            mock_predictor.assert_called_once()
            call_args = mock_predictor.call_args.kwargs
            assert len(call_args["inspiration_programs"]) == 3
            # Verify they are the top 3 by score
            scores = [prog.score for prog in call_args["inspiration_programs"]]
            expected_scores = [0.9, 0.85, 0.8]
            for actual, expected in zip(scores, expected_scores):
                assert abs(actual - expected) < 0.0001

    def test_program_info_conversion(self, sample_programs):
        """Test ProgramInfo correctly converts from Program."""
        program = sample_programs[2]
        info = ProgramInfo.from_program(program, "fitness")

        assert info.code == program.evolve_code
        assert info.metrics == program.metrics
        assert info.score == program.metrics["fitness"]
        assert abs(info.score - 0.8) < 0.0001

    def test_evolution_workflow(self, sample_programs):
        """Test that the evolution workflow properly passes inspirations through iterations."""
        database = ProgramDatabase(LinearSamplingStrategy())

        # Iteration 0: Add initial program - no inspirations
        database.add(sample_programs[0])
        parent1, inspirations1 = database.sample()
        assert len(inspirations1) == 0  # First iteration has no inspirations

        # Iteration 1: Add more programs - now we have inspirations
        for prog in sample_programs[1:3]:
            database.add(prog)

        parent2, inspirations2 = database.sample()
        assert parent2.id == "2"  # Most recent program
        assert len(inspirations2) > 0  # Now we have inspirations
        assert all(insp.id != parent2.id for insp in inspirations2)

        # Iteration 2: Even more programs available
        for prog in sample_programs[3:5]:
            database.add(prog)

        parent3, inspirations3 = database.sample()
        assert parent3.id == "4"  # Most recent
        assert len(inspirations3) >= len(inspirations2)  # More inspirations available
