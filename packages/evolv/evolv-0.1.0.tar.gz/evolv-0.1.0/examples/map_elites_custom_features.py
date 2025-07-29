#!/usr/bin/env python
"""Example demonstrating MAP-Elites with custom feature extractors.

This example evolves a mathematical expression evaluator, exploring trade-offs
between accuracy, computational efficiency, and numerical stability.
"""

import ast
import json
import math
import time

from evolve import evolve, main_entrypoint
from evolve.database import Program


def count_math_operations(program: Program) -> float:
    """Count mathematical operations in the code."""
    try:
        tree = ast.parse(program.evolve_code)
        math_ops = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                math_ops += 1
            elif isinstance(node, ast.Call) and hasattr(node.func, "id"):
                if node.func.id in ["abs", "sqrt", "sin", "cos", "tan", "exp", "log"]:
                    math_ops += 1
        return float(math_ops)
    except Exception:
        return 0.0


def count_conditionals(program: Program) -> float:
    """Count conditional statements (if/else)."""
    try:
        tree = ast.parse(program.evolve_code)
        conditionals = sum(1 for node in ast.walk(tree) if isinstance(node, ast.If))
        return float(conditionals)
    except Exception:
        return 0.0


@evolve(
    goal="Evolv accurate and efficient mathematical expression evaluators with different approaches",
    strategy="map_elites",
    strategy_config={
        "features": [
            ("accuracy", (0.0, 1.0), 20),  # 20 bins for accuracy
            ("math_operations", (0, 50), 10),  # Custom: number of math operations
            ("conditionals", (0, 10), 5),  # Custom: number of conditionals
        ],
        "selection": "curiosity",
        "custom_extractors": {
            "math_operations": count_math_operations,
            "conditionals": count_conditionals,
        },
    },
    iterations=5,
)
def evaluate_expression(x, n=10):
    """Approximate sin(x) using Taylor series or other methods."""
    # Initial implementation: Simple Taylor series
    result = 0
    for i in range(n):
        sign = (-1) ** i
        result += sign * (x ** (2 * i + 1)) / math.factorial(2 * i + 1)
    return result


@main_entrypoint
def main():
    """Test the expression evaluator on various inputs."""
    import numpy as np

    # Test points
    test_points = np.linspace(-np.pi, np.pi, 50)

    # Calculate accuracy
    errors = []
    execution_times = []

    for x in test_points:
        start = time.time()
        try:
            approx = evaluate_expression(x)
            end = time.time()

            execution_times.append(end - start)

            # Compare with ground truth
            true_value = math.sin(x)
            error = abs(approx - true_value)
            errors.append(error)
        except Exception:
            # Handle numerical instability
            errors.append(float("inf"))
            execution_times.append(0.001)

    # Calculate metrics
    mean_error = np.mean([e for e in errors if not math.isinf(e)])
    accuracy = max(0, 1 - mean_error)  # Convert error to accuracy
    avg_time = np.mean(execution_times)

    # Check for numerical stability
    stable = all(not math.isinf(e) and not math.isnan(e) for e in errors)

    # Fitness combines accuracy and efficiency
    if stable:
        fitness = 0.7 * accuracy + 0.3 * (1 - min(avg_time * 1000, 1))
    else:
        fitness = accuracy * 0.5  # Penalize unstable solutions

    metrics = {
        "fitness": fitness,
        "accuracy": accuracy,
        "execution_time": avg_time,
        "mean_error": mean_error,
        "stable": stable,
        "max_error": max(errors) if errors else float("inf"),
    }

    print(f"Metrics: {json.dumps(metrics, indent=2)}")
    return metrics


if __name__ == "__main__":
    main()


# Running this example:
# EVOLVE=1 python examples/map_elites_custom_features.py
#
# MAP-Elites will explore different approximation methods:
# - Simple Taylor series (many math operations, no conditionals)
# - Padé approximants (balanced operations and conditionals)
# - Lookup tables with interpolation (few operations, many conditionals)
# - Chebyshev polynomials (optimized operation count)
# - Range-reduction techniques (conditionals for different ranges)
#
# The custom extractors help MAP-Elites understand the structure
# of each solution, leading to more diverse exploration!
