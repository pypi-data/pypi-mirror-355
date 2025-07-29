"""Tests for MAP-Elites evolution strategy."""

import ast

import numpy as np
import pytest

from evolve.database import Program, ProgramDatabase
from evolve.strategies.base import StrategyFactory
from evolve.strategies.map_elites import (
    BehaviorDescriptor,
    FeatureExtractor,
    GridSpecification,
    MAPElitesArchive,
    MAPElitesStrategy,
)


@pytest.fixture
def sample_program():
    """Create a sample program for testing."""
    return Program(
        program_code="def test_func():\n    return 42",
        evolve_code="def test_func():\n    return 42",
        success=True,
        metrics={"fitness": 0.8, "execution_time": 0.5, "memory_bytes": 1024 * 1024},
    )


@pytest.fixture
def grid_spec():
    """Create a test grid specification."""
    return GridSpecification(dimensions=[("execution_time", (0.1, 1.0), 10), ("code_length", (10, 100), 10)])


class TestBehaviorDescriptor:
    """Test BehaviorDescriptor class."""

    def test_to_grid_coords(self, grid_spec):
        """Test conversion of features to grid coordinates."""
        descriptor = BehaviorDescriptor({"execution_time": 0.5, "code_length": 50})
        coords = descriptor.to_grid_coords(grid_spec)

        # 0.5 in range [0.1, 1.0] = normalized to ~0.44, bin 4
        # 50 in range [10, 100] = normalized to ~0.44, bin 4
        assert coords == (4, 4)

    def test_to_grid_coords_clipping(self, grid_spec):
        """Test that values outside bounds are clipped."""
        descriptor = BehaviorDescriptor({"execution_time": 2.0, "code_length": -10})
        coords = descriptor.to_grid_coords(grid_spec)

        # 2.0 is above max, should clip to bin 9
        # -10 is below min, should clip to bin 0
        assert coords == (9, 0)


class TestGridSpecification:
    """Test GridSpecification class."""

    def test_get_total_cells(self, grid_spec):
        """Test total cell calculation."""
        assert grid_spec.get_total_cells() == 100  # 10 * 10

    def test_get_shape(self, grid_spec):
        """Test grid shape."""
        assert grid_spec.get_shape() == (10, 10)


class TestMAPElitesArchive:
    """Test MAPElitesArchive class."""

    def test_add_new_cell(self, grid_spec, sample_program):
        """Test adding program to empty cell."""
        archive = MAPElitesArchive(grid_spec)
        descriptor = BehaviorDescriptor({"execution_time": 0.5, "code_length": 50})

        improved = archive.add(sample_program, descriptor)

        assert improved
        assert len(archive.archive) == 1
        assert archive.get_coverage() == 0.01  # 1/100

    def test_add_improvement(self, grid_spec, sample_program):
        """Test replacing program with better one."""
        archive = MAPElitesArchive(grid_spec)
        descriptor = BehaviorDescriptor({"execution_time": 0.5, "code_length": 50})

        # Add initial program
        archive.add(sample_program, descriptor)

        # Create better program
        better_program = Program(
            program_code="def test(): return 84",
            evolve_code="def test(): return 84",
            success=True,
            metrics={"fitness": 0.9},  # Higher fitness
        )

        improved = archive.add(better_program, descriptor)

        assert improved
        assert len(archive.archive) == 1  # Still one cell
        assert archive.archive[(4, 4)].score == 0.9

    def test_no_improvement(self, grid_spec, sample_program):
        """Test not replacing program with worse one."""
        archive = MAPElitesArchive(grid_spec)
        descriptor = BehaviorDescriptor({"execution_time": 0.5, "code_length": 50})

        # Add initial program
        archive.add(sample_program, descriptor)

        # Create worse program
        worse_program = Program(
            program_code="def test(): return 21",
            evolve_code="def test(): return 21",
            success=True,
            metrics={"fitness": 0.7},  # Lower fitness
        )

        improved = archive.add(worse_program, descriptor)

        assert not improved
        assert archive.archive[(4, 4)].score == 0.8  # Original remains

    def test_sample_uniform(self, grid_spec):
        """Test uniform sampling from archive."""
        archive = MAPElitesArchive(grid_spec)

        # Add multiple programs
        for i in range(5):
            program = Program(
                program_code=f"def func{i}(): pass",
                evolve_code=f"def func{i}(): pass",
                success=True,
                metrics={"fitness": 0.5 + i * 0.1},
            )
            descriptor = BehaviorDescriptor({"execution_time": 0.1 + i * 0.2, "code_length": 20 + i * 10})
            archive.add(program, descriptor)

        # Sample 3 programs
        samples = archive.sample_uniform(3)

        assert len(samples) == 3
        assert all(isinstance(p, Program) for p in samples)

    def test_sample_curiosity(self, grid_spec):
        """Test curiosity-based sampling."""
        archive = MAPElitesArchive(grid_spec)

        # Add clustered programs (should be selected less)
        for i in range(3):
            program = Program(
                program_code=f"def clustered{i}(): pass",
                evolve_code=f"def clustered{i}(): pass",
                success=True,
                metrics={"fitness": 0.5},
            )
            descriptor = BehaviorDescriptor({"execution_time": 0.5 + i * 0.01, "code_length": 50 + i})
            archive.add(program, descriptor)

        # Add isolated program (should be selected more)
        isolated = Program(
            program_code="def isolated(): pass",
            evolve_code="def isolated(): pass",
            success=True,
            metrics={"fitness": 0.6},
        )
        descriptor = BehaviorDescriptor({"execution_time": 0.9, "code_length": 90})
        archive.add(isolated, descriptor)

        # Sample with curiosity
        samples = archive.sample_curiosity(10)

        assert len(samples) == 10  # Should sample with replacement
        # The isolated program should appear in samples

    def test_get_elite_grid(self, grid_spec):
        """Test elite grid generation."""
        archive = MAPElitesArchive(grid_spec)

        # Add some programs
        program1 = Program(
            program_code="def f1(): pass",
            evolve_code="def f1(): pass",
            success=True,
            metrics={"fitness": 0.8},
        )
        archive.add(program1, BehaviorDescriptor({"execution_time": 0.5, "code_length": 50}))

        grid = archive.get_elite_grid()

        assert grid.shape == (10, 10)
        assert grid[4, 4] == 0.8
        assert np.isnan(grid[0, 0])  # Empty cell


