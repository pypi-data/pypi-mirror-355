"""MAP-Elites (Multidimensional Archive of Phenotypic Elites) evolution strategy."""

import ast
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from ..database import Program, ProgramDatabase
from .base import BaseEvolutionStrategy, StrategyFactory

logger = logging.getLogger(__name__)


@dataclass
class BehaviorDescriptor:
    """Describes a program's behavioral characteristics."""

    features: Dict[str, float]

    def to_grid_coords(self, grid_spec: "GridSpecification") -> Tuple[int, ...]:
        """Convert continuous features to discrete grid coordinates."""
        coords = []
        for feature_name, bounds, bins in grid_spec.dimensions:
            value = self.features.get(feature_name, 0.0)
            # Normalize to [0, 1]
            normalized = np.clip((value - bounds[0]) / (bounds[1] - bounds[0]), 0, 1)
            # Discretize
            bin_idx = int(normalized * (bins - 1))
            coords.append(bin_idx)
        return tuple(coords)


@dataclass
class GridSpecification:
    """Defines the discretization of the behavior space."""

    dimensions: List[Tuple[str, Tuple[float, float], int]]
    # Each dimension: (feature_name, (min, max), num_bins)

    def get_total_cells(self) -> int:
        """Calculate total number of cells in the grid."""
        return int(np.prod([bins for _, _, bins in self.dimensions]))

    def get_shape(self) -> Tuple[int, ...]:
        """Get the shape of the grid."""
        return tuple(bins for _, _, bins in self.dimensions)


class MAPElitesArchive:
    """The core MAP-Elites archive data structure."""

    def __init__(self, grid_spec: GridSpecification):
        self.grid_spec = grid_spec
        self.grid_shape = grid_spec.get_shape()
        self.archive: Dict[Tuple[int, ...], Program] = {}
        self.history: List[Dict[str, Any]] = []
        self.coverage_history: List[float] = []

    def add(self, program: Program, descriptor: BehaviorDescriptor) -> bool:
        """Add a program to the archive if it improves its cell."""
        coords = descriptor.to_grid_coords(self.grid_spec)

        # Check if cell is empty or new program is better
        improved = False
        event_type = None

        if coords not in self.archive:
            self.archive[coords] = program
            improved = True
            event_type = "new_cell"
        elif program.score > self.archive[coords].score:
            self.archive[coords] = program
            improved = True
            event_type = "improvement"

        # Log event
        if improved:
            self.history.append(
                {
                    "event": event_type,
                    "coords": coords,
                    "fitness": program.score,
                    "features": descriptor.features,
                    "iteration": len(self.history),
                }
            )
            self.coverage_history.append(self.get_coverage())

        return improved

    def sample_uniform(self, count: int = 1) -> List[Program]:
        """Sample uniformly from occupied cells."""
        if not self.archive:
            return []

        cells = list(self.archive.values())
        # If we need more samples than available, use replacement
        replace = count > len(cells)
        actual_count = count if replace else min(count, len(cells))
        selected_indices = np.random.choice(len(cells), size=actual_count, replace=replace)
        return [cells[i] for i in selected_indices]

    def sample_curiosity(self, count: int = 1) -> List[Program]:
        """Sample with bias toward less-explored regions."""
        if not self.archive:
            return []

        # Calculate density around each cell
        densities = {}
        for coords in self.archive:
            # Count neighbors within distance 1
            neighbors = 0
            for other_coords in self.archive:
                if coords != other_coords:
                    distance = sum(abs(a - b) for a, b in zip(coords, other_coords))
                    if distance <= 1:
                        neighbors += 1
            densities[coords] = neighbors

        # Weight by inverse density (less explored = higher weight)
        weights = [1.0 / (1 + densities[coords]) for coords in self.archive]

        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        # Sample based on weights
        cells = list(self.archive.values())
        # If we need more samples than available, use replacement
        replace = count > len(cells)
        actual_count = count if replace else min(count, len(cells))
        selected_indices = np.random.choice(len(cells), size=actual_count, replace=replace, p=weights)
        return [cells[i] for i in selected_indices]

    def get_coverage(self) -> float:
        """Return the fraction of cells that are occupied."""
        total_cells = self.grid_spec.get_total_cells()
        return len(self.archive) / total_cells if total_cells > 0 else 0

    def get_elite_grid(self) -> np.ndarray:
        """Return grid with fitness values (for visualization)."""
        grid = np.full(self.grid_shape, np.nan)
        for coords, program in self.archive.items():
            grid[coords] = program.score
        return grid


