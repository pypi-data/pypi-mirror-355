"""Tests for island-based evolution strategy."""

import pytest

from evolve.database import Program, ProgramDatabase
from evolve.strategies.base import StrategyFactory
from evolve.strategies.islands import (
    HeterogeneousIslandStrategy,
    Island,
    IslandConfig,
    IslandStrategy,
    MigrationManager,
    MigrationTopology,
)


@pytest.fixture
def sample_program():
    """Create a sample program for testing."""
    return Program(
        program_code="def test(): return 42",
        evolve_code="def test(): return 42",
        success=True,
        metrics={"fitness": 0.8},
    )


@pytest.fixture
def island_config():
    """Create a basic island configuration."""
    return IslandConfig(
        island_id=0,
        size=10,
        mutation_rate=0.7,
        crossover_rate=0.3,
        selection_pressure=0.8,
        elitism_rate=0.1,
    )


class TestIslandConfig:
    """Test IslandConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = IslandConfig(island_id=1)
        assert config.island_id == 1
        assert config.size == 20
        assert config.mutation_rate == 0.7
        assert config.llm_model is None

    def test_custom_values(self):
        """Test custom configuration values."""
        config = IslandConfig(
            island_id=2,
            size=30,
            mutation_rate=0.9,
            llm_model="gpt-4",
            llm_temperature=0.5,
            prompt_style="creative",
        )
        assert config.size == 30
        assert config.mutation_rate == 0.9
        assert config.llm_model == "gpt-4"
        assert config.llm_temperature == 0.5
        assert config.prompt_style == "creative"


class TestIsland:
    """Test Island class."""

    def test_initialization(self, island_config):
        """Test island initialization."""
        island = Island(island_config)
        assert island.config == island_config
        assert len(island.population) == 0
        assert island.best_program is None
        assert island.best_fitness == -float("inf")
        assert island.diversity_score == 1.0

    def test_add_program(self, island_config, sample_program):
        """Test adding programs to island."""
        island = Island(island_config)

        # Add first program
        assert island.add_program(sample_program)
        assert len(island.population) == 1
        assert island.best_program == sample_program
        assert island.best_fitness == 0.8
        assert island.metrics["total_evaluations"] == 1
        assert island.metrics["improvements"] == 1

    def test_population_size_limit(self, island_config):
        """Test that population size is maintained."""
        island = Island(island_config)

        # Add more programs than island size
        for i in range(15):
            program = Program(
                program_code=f"def func{i}(): return {i}",
                evolve_code=f"def func{i}(): return {i}",
                success=True,
                metrics={"fitness": 0.5 + i * 0.01},
            )
            island.add_program(program)

        # Population should be limited to island size
        assert len(island.population) == island.config.size

    def test_elitism(self, island_config):
        """Test that best programs are preserved."""
        island = Island(island_config)

        # Add programs with different fitness
        best_program = None
        for i in range(15):
            program = Program(
                program_code=f"def func{i}(): return {i}",
                evolve_code=f"def func{i}(): return {i}",
                success=True,
                metrics={"fitness": 0.5 + i * 0.05},
            )
            island.add_program(program)
            if i == 14:  # Last program has highest fitness
                best_program = program

        # Best program should still be in population
        assert best_program in island.population
        assert island.best_program == best_program

    def test_diversity_score(self, island_config):
        """Test diversity calculation."""
        island = Island(island_config)

        # Add identical programs (more than island size to trigger selection)
        for _i in range(12):
            program = Program(
                program_code="def same(): return 42",
                evolve_code="def same(): return 42",
                success=True,
                metrics={"fitness": 0.5},
            )
            island.add_program(program)

        # Low diversity
        assert island.diversity_score < 0.3

        # Add diverse programs
        for i in range(10):
            program = Program(
                program_code=f"def different{i}(): return {i * 10}",
                evolve_code=f"def different{i}(): return {i * 10}",
                success=True,
                metrics={"fitness": 0.6},
            )
            island.add_program(program)

        # Higher diversity (should be better than before)
        assert island.diversity_score >= 0.3

    def test_select_parent(self, island_config, sample_program):
        """Test parent selection."""
        island = Island(island_config)

        # Add some programs
        for i in range(5):
            program = Program(
                program_code=f"def func{i}(): return {i}",
                evolve_code=f"def func{i}(): return {i}",
                success=True,
                metrics={"fitness": 0.5 + i * 0.1},
            )
            island.add_program(program)

        # Select parent multiple times
        parents = [island.select_parent() for _ in range(10)]

        # Should get valid programs
        assert all(isinstance(p, Program) for p in parents)
        assert all(p in island.population for p in parents)

    def test_migration_methods(self, island_config):
        """Test emigration and immigration."""
        island = Island(island_config)

        # Add programs
        programs = []
        for i in range(5):
            program = Program(
                program_code=f"def func{i}(): return {i}",
                evolve_code=f"def func{i}(): return {i}",
                success=True,
                metrics={"fitness": 0.5 + i * 0.1},
            )
            programs.append(program)
            island.add_program(program)

        # Select emigrants
        emigrants = island.select_emigrants(2)
        assert len(emigrants) == 2
        assert all(p in programs for p in emigrants)
        assert island.metrics["migrations_sent"] == 2

        # Test immigration
        immigrant = Program(
            program_code="def immigrant(): return 999",
            evolve_code="def immigrant(): return 999",
            success=True,
            metrics={"fitness": 0.9},
        )
        island.receive_immigrants([immigrant])
        assert island.metrics["migrations_received"] == 1

        # Process immigration
        island.process_immigration()
        # Should have new program (but might be removed by selection)
        assert island.metrics["total_evaluations"] == 6

    def test_adaptation(self, island_config):
        """Test parameter adaptation."""
        island = Island(island_config)
        initial_mutation = island.config.mutation_rate

        # Add same program many times to trigger stagnation
        for _i in range(15):
            program = Program(
                program_code="def stagnant(): return 42",
                evolve_code="def stagnant(): return 42",
                success=True,
                metrics={"fitness": 0.5},
            )
            island.add_program(program)

        # Should detect need for adaptation
        assert island.should_adapt()

        # Adapt parameters
        island.adapt_parameters()

        # Mutation rate should increase due to low diversity
        assert island.config.mutation_rate > initial_mutation


class TestMigrationManager:
    """Test MigrationManager class."""

    def test_initialization(self):
        """Test migration manager initialization."""
        manager = MigrationManager(MigrationTopology.RING, migration_rate=0.2, migration_interval=10)
        assert manager.topology == MigrationTopology.RING
        assert manager.migration_rate == 0.2
        assert manager.migration_interval == 10
        assert manager.migration_count == 0

    def test_should_migrate(self):
        """Test migration scheduling."""
        manager = MigrationManager(MigrationTopology.RING, migration_interval=5)

        assert not manager.should_migrate(0)  # Generation 0
        assert not manager.should_migrate(3)
        assert manager.should_migrate(5)
        assert manager.should_migrate(10)
        assert not manager.should_migrate(11)

    def test_ring_topology(self):
        """Test ring topology connections."""
        manager = MigrationManager(MigrationTopology.RING)

        # 5 islands in a ring
        assert manager.get_migration_targets(0, 5) == [1]
        assert manager.get_migration_targets(1, 5) == [2]
        assert manager.get_migration_targets(4, 5) == [0]  # Wraps around

    def test_fully_connected_topology(self):
        """Test fully connected topology."""
        manager = MigrationManager(MigrationTopology.FULLY_CONNECTED)

        # Island 0 connects to all others
        targets = manager.get_migration_targets(0, 4)
        assert set(targets) == {1, 2, 3}
        assert 0 not in targets

    def test_star_topology(self):
        """Test star topology with central hub."""
        manager = MigrationManager(MigrationTopology.STAR)

        # Island 0 is hub
        assert set(manager.get_migration_targets(0, 5)) == {1, 2, 3, 4}

        # Other islands connect only to hub
        assert manager.get_migration_targets(1, 5) == [0]
        assert manager.get_migration_targets(3, 5) == [0]

    def test_grid_topology(self):
        """Test 2D grid topology."""
        manager = MigrationManager(MigrationTopology.GRID)

        # 9 islands in 3x3 grid
        # 0 1 2
        # 3 4 5
        # 6 7 8

        # Corner island
        assert set(manager.get_migration_targets(0, 9)) == {1, 3}

        # Center island
        assert set(manager.get_migration_targets(4, 9)) == {1, 3, 5, 7}

        # Edge island
        assert set(manager.get_migration_targets(1, 9)) == {0, 2, 4}

    def test_random_topology(self):
        """Test random topology connections."""
        manager = MigrationManager(MigrationTopology.RANDOM)

        # Should get random connections
        targets = manager.get_migration_targets(0, 10)
        assert len(targets) <= 3  # Max 3 connections
        assert 0 not in targets

        # Different calls might give different results
        targets2 = manager.get_migration_targets(0, 10)
        # Can't guarantee they're different due to randomness

    def test_perform_migration(self, island_config):
        """Test migration execution."""
        manager = MigrationManager(MigrationTopology.RING, migration_rate=0.2)

        # Create islands
        islands = []
        for i in range(3):
            config = IslandConfig(island_id=i, size=5)
            island = Island(config)
            # Add some programs
            for j in range(3):
                program = Program(
                    program_code=f"def f{i}_{j}(): pass",
                    evolve_code=f"def f{i}_{j}(): pass",
                    success=True,
                    metrics={"fitness": 0.5},
                )
                island.add_program(program)
            islands.append(island)

        # Perform migration
        manager.perform_migration(islands)

        # Check migration occurred
        assert manager.migration_count == 1
        total_sent = sum(i.metrics["migrations_sent"] for i in islands)
        assert total_sent > 0


class TestIslandStrategy:
    """Test IslandStrategy class."""

    def test_initialization(self, sample_program):
        """Test strategy initialization."""
        strategy = IslandStrategy()
        config = {
            "num_islands": 3,
            "island_size": 10,
            "topology": "ring",
            "migration_rate": 0.1,
            "migration_interval": 5,
        }

        strategy.initialize(config, sample_program)

        assert len(strategy.islands) == 3
        assert strategy.migration_manager is not None
        assert strategy.migration_manager.topology == MigrationTopology.RING
        assert strategy.global_best == sample_program

    def test_gradient_island_configs(self, sample_program):
        """Test that islands get gradient configurations."""
        strategy = IslandStrategy()
        config = {"num_islands": 5}

        strategy.initialize(config, sample_program)

        # Check mutation rates form a gradient
        mutation_rates = [island.config.mutation_rate for island in strategy.islands]
        assert mutation_rates[0] < mutation_rates[-1]
        assert all(0.5 <= rate <= 0.9 for rate in mutation_rates)

    def test_select_parents(self, sample_program):
        """Test parent selection across islands."""
        strategy = IslandStrategy()
        config = {"num_islands": 3, "island_size": 5}
        strategy.initialize(config, sample_program)

        # Add some programs to islands
        for i, island in enumerate(strategy.islands):
            for j in range(3):
                program = Program(
                    program_code=f"def f{i}_{j}(): pass",
                    evolve_code=f"def f{i}_{j}(): pass",
                    success=True,
                    metrics={"fitness": 0.5 + i * 0.1 + j * 0.01},
                )
                island.add_program(program)

        from evolve.database import LinearSamplingStrategy

        db = ProgramDatabase(LinearSamplingStrategy())

        # Select parents
        parents = strategy.select_parents(db, count=5)

        assert len(parents) == 5
        assert all(isinstance(p, Program) for p in parents)

    def test_update_state_and_migration(self, sample_program):
        """Test state updates and migration triggering."""
        strategy = IslandStrategy()
        config = {"num_islands": 3, "topology": "ring", "migration_interval": 3}
        strategy.initialize(config, sample_program)

        from evolve.database import LinearSamplingStrategy

        db = ProgramDatabase(LinearSamplingStrategy())

        # Add programs over multiple generations
        for gen in range(5):
            program = Program(
                program_code=f"def gen{gen}(): return {gen}",
                evolve_code=f"def gen{gen}(): return {gen}",
                success=True,
                metrics={"fitness": 0.5 + gen * 0.1},
            )
            strategy.update_state(program, db)

        # Check migration occurred
        assert strategy.migration_manager.migration_count > 0

        # Check global best updated
        assert strategy.global_best.score >= 0.9

    def test_convergence_detection(self, sample_program):
        """Test convergence detection and diversity injection."""
        strategy = IslandStrategy()
        config = {"num_islands": 3}
        strategy.initialize(config, sample_program)

        # Make all islands converge to same fitness
        for island in strategy.islands:
            for _i in range(5):
                program = Program(
                    program_code="def same(): return 42",
                    evolve_code="def same(): return 42",
                    success=True,
                    metrics={"fitness": 0.8},  # Same fitness
                )
                island.add_program(program)

        # Should detect convergence
        assert strategy._check_convergence()

        # Inject diversity
        initial_mutations = [i.config.mutation_rate for i in strategy.islands]
        strategy._inject_diversity()
        new_mutations = [i.config.mutation_rate for i in strategy.islands]

        # Mutation rates should increase
        assert all(new > old for new, old in zip(new_mutations, initial_mutations))

    def test_assign_to_island(self):
        """Test program assignment to islands."""
        strategy = IslandStrategy()
        strategy.islands = [Island(IslandConfig(i)) for i in range(5)]

        # Test code length based assignment
        short_program = Program(
            program_code="x=1",
            evolve_code="x=1",
            success=True,
            metrics={"fitness": 0.5},
        )

        long_program = Program(
            program_code="x" * 1500,
            evolve_code="x" * 1500,
            success=True,
            metrics={"fitness": 0.5},
        )

        short_idx = strategy._assign_to_island(short_program)
        long_idx = strategy._assign_to_island(long_program)

        assert 0 <= short_idx < 5
        assert 0 <= long_idx < 5
        assert short_idx < long_idx  # Short code goes to lower index

    def test_strategy_metrics(self, sample_program):
        """Test strategy metrics reporting."""
        strategy = IslandStrategy()
        config = {"num_islands": 2}
        strategy.initialize(config, sample_program)

        # Add some activity
        for i in range(3):
            program = Program(
                program_code=f"def f{i}(): pass",
                evolve_code=f"def f{i}(): pass",
                success=True,
                metrics={"fitness": 0.5 + i * 0.1},
            )
            strategy.islands[i % 2].add_program(program)

        metrics = strategy.get_strategy_metrics()

        assert metrics["type"] == "Island"
        assert metrics["num_islands"] == 2
        assert metrics["topology"] == "ring"
        assert metrics["total_evaluations"] > 0
        assert "islands" in metrics
        assert len(metrics["islands"]) == 2


class TestHeterogeneousIslandStrategy:
    """Test HeterogeneousIslandStrategy class."""

    def test_default_heterogeneous_configs(self, sample_program):
        """Test default heterogeneous island configurations."""
        strategy = HeterogeneousIslandStrategy()
        config = {"num_islands": 5}

        strategy.initialize(config, sample_program)

        # Check each island has different configuration
        configs = [island.config for island in strategy.islands]

        # Different mutation rates
        mutation_rates = [c.mutation_rate for c in configs]
        assert len(set(mutation_rates)) == 5

        # Different LLM models
        llm_models = [c.llm_model for c in configs]
        assert all(model is not None for model in llm_models)
        assert "gpt-4o-mini" in llm_models[0]
        assert "claude" in llm_models[2]

        # Different prompt styles
        prompt_styles = [c.prompt_style for c in configs]
        assert "conservative" in prompt_styles
        assert "creative" in prompt_styles

    def test_custom_island_configs(self, sample_program):
        """Test custom island configurations override defaults."""
        strategy = HeterogeneousIslandStrategy()
        config = {
            "num_islands": 3,
            "island_configs": [
                {"mutation_rate": 0.1, "llm_model": "custom-model-1"},
                {"mutation_rate": 0.2, "llm_model": "custom-model-2"},
            ],
        }

        strategy.initialize(config, sample_program)

        # First two islands should use custom configs
        assert strategy.islands[0].config.mutation_rate == 0.1
        assert strategy.islands[0].config.llm_model == "custom-model-1"
        assert strategy.islands[1].config.mutation_rate == 0.2
        assert strategy.islands[1].config.llm_model == "custom-model-2"

        # Third island uses default
        assert strategy.islands[2].config.mutation_rate == 0.9


class TestStrategyRegistration:
    """Test that island strategies are properly registered."""

    def test_island_strategy_registered(self):
        """Test IslandStrategy is in factory."""
        assert "islands" in StrategyFactory.list_strategies()

    def test_heterogeneous_strategy_registered(self):
        """Test HeterogeneousIslandStrategy is in factory."""
        assert "heterogeneous_islands" in StrategyFactory.list_strategies()

    def test_create_island_strategy(self):
        """Test creating island strategy via factory."""
        strategy = StrategyFactory.create("islands")
        assert isinstance(strategy, IslandStrategy)

    def test_create_heterogeneous_strategy(self):
        """Test creating heterogeneous strategy via factory."""
        strategy = StrategyFactory.create("heterogeneous_islands")
        assert isinstance(strategy, HeterogeneousIslandStrategy)