class TestFeatureExtractor:
    """Test FeatureExtractor class."""

    def test_default_extractors(self, sample_program):
        """Test default feature extractors."""
        extractor = FeatureExtractor()

        # Test code length
        assert extractor.extractors["code_length"](sample_program) == len(sample_program.evolve_code)

        # Test num lines
        assert extractor.extractors["num_lines"](sample_program) == 2

        # Test metrics extraction
        assert extractor.extractors["execution_time"](sample_program) == 0.5
        assert extractor.extractors["memory_usage"](sample_program) == 1.0  # 1MB

    def test_complexity_calculation(self):
        """Test cyclomatic complexity calculation."""
        extractor = FeatureExtractor()

        # Simple function
        simple = Program(
            program_code="def f(): return 1",
            evolve_code="def f(): return 1",
            success=True,
            metrics={},
        )
        assert extractor._calculate_complexity(simple) == 1.0

        # Function with conditions
        complex_code = """
def f(x):
    if x > 0:
        if x > 10:
            return 1
    else:
        return 0
    for i in range(x):
        pass
"""
        complex_prog = Program(
            program_code=complex_code,
            evolve_code=complex_code,
            success=True,
            metrics={},
        )
        assert extractor._calculate_complexity(complex_prog) == 4.0  # 1 base + 2 if + 1 for

    def test_function_counting(self):
        """Test function counting."""
        extractor = FeatureExtractor()

        code = """
def f1():
    pass

def f2():
    def inner():
        pass
    return inner

class C:
    def method(self):
        pass
"""
        program = Program(
            program_code=code,
            evolve_code=code,
            success=True,
            metrics={},
        )

        assert extractor._count_functions(program) == 4.0  # f1, f2, inner, method

    def test_nesting_calculation(self):
        """Test max nesting depth calculation."""
        extractor = FeatureExtractor()

        nested_code = """
def f():
    if True:
        for i in range(10):
            while True:
                if False:
                    pass
"""
        program = Program(
            program_code=nested_code,
            evolve_code=nested_code,
            success=True,
            metrics={},
        )

        assert extractor._calculate_max_nesting(program) == 4.0

    def test_extract_features(self, sample_program):
        """Test extracting multiple features."""
        extractor = FeatureExtractor()

        descriptor = extractor.extract(sample_program, ["code_length", "execution_time", "unknown_feature"])

        assert descriptor.features["code_length"] == len(sample_program.evolve_code)
        assert descriptor.features["execution_time"] == 0.5
        assert descriptor.features["unknown_feature"] == 0.0  # Default for unknown

    def test_custom_extractor(self):
        """Test registering custom extractor."""
        extractor = FeatureExtractor()

        # Register custom extractor
        def count_returns(program: Program) -> float:
            tree = ast.parse(program.evolve_code)
            return float(sum(1 for node in ast.walk(tree) if isinstance(node, ast.Return)))

        extractor.register_custom_extractor("num_returns", count_returns)

        program = Program(
            program_code="def f():\n    if True:\n        return 1\n    return 2",
            evolve_code="def f():\n    if True:\n        return 1\n    return 2",
            success=True,
            metrics={},
        )

        descriptor = extractor.extract(program, ["num_returns"])
        assert descriptor.features["num_returns"] == 2.0