class FeatureExtractor:
    """Extracts behavioral features from programs."""

    def __init__(self):
        self.extractors: Dict[str, Callable[[Program], float]] = {}
        self._register_default_extractors()

    def _register_default_extractors(self):
        """Register default feature extractors."""
        # Code metrics
        self.extractors["code_length"] = lambda p: len(p.evolve_code)
        self.extractors["num_lines"] = lambda p: p.evolve_code.count("\n") + 1
        self.extractors["complexity"] = self._calculate_complexity

        # Performance metrics (from execution)
        self.extractors["execution_time"] = lambda p: p.metrics.get("execution_time", 0.0)
        self.extractors["memory_usage"] = lambda p: p.metrics.get("memory_bytes", 0) / 1024 / 1024  # MB
        self.extractors["accuracy"] = lambda p: p.metrics.get("accuracy", 0.0)
        self.extractors["fitness"] = lambda p: p.metrics.get("fitness", 0.0)

        # Code style metrics
        self.extractors["num_functions"] = self._count_functions
        self.extractors["max_nesting"] = self._calculate_max_nesting
        self.extractors["num_loops"] = self._count_loops

    def _calculate_complexity(self, program: Program) -> float:
        """Calculate cyclomatic complexity."""
        try:
            tree = ast.parse(program.evolve_code)
            complexity = 1  # Base complexity

            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, (ast.And, ast.Or)):
                    complexity += 1

            return float(complexity)
        except Exception:
            return 1.0

    def _count_functions(self, program: Program) -> float:
        """Count number of function definitions."""
        try:
            tree = ast.parse(program.evolve_code)
            return float(sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)))
        except Exception:
            return 0.0

    def _calculate_max_nesting(self, program: Program) -> float:
        """Calculate maximum nesting depth."""
        try:
            tree = ast.parse(program.evolve_code)

            def get_depth(node, current_depth=0):
                max_depth = current_depth
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                        child_depth = get_depth(child, current_depth + 1)
                        max_depth = max(max_depth, child_depth)
                    else:
                        child_depth = get_depth(child, current_depth)
                        max_depth = max(max_depth, child_depth)
                return max_depth

            return float(get_depth(tree))
        except Exception:
            return 0.0

    def _count_loops(self, program: Program) -> float:
        """Count number of loops."""
        try:
            tree = ast.parse(program.evolve_code)
            return float(sum(1 for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While))))
        except Exception:
            return 0.0

    def extract(self, program: Program, features: List[str]) -> BehaviorDescriptor:
        """Extract specified features from a program."""
        feature_values = {}

        for feature_name in features:
            if feature_name in self.extractors:
                try:
                    value = self.extractors[feature_name](program)
                    feature_values[feature_name] = value
                except Exception as e:
                    logger.warning(f"Failed to extract {feature_name}: {e}")
                    feature_values[feature_name] = 0.0
            else:
                logger.warning(f"Unknown feature: {feature_name}")
                feature_values[feature_name] = 0.0

        return BehaviorDescriptor(feature_values)

    def register_custom_extractor(self, name: str, extractor: Callable[[Program], float]):
        """Register a custom feature extractor."""
        self.extractors[name] = extractor


