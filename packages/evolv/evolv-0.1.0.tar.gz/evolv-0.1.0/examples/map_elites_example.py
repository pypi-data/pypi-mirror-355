#!/usr/bin/env python
"""Example demonstrating MAP-Elites evolution strategy.

This example evolves a sorting algorithm, exploring different trade-offs
between execution speed and code complexity.
"""

import json
import time

from evolve import evolve, main_entrypoint


@evolve(
    goal="Create efficient sorting algorithms with different speed/complexity trade-offs",
    strategy="map_elites",
    strategy_config={
        "features": [
            ("execution_time", (0.0001, 0.01), 10),  # 10 bins for execution time
            ("complexity", (1, 20), 10),  # 10 bins for cyclomatic complexity
        ],
        "selection": "curiosity",  # Explore less-visited regions
    },
    iterations=5,
)
def sort_algorithm(arr):
    """Sort an array of integers."""
    # Initial implementation: simple bubble sort
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


@main_entrypoint
def main():
    """Test the sorting algorithm and measure performance."""
    import random

    # Generate test data
    test_sizes = [10, 50, 100, 500]
    test_arrays = [[random.randint(1, 1000) for _ in range(size)] for size in test_sizes]

    # Measure execution time
    total_time = 0
    correct = True

    for test_array in test_arrays:
        arr_copy = test_array.copy()

        start = time.time()
        result = sort_algorithm(arr_copy)
        end = time.time()

        total_time += end - start

        # Verify correctness
        expected = sorted(test_array)
        if result != expected:
            correct = False
            break

    # Calculate average execution time
    avg_time = total_time / len(test_arrays)

    # Calculate fitness (prioritize correctness, then speed)
    if correct:
        # Fitness inversely proportional to execution time
        # Scale to [0, 1] range
        fitness = max(0, 1 - avg_time * 100)  # Assuming times are in 0.01s range
    else:
        fitness = 0.0

    metrics = {
        "fitness": fitness,
        "execution_time": avg_time,
        "correct": correct,
        "total_time": total_time,
    }

    print(f"Metrics: {json.dumps(metrics, indent=2)}")
    return metrics


if __name__ == "__main__":
    main()


# Running this example with evolution:
# EVOLVE=1 python examples/map_elites_example.py
#
# MAP-Elites will:
# 1. Maintain a 10x10 grid of solutions
# 2. Each cell represents a unique combination of speed and complexity
# 3. Only the best solution for each cell is kept
# 4. Curiosity-based selection explores under-represented regions
# 5. Over iterations, you'll see diverse sorting implementations
#    (bubble sort, insertion sort, quicksort variants, etc.)
#
# The archive will contain:
# - Simple but slow algorithms (high complexity, high execution time)
# - Complex but fast algorithms (low execution time, high complexity)
# - Balanced solutions (medium complexity, medium speed)
# - Potentially discover novel sorting approaches!
