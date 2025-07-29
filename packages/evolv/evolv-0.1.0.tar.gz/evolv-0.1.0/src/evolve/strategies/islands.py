"""Island-based parallel evolution strategy.

Implements the island-based evolution strategy as described in Issue #19.
This strategy maintains multiple isolated populations that evolve independently
with periodic migration between islands to maintain diversity.
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

from ..database import Program, ProgramDatabase
from .base import BaseEvolutionStrategy, StrategyFactory

logger = logging.getLogger(__name__)


class MigrationTopology(Enum):
    """Defines how islands are connected for migration."""

    RING = "ring"  # Each island connects to neighbors in a ring
    FULLY_CONNECTED = "fully_connected"  # All islands connected
    RANDOM = "random"  # Random connections each migration
    STAR = "star"  # Central hub island
    GRID = "grid"  # 2D grid topology


@dataclass
class IslandConfig:
    """Configuration for a single island."""

    island_id: int
    size: int = 20
    mutation_rate: float = 0.7
    crossover_rate: float = 0.3
    selection_pressure: float = 0.8
    elitism_rate: float = 0.1

    # Optional: Different LLM per island
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    prompt_style: Optional[str] = None  # "conservative", "creative", "analytical"


class Island:
    """Represents a single evolutionary island."""

    def __init__(self, config: IslandConfig):
        self.config = config
        self.population: List[Program] = []
        self.best_program: Optional[Program] = None
        self.best_fitness: float = -float("inf")
        self.generations: int = 0
        self.stagnation_counter: int = 0
        self.diversity_score: float = 1.0

        # Migration queues
        self.immigration_queue: List[Program] = []
        self.emigration_history: List[str] = []  # Track sent program IDs

        # Island-specific metrics
        self.metrics = {
            "total_evaluations": 0,
            "improvements": 0,
            "migrations_sent": 0,
            "migrations_received": 0,
            "unique_solutions": set(),
        }

    def add_program(self, program: Program, force: bool = False) -> bool:
        """Add a program to the island population."""
        # Update metrics
        self.metrics["total_evaluations"] += 1

        # Check for improvement
        if program.score > self.best_fitness:
            self.best_fitness = program.score
            self.best_program = program
            self.stagnation_counter = 0
            self.metrics["improvements"] += 1
        else:
            self.stagnation_counter += 1

        # Add to population
        self.population.append(program)

        # Maintain population size with selection
        if len(self.population) > self.config.size:
            self._apply_selection()

        # Track unique solutions (by code hash)
        code_hash = hash(program.evolve_code)
        self.metrics["unique_solutions"].add(code_hash)

        return True

    def _apply_selection(self):
        """Apply selection to maintain population size."""
        # Sort by fitness
        self.population.sort(key=lambda p: p.score, reverse=True)

        # Elitism: Keep top performers
        elite_count = max(1, int(self.config.size * self.config.elitism_rate))
        elites = self.population[:elite_count]

        # Tournament selection for the rest
        remaining_slots = self.config.size - elite_count
        selected = []

        for _ in range(remaining_slots):
            tournament_size = max(2, int(len(self.population) * 0.1))
            tournament = random.sample(self.population[elite_count:], tournament_size)
            winner = max(tournament, key=lambda p: p.score)
            selected.append(winner)

        # Update population
        self.population = elites + selected

        # Update diversity
        self._update_diversity_score()

    def _update_diversity_score(self):
        """Calculate population diversity."""
        if len(self.population) < 2:
            self.diversity_score = 1.0
            return

        # Simple diversity: unique code patterns
        unique_codes = len({hash(p.evolve_code) for p in self.population})
        self.diversity_score = unique_codes / len(self.population)

    def select_parent(self) -> Program:
        """Select a parent using tournament selection."""
        if not self.population:
            raise ValueError("Empty population")

        # Adaptive tournament size based on selection pressure
        base_size = 3
        tournament_size = max(2, int(base_size * self.config.selection_pressure))
        tournament_size = min(tournament_size, len(self.population))

        tournament = random.sample(self.population, tournament_size)

        # Fitness-proportionate selection within tournament
        if random.random() < 0.8:  # 80% fitness-based
            return max(tournament, key=lambda p: p.score)
        else:  # 20% random for diversity
            return random.choice(tournament)

    def select_emigrants(self, count: int) -> List[Program]:
        """Select programs to migrate to other islands."""
        if not self.population:
            return []

        # Prioritize diverse, high-quality individuals
        candidates = sorted(self.population, key=lambda p: p.score, reverse=True)

        # Don't send the same program multiple times
        eligible = [p for p in candidates if p.id not in self.emigration_history[-50:]]  # Last 50

        emigrants = eligible[:count]

        # Track what we sent
        for program in emigrants:
            self.emigration_history.append(program.id)
            self.metrics["migrations_sent"] += 1

        return emigrants

    def receive_immigrants(self, immigrants: List[Program]):
        """Add immigrants to the immigration queue."""
        self.immigration_queue.extend(immigrants)
        self.metrics["migrations_received"] += len(immigrants)

    def process_immigration(self):
        """Integrate immigrants into the population."""
        if not self.immigration_queue:
            return

        # Add immigrants, let selection handle population size
        for immigrant in self.immigration_queue:
            # Create a copy to avoid shared references
            immigrant_copy = Program(
                program_code=immigrant.program_code,
                evolve_code=immigrant.evolve_code,
                metrics=immigrant.metrics.copy(),
                success=immigrant.success,
                parent_id=immigrant.id,  # Track origin
            )
            self.add_program(immigrant_copy)

        self.immigration_queue.clear()

    def should_adapt(self) -> bool:
        """Check if island parameters should be adapted."""
        # Adapt if stagnating
        return self.stagnation_counter > 10

    def adapt_parameters(self):
        """Adapt island parameters based on performance."""
        if self.diversity_score < 0.3:
            # Low diversity: increase mutation
            self.config.mutation_rate = min(0.95, self.config.mutation_rate * 1.1)
            self.config.selection_pressure = max(0.5, self.config.selection_pressure * 0.9)

        if self.stagnation_counter > 20:
            # High stagnation: shake things up
            self.config.mutation_rate = 0.9
            self.config.crossover_rate = 0.1
            # Reset stagnation counter
            self.stagnation_counter = 10


class MigrationManager:
    """Manages migration between islands."""

    def __init__(self, topology: MigrationTopology, migration_rate: float = 0.1, migration_interval: int = 5):
        self.topology = topology
        self.migration_rate = migration_rate
        self.migration_interval = migration_interval
        self.migration_count = 0
        self.topology_cache: Optional[Dict[int, List[int]]] = None

    def should_migrate(self, generation: int) -> bool:
        """Check if migration should occur."""
        return generation > 0 and generation % self.migration_interval == 0

    def get_migration_targets(self, island_id: int, num_islands: int) -> List[int]:
        """Get target islands for migration based on topology."""
        if self.topology == MigrationTopology.RING:
            # Each island sends to next in ring
            return [(island_id + 1) % num_islands]

        elif self.topology == MigrationTopology.FULLY_CONNECTED:
            # Can send to any other island
            return [i for i in range(num_islands) if i != island_id]

        elif self.topology == MigrationTopology.RANDOM:
            # Random connections each time
            others = [i for i in range(num_islands) if i != island_id]
            k = min(3, len(others))  # Connect to up to 3 random islands
            return random.sample(others, k)

        elif self.topology == MigrationTopology.STAR:
            # Central hub (island 0) connects to all
            if island_id == 0:
                return list(range(1, num_islands))
            else:
                return [0]

        elif self.topology == MigrationTopology.GRID:
            # 2D grid topology
            return self._get_grid_neighbors(island_id, num_islands)

        return []

    def _get_grid_neighbors(self, island_id: int, num_islands: int) -> List[int]:
        """Get neighbors in 2D grid topology."""
        # Arrange islands in square grid
        grid_size = int(np.sqrt(num_islands))
        row = island_id // grid_size
        col = island_id % grid_size

        neighbors = []
        # Check 4-connected neighbors
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < grid_size and 0 <= new_col < grid_size:
                neighbor_id = new_row * grid_size + new_col
                if neighbor_id < num_islands:
                    neighbors.append(neighbor_id)

        return neighbors

    def perform_migration(self, islands: List[Island]):
        """Execute migration between islands."""
        self.migration_count += 1
        migration_size = max(1, int(islands[0].config.size * self.migration_rate))

        # Collect emigrants from each island
        all_migrations = []
        for i, island in enumerate(islands):
            emigrants = island.select_emigrants(migration_size)
            targets = self.get_migration_targets(i, len(islands))

            for emigrant in emigrants:
                # Distribute to target islands
                if self.topology == MigrationTopology.FULLY_CONNECTED:
                    # Send to one random target
                    target = random.choice(targets)
                    all_migrations.append((emigrant, target))
                else:
                    # Send to all targets
                    for target in targets:
                        all_migrations.append((emigrant, target))

        # Deliver immigrants
        for emigrant, target_id in all_migrations:
            islands[target_id].receive_immigrants([emigrant])

        # Process immigration queues
        for island in islands:
            island.process_immigration()


class IslandStrategy(BaseEvolutionStrategy):
    """Island-based parallel evolution strategy."""

    def __init__(self):
        super().__init__()
        self.islands: List[Island] = []
        self.migration_manager: Optional[MigrationManager] = None
        self.global_best: Optional[Program] = None
        self.convergence_threshold: float = 0.95

    def initialize(self, config: Dict[str, Any], initial_program: Program):
        """Initialize islands with configuration."""
        super().initialize(config, initial_program)

        # Parse configuration
        num_islands = config.get("num_islands", 5)
        island_size = config.get("island_size", 20)
        topology = MigrationTopology(config.get("topology", "ring"))
        migration_rate = config.get("migration_rate", 0.1)
        migration_interval = config.get("migration_interval", 5)

        # Heterogeneous island configurations
        island_configs = config.get("island_configs", [])

        # Create islands with varying characteristics
        self.islands = []
        for i in range(num_islands):
            if i < len(island_configs):
                # Use provided config
                island_config = IslandConfig(island_id=i, size=island_size, **island_configs[i])
            else:
                # Generate config with gradient
                mutation_rate = 0.5 + (0.4 * i / (num_islands - 1)) if num_islands > 1 else 0.7
                island_config = IslandConfig(
                    island_id=i,
                    size=island_size,
                    mutation_rate=mutation_rate,
                    crossover_rate=1.0 - mutation_rate,
                    selection_pressure=0.6 + (0.3 * i / (num_islands - 1)) if num_islands > 1 else 0.8,
                )

            island = Island(island_config)
            # Seed with initial program
            island.add_program(initial_program)
            self.islands.append(island)

        # Setup migration
        self.migration_manager = MigrationManager(
            topology=topology, migration_rate=migration_rate, migration_interval=migration_interval
        )

        # Initialize global best
        self.global_best = initial_program

        logger.info(f"Initialized {num_islands} islands with {topology.value} topology")

    def select_parents(self, database: ProgramDatabase, count: int = 1) -> List[Program]:
        """Select parents from across all islands."""
        parents = []

        # Weighted selection based on island performance
        island_weights = []
        for island in self.islands:
            # Weight by best fitness and diversity
            weight = island.best_fitness * island.diversity_score
            island_weights.append(max(0.1, weight))  # Minimum weight

        # Normalize weights
        total_weight = sum(island_weights)
        island_weights = [w / total_weight for w in island_weights]

        # Select parents
        for _ in range(count):
            # Choose island
            island_idx = np.random.choice(len(self.islands), p=island_weights)
            island = self.islands[island_idx]

            if island.population:
                parent = island.select_parent()
                parents.append(parent)
            else:
                # Fallback to global best
                if self.global_best:
                    parents.append(self.global_best)

        return parents

    def should_accept(self, candidate: Program, database: ProgramDatabase) -> bool:
        """Always accept successful programs."""
        return candidate.success

    def update_state(self, new_program: Program, database: ProgramDatabase):
        """Add program to appropriate island and manage migration."""
        super().update_state(new_program, database)

        # Assign to island based on program characteristics
        island_idx = self._assign_to_island(new_program)
        self.islands[island_idx].add_program(new_program)

        # Update global best
        if new_program.score > (self.global_best.score if self.global_best else -float("inf")):
            self.global_best = new_program
            logger.info(f"New global best: {new_program.score:.4f}")

        # Perform migration if scheduled
        if self.migration_manager.should_migrate(self.generation):
            self._perform_migration()

        # Adaptive island parameters
        if self.generation % 10 == 0:
            self._adapt_islands()

        # Check for convergence
        if self._check_convergence():
            logger.warning("Islands converging - increasing diversity")
            self._inject_diversity()

    def _assign_to_island(self, program: Program) -> int:
        """Assign program to island based on characteristics."""
        # Simple assignment: rotate or based on code characteristics

        # Option 1: Round-robin
        # return self.generation % len(self.islands)

        # Option 2: Based on code length (spatial distribution)
        code_length = len(program.evolve_code)
        normalized_length = min(1.0, code_length / 2000)
        island_idx = int(normalized_length * (len(self.islands) - 1))
        return island_idx

        # Option 3: Random for maximum diversity
        # return random.randint(0, len(self.islands) - 1)

    def _perform_migration(self):
        """Execute migration between islands."""
        logger.info(f"Performing migration at generation {self.generation}")
        self.migration_manager.perform_migration(self.islands)

        # Log migration summary
        total_sent = sum(i.metrics["migrations_sent"] for i in self.islands)
        logger.info(f"Migration complete: {total_sent} programs migrated")

    def _adapt_islands(self):
        """Adapt island parameters based on performance."""
        for island in self.islands:
            if island.should_adapt():
                island.adapt_parameters()
                logger.debug(f"Island {island.config.island_id} adapted: mutation={island.config.mutation_rate:.2f}")

    def _check_convergence(self) -> bool:
        """Check if islands are converging."""
        if len(self.islands) < 2:
            return False

        # Check if all islands have similar best fitness
        best_fitnesses = [i.best_fitness for i in self.islands]
        mean_fitness = np.mean(best_fitnesses)
        std_fitness = np.std(best_fitnesses)

        # Low variance indicates convergence
        return std_fitness / (mean_fitness + 1e-6) < 0.05

    def _inject_diversity(self):
        """Inject diversity when islands converge."""
        # Increase mutation rates temporarily
        for island in self.islands:
            island.config.mutation_rate = min(0.95, island.config.mutation_rate * 1.5)
            island.stagnation_counter = 0

    def get_strategy_metrics(self) -> Dict[str, Any]:
        """Return comprehensive island metrics."""
        metrics = super().get_strategy_metrics()

        # Aggregate island metrics
        total_evaluations = sum(i.metrics["total_evaluations"] for i in self.islands)
        total_improvements = sum(i.metrics["improvements"] for i in self.islands)
        total_unique = sum(len(i.metrics["unique_solutions"]) for i in self.islands)

        # Per-island summary
        island_summary = []
        for island in self.islands:
            island_summary.append(
                {
                    "id": island.config.island_id,
                    "best_fitness": island.best_fitness,
                    "population_size": len(island.population),
                    "diversity": island.diversity_score,
                    "stagnation": island.stagnation_counter,
                    "mutation_rate": island.config.mutation_rate,
                }
            )

        metrics.update(
            {
                "type": "Island",
                "num_islands": len(self.islands),
                "topology": self.migration_manager.topology.value if self.migration_manager else "none",
                "global_best_fitness": self.global_best.score if self.global_best else 0,
                "total_evaluations": total_evaluations,
                "total_improvements": total_improvements,
                "total_unique_solutions": total_unique,
                "migrations_performed": self.migration_manager.migration_count if self.migration_manager else 0,
                "islands": island_summary,
            }
        )

        return metrics


class HeterogeneousIslandStrategy(IslandStrategy):
    """Islands with different LLMs and evolution approaches."""

    def initialize(self, config: Dict[str, Any], initial_program: Program):
        """Initialize with heterogeneous configurations."""
        # Define different island personalities
        default_configs = [
            {
                "mutation_rate": 0.3,
                "prompt_style": "conservative",
                "llm_temperature": 0.3,
                "llm_model": "openrouter/openai/gpt-4o-mini",
            },
            {
                "mutation_rate": 0.7,
                "prompt_style": "balanced",
                "llm_temperature": 0.7,
                "llm_model": "openrouter/openai/gpt-4o",
            },
            {
                "mutation_rate": 0.9,
                "prompt_style": "creative",
                "llm_temperature": 0.9,
                "llm_model": "openrouter/anthropic/claude-3-opus",
            },
            {
                "mutation_rate": 0.5,
                "prompt_style": "analytical",
                "llm_temperature": 0.5,
                "llm_model": "openrouter/google/gemini-pro-1.5",
            },
            {
                "mutation_rate": 0.6,
                "prompt_style": "explorative",
                "llm_temperature": 0.8,
                "llm_model": "openrouter/mistralai/mistral-large",
            },
        ]

        # Merge with user configs
        island_configs = config.get("island_configs", [])
        for i in range(len(default_configs)):
            if i < len(island_configs):
                default_configs[i].update(island_configs[i])

        config["island_configs"] = default_configs[: config.get("num_islands", 5)]

        # Initialize parent class
        super().initialize(config, initial_program)


# Register the strategies
StrategyFactory.register("islands", IslandStrategy)
StrategyFactory.register("heterogeneous_islands", HeterogeneousIslandStrategy)