class MAPElitesStrategy(BaseEvolutionStrategy):
    """MAP-Elites evolution strategy for quality-diversity optimization."""

    def __init__(self):
        super().__init__()
        self.archive: Optional[MAPElitesArchive] = None
        self.feature_extractor = FeatureExtractor()
        self.selection_method = "uniform"
        self.feature_names: List[str] = []
        self.total_evaluations = 0
        self.improvements = 0

    def initialize(self, config: Dict[str, Any], initial_program: Program):
        """Initialize MAP-Elites with grid specification."""
        super().initialize(config, initial_program)

        # Parse configuration
        features_config = config.get(
            "features", [("code_length", (10, 1000), 10), ("execution_time", (0.001, 10.0), 10)]
        )

        # Create grid specification
        grid_spec = GridSpecification(dimensions=features_config)
        self.archive = MAPElitesArchive(grid_spec)

        # Set feature names for extraction
        self.feature_names = [name for name, _, _ in features_config]

        # Selection method
        self.selection_method = config.get("selection", "uniform")

        # Register custom extractors if provided
        custom_extractors = config.get("custom_extractors", {})
        for name, extractor in custom_extractors.items():
            self.feature_extractor.register_custom_extractor(name, extractor)

        # Add initial program to archive
        descriptor = self.feature_extractor.extract(initial_program, self.feature_names)
        self.archive.add(initial_program, descriptor)
        self.total_evaluations = 1

    def select_parents(self, database: ProgramDatabase, count: int = 1) -> List[Program]:
        """Select parents from the MAP-Elites archive."""
        if not self.archive or not self.archive.archive:
            # Fallback to database if archive is empty
            return [database.sample() for _ in range(count)]

        if self.selection_method == "uniform":
            return self.archive.sample_uniform(count)
        elif self.selection_method == "curiosity":
            return self.archive.sample_curiosity(count)
        else:
            # Default to uniform
            return self.archive.sample_uniform(count)

    def should_accept(self, candidate: Program, database: ProgramDatabase) -> bool:
        """MAP-Elites accepts all successful programs."""
        return candidate.success

    def update_state(self, new_program: Program, database: ProgramDatabase):
        """Add program to MAP-Elites archive."""
        super().update_state(new_program, database)

        if new_program.success:
            # Extract features
            descriptor = self.feature_extractor.extract(new_program, self.feature_names)

            # Add to archive
            improved = self.archive.add(new_program, descriptor)

            self.total_evaluations += 1
            if improved:
                self.improvements += 1

            # Log progress
            if self.total_evaluations % 10 == 0:
                coverage = self.archive.get_coverage()
                logger.info(f"MAP-Elites coverage: {coverage:.2%} ({len(self.archive.archive)} cells occupied)")

    def get_strategy_metrics(self) -> Dict[str, Any]:
        """Return MAP-Elites specific metrics."""
        metrics = super().get_strategy_metrics()

        if not self.archive:
            return metrics

        coverage = self.archive.get_coverage()
        occupied_cells = len(self.archive.archive)
        total_cells = self.archive.grid_spec.get_total_cells()

        # Get best fitness per feature dimension
        best_per_dimension = {}
        for dim_name, _, _ in self.archive.grid_spec.dimensions:
            best_per_dimension[f"best_{dim_name}"] = 0.0

        for _coords, program in self.archive.archive.items():
            descriptor = self.feature_extractor.extract(program, self.feature_names)
            for feature_name, _value in descriptor.features.items():
                key = f"best_{feature_name}"
                if key in best_per_dimension:
                    current_best = best_per_dimension[key]
                    if program.score > current_best:
                        best_per_dimension[key] = program.score

        metrics.update(
            {
                "type": "MAP-Elites",
                "coverage": coverage,
                "occupied_cells": occupied_cells,
                "total_cells": total_cells,
                "total_evaluations": self.total_evaluations,
                "improvements": self.improvements,
                "improvement_rate": self.improvements / self.total_evaluations if self.total_evaluations > 0 else 0,
                **best_per_dimension,
            }
        )

        return metrics

    def get_archive_visualization(self) -> Dict[str, Any]:
        """Get data for visualizing the archive."""
        if not self.archive:
            return {}

        return {
            "grid": self.archive.get_elite_grid().tolist(),
            "dimensions": [
                {"name": name, "range": bounds, "bins": bins}
                for name, bounds, bins in self.archive.grid_spec.dimensions
            ],
            "coverage_history": self.archive.coverage_history,
            "events": self.archive.history[-100:],  # Last 100 events
        }


# Register the strategy
StrategyFactory.register("map_elites", MAPElitesStrategy)
