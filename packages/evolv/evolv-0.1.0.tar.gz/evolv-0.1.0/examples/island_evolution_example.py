#!/usr/bin/env python
"""Example demonstrating island-based evolution strategy.

This example demonstrates the island-based evolution feature from Issue #19,
evolving a numerical optimization function using multiple isolated populations
that occasionally share their best solutions through migration.
"""

import json
import math
import time

from evolve import evolve, main_entrypoint


@evolve(
    goal="Find the global optimum of a complex multi-modal function",
    strategy="islands",
    strategy_config={
        "num_islands": 5,  # 5 separate populations
        "island_size": 20,  # 20 programs per island
        "topology": "ring",  # Islands connected in a ring
        "migration_rate": 0.1,  # 10% of population migrates
        "migration_interval": 5,  # Every 5 generations
    },
    iterations=10,
)
def optimize_function(x, y):
    """Find the maximum of a complex 2D function.

    This function has multiple local maxima, making it challenging
    for traditional optimization. Islands help explore different regions.
    """
    # Initial simple approach: just return a basic calculation
    return -(x**2 + y**2)  # Simple parabola (wrong!)


@main_entrypoint
def main():
    """Test the optimization function on a grid of points."""
    import numpy as np

    # Define the true function we're trying to approximate
    # This has multiple peaks - perfect for island evolution!
    def true_function(x, y):
        # Rastrigin-like function with multiple local maxima
        term1 = 20 + x**2 + y**2
        term2 = 10 * (math.cos(2 * math.pi * x) + math.cos(2 * math.pi * y))
        return -(term1 - term2)  # Negate for maximization

    # Test on a grid of points
    test_points = []
    true_values = []

    # Create test grid
    for x in np.linspace(-5, 5, 20):
        for y in np.linspace(-5, 5, 20):
            test_points.append((x, y))
            true_values.append(true_function(x, y))

    # Evaluate our function
    start_time = time.time()
    predicted_values = []
    errors = []

    for x, y in test_points:
        try:
            pred = optimize_function(x, y)
            predicted_values.append(pred)
            true_val = true_function(x, y)
            errors.append(abs(pred - true_val))
        except Exception:
            predicted_values.append(float("-inf"))
            errors.append(float("inf"))

    execution_time = time.time() - start_time

    # Calculate metrics
    mean_error = sum(errors) / len(errors) if errors else float("inf")

    # Find how well we approximate the global maximum
    max_true = max(true_values)
    max_pred = max(predicted_values) if predicted_values else float("-inf")
    max_error = abs(max_true - max_pred)

    # Fitness based on accuracy and finding the global optimum
    fitness = 1.0 / (1.0 + mean_error) * (1.0 / (1.0 + max_error))

    metrics = {
        "fitness": fitness,
        "mean_error": mean_error,
        "max_error": max_error,
        "execution_time": execution_time,
        "num_evaluations": len(test_points),
        "global_max_found": max_error < 0.1,
    }

    print(f"Metrics: {json.dumps(metrics, indent=2)}")
    return metrics


if __name__ == "__main__":
    main()


# Running this example with evolution:
# EVOLVE=1 python examples/island_evolution_example.py
#
# Island evolution helps because:
# 1. Different islands can explore different regions of the solution space
# 2. Ring topology allows gradual spread of good solutions
# 3. Migration prevents islands from getting stuck in local optima
# 4. Each island can develop different approaches
#
# You might see evolution discovering:
# - Islands focusing on different peaks in the function
# - Some islands finding trigonometric patterns
# - Migration spreading successful patterns
# - Eventually converging on the true Rastrigin-like form
#
# The ring topology means:
# - Island 0 → Island 1 → Island 2 → Island 3 → Island 4 → Island 0
# - Good solutions spread gradually around the ring
# - Allows both exploration (isolated evolution) and exploitation (migration)