class TestMAPElitesStrategy:
    """Test MAPElitesStrategy class."""

    def test_initialization(self, sample_program):
        """Test strategy initialization."""
        strategy = MAPElitesStrategy()
        config = {
            "features": [
                ("execution_time", (0.1, 1.0), 5),
                ("code_length", (10, 100), 5),
            ],
            "selection": "curiosity",
        }

        strategy.initialize(config, sample_program)

        assert strategy.archive is not None
        assert strategy.selection_method == "curiosity"
        assert strategy.feature_names == ["execution_time", "code_length"]
        assert len(strategy.archive.archive) == 1  # Initial program added

    def test_select_parents_from_archive(self, sample_program):
        """Test parent selection from archive."""
        strategy = MAPElitesStrategy()
        config = {"features": [("code_length", (10, 100), 5)]}
        strategy.initialize(config, sample_program)

        # Create dummy database
        from evolve.database import LinearSamplingStrategy

        db = ProgramDatabase(LinearSamplingStrategy())

        # Add more programs to archive
        for i in range(3):
            prog = Program(
                program_code=f"def f{i}(): pass",
                evolve_code=f"def f{i}(): pass",
                success=True,
                metrics={"fitness": 0.5 + i * 0.1},
            )
            descriptor = strategy.feature_extractor.extract(prog, strategy.feature_names)
            strategy.archive.add(prog, descriptor)

        parents = strategy.select_parents(db, count=2)

        assert len(parents) == 2
        assert all(isinstance(p, Program) for p in parents)

    def test_should_accept(self):
        """Test acceptance criteria."""
        strategy = MAPElitesStrategy()

        success_prog = Program(program_code="", evolve_code="", success=True, metrics={})
        failure_prog = Program(program_code="", evolve_code="", success=False, metrics={})

        from evolve.database import LinearSamplingStrategy

        db = ProgramDatabase(LinearSamplingStrategy())

        assert strategy.should_accept(success_prog, db)
        assert not strategy.should_accept(failure_prog, db)

    def test_update_state(self, sample_program):
        """Test state update with new program."""
        strategy = MAPElitesStrategy()
        config = {"features": [("code_length", (10, 100), 5)]}
        strategy.initialize(config, sample_program)

        from evolve.database import LinearSamplingStrategy

        db = ProgramDatabase(LinearSamplingStrategy())

        new_prog = Program(
            program_code="def new_func(): return 100",
            evolve_code="def new_func(): return 100",
            success=True,
            metrics={"fitness": 0.9},
        )

        strategy.update_state(new_prog, db)

        assert strategy.total_evaluations == 2
        assert strategy.generation == 1

    def test_get_strategy_metrics(self, sample_program):
        """Test metrics reporting."""
        strategy = MAPElitesStrategy()
        config = {"features": [("code_length", (10, 100), 10)]}
        strategy.initialize(config, sample_program)

        metrics = strategy.get_strategy_metrics()

        assert metrics["type"] == "MAP-Elites"
        assert "coverage" in metrics
        assert "occupied_cells" in metrics
        assert "total_cells" in metrics
        assert metrics["total_evaluations"] == 1

    def test_visualization_data(self, sample_program):
        """Test archive visualization data generation."""
        strategy = MAPElitesStrategy()
        config = {
            "features": [
                ("execution_time", (0.1, 1.0), 5),
                ("code_length", (10, 100), 5),
            ]
        }
        strategy.initialize(config, sample_program)

        viz_data = strategy.get_archive_visualization()

        assert "grid" in viz_data
        assert "dimensions" in viz_data
        assert "coverage_history" in viz_data
        assert "events" in viz_data

        assert len(viz_data["dimensions"]) == 2
        assert viz_data["dimensions"][0]["name"] == "execution_time"

    def test_custom_extractors_in_config(self):
        """Test using custom extractors via config."""
        strategy = MAPElitesStrategy()

        def custom_metric(program: Program) -> float:
            return len(program.evolve_code) * 2

        config = {
            "features": [("custom", (0, 200), 10)],
            "custom_extractors": {"custom": custom_metric},
        }

        sample_prog = Program(
            program_code="def f(): pass",
            evolve_code="def f(): pass",
            success=True,
            metrics={"fitness": 0.5},
        )

        strategy.initialize(config, sample_prog)

        assert "custom" in strategy.feature_extractor.extractors
        descriptor = strategy.feature_extractor.extract(sample_prog, ["custom"])
        assert descriptor.features["custom"] == len(sample_prog.evolve_code) * 2


class TestStrategyRegistration:
    """Test that MAP-Elites is properly registered."""

    def test_map_elites_registered(self):
        """Test MAP-Elites is in factory."""
        assert "map_elites" in StrategyFactory.list_strategies()

    def test_create_map_elites(self):
        """Test creating MAP-Elites via factory."""
        strategy = StrategyFactory.create("map_elites")
        assert isinstance(strategy, MAPElitesStrategy)
