"""Tests for the modular strategy system."""

import pytest

from evolve.database import Program, ProgramDatabase
from evolve.strategies import (
    LinearStrategy,
    RandomStrategy,
    StrategyFactory,
    TournamentStrategy,
)


@pytest.fixture
def sample_program():
    """Create a sample program for testing."""
    return Program(
        program_code="def test(): return 42",
        evolve_code="def test(): return 42",
        success=True,
        metrics={"fitness": 0.8, "accuracy": 0.9},
        id="1",
    )


@pytest.fixture
def sample_database(sample_program):
    """Create a sample database with programs."""
    from evolve.database import LinearSamplingStrategy

    db = ProgramDatabase(LinearSamplingStrategy())

    # Add multiple programs with different metrics
    for i in range(5):
        program = Program(
            program_code=f"def test(): return {i}",
            evolve_code=f"def test(): return {i}",
            success=True,
            metrics={"fitness": 0.1 * i, "accuracy": 0.2 * i},
            id=str(i),
        )
        db.add(program)

    return db


class TestStrategyFactory:
    """Test the strategy factory."""

    def test_register_and_create(self):
        """Test registering and creating strategies."""
        # Basic strategies should already be registered
        assert "linear" in StrategyFactory.list_strategies()
        assert "random" in StrategyFactory.list_strategies()
        assert "tournament" in StrategyFactory.list_strategies()

        # Create strategies
        linear = StrategyFactory.create("linear")
        assert isinstance(linear, LinearStrategy)

        random_strat = StrategyFactory.create("random")
        assert isinstance(random_strat, RandomStrategy)

        tournament = StrategyFactory.create("tournament")
        assert isinstance(tournament, TournamentStrategy)

    def test_unknown_strategy(self):
        """Test creating unknown strategy raises error."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            StrategyFactory.create("nonexistent")

    def test_custom_strategy_registration(self):
        """Test registering a custom strategy."""

        class CustomStrategy:
            def initialize(self, config, initial_program):
                pass

            def select_parents(self, database, count=1):
                return []

            def should_accept(self, candidate, database):
                return True

            def update_state(self, new_program, database):
                pass

            def get_strategy_metrics(self):
                return {}

        StrategyFactory.register("custom", CustomStrategy)
        assert "custom" in StrategyFactory.list_strategies()

        custom = StrategyFactory.create("custom")
        assert isinstance(custom, CustomStrategy)


class TestLinearStrategy:
    """Test the linear selection strategy."""

    def test_select_parents(self, sample_database, sample_program):
        """Test selecting most recent parents."""
        strategy = LinearStrategy()
        strategy.initialize({}, sample_program)

        # Should select most recent (highest ID) first
        parents = strategy.select_parents(sample_database, count=2)
        assert len(parents) == 2
        assert parents[0].id == "4"  # Most recent
        assert parents[1].id == "3"  # Second most recent

    def test_select_more_than_available(self, sample_database, sample_program):
        """Test selecting more parents than available."""
        strategy = LinearStrategy()
        strategy.initialize({}, sample_program)

        parents = strategy.select_parents(sample_database, count=10)
        assert len(parents) == 5  # Only 5 programs in database

    def test_empty_database(self, sample_program):
        """Test selecting from empty database."""
        from evolve.database import LinearSamplingStrategy

        empty_db = ProgramDatabase(LinearSamplingStrategy())

        strategy = LinearStrategy()
        strategy.initialize({}, sample_program)

        with pytest.raises(ValueError, match="empty database"):
            strategy.select_parents(empty_db)


class TestRandomStrategy:
    """Test the random selection strategy."""

    def test_select_parents(self, sample_database, sample_program):
        """Test random parent selection."""
        strategy = RandomStrategy()
        strategy.initialize({}, sample_program)

        # Select multiple times to check randomness
        parent_ids = set()
        for _ in range(20):
            parents = strategy.select_parents(sample_database, count=1)
            assert len(parents) == 1
            parent_ids.add(parents[0].id)

        # Should have selected different parents
        assert len(parent_ids) > 1

    def test_select_with_replacement(self, sample_database, sample_program):
        """Test selecting more parents than population size."""
        strategy = RandomStrategy()
        strategy.initialize({}, sample_program)

        parents = strategy.select_parents(sample_database, count=10)
        assert len(parents) == 10  # Can select with replacement


class TestTournamentStrategy:
    """Test tournament selection strategy."""

    def test_tournament_selection(self, sample_database, sample_program):
        """Test tournament-based selection."""
        strategy = TournamentStrategy()
        strategy.initialize({"tournament_size": 3, "selection_pressure": 0.8}, sample_program)

        # With high selection pressure, should favor higher fitness
        selected_fitnesses = []
        for _ in range(20):
            parents = strategy.select_parents(sample_database, count=1)
            assert len(parents) == 1
            selected_fitnesses.append(parents[0].metrics["fitness"])

        # Average fitness should be higher than random (0.2)
        avg_fitness = sum(selected_fitnesses) / len(selected_fitnesses)
        assert avg_fitness > 0.2

    def test_configuration(self, sample_program):
        """Test tournament configuration."""
        strategy = TournamentStrategy()

        # Test default configuration
        strategy.initialize({}, sample_program)
        assert strategy.tournament_size == 3
        assert strategy.selection_pressure == 0.8

        # Test custom configuration
        strategy.initialize({"tournament_size": 5, "selection_pressure": 0.5}, sample_program)
        assert strategy.tournament_size == 5
        assert strategy.selection_pressure == 0.5

    def test_strategy_metrics(self, sample_program):
        """Test getting strategy metrics."""
        strategy = TournamentStrategy()
        strategy.initialize({"tournament_size": 4}, sample_program)

        metrics = strategy.get_strategy_metrics()
        assert metrics["type"] == "TournamentStrategy"
        assert metrics["generation"] == 0
        assert metrics["tournament_size"] == 4
        assert metrics["selection_pressure"] == 0.8


class TestStrategyProtocol:
    """Test the strategy protocol implementation."""

    def test_should_accept_default(self, sample_database, sample_program):
        """Test default acceptance behavior."""
        strategy = LinearStrategy()
        strategy.initialize({}, sample_program)

        # Should accept successful programs
        success_program = Program(program_code="test", evolve_code="test", success=True, metrics={"fitness": 0.5})
        assert strategy.should_accept(success_program, sample_database)

        # Should reject failed programs
        failed_program = Program(program_code="test", evolve_code="test", success=False, metrics={"fitness": 0.5})
        assert not strategy.should_accept(failed_program, sample_database)

    def test_update_state(self, sample_database, sample_program):
        """Test state updates."""
        strategy = LinearStrategy()
        strategy.initialize({}, sample_program)

        assert strategy.generation == 0

        new_program = Program(program_code="new", evolve_code="new", success=True, metrics={"fitness": 0.9})

        strategy.update_state(new_program, sample_database)
        assert strategy.generation == 1
