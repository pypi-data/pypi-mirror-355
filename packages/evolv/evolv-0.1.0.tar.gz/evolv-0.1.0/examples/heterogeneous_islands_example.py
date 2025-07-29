#!/usr/bin/env python
"""Example demonstrating heterogeneous island evolution.

This example uses different LLM models and evolution parameters on each
island to explore diverse solution strategies for a complex problem.
"""

import json
import time

from evolve import evolve, main_entrypoint


@evolve(
    goal="Create an efficient text parser that handles various formats and edge cases",
    strategy="heterogeneous_islands",
    strategy_config={
        "num_islands": 4,
        "island_size": 15,
        "topology": "fully_connected",  # All islands can share solutions
        "migration_rate": 0.15,
        "migration_interval": 3,
        # Each island has different characteristics
        "island_configs": [
            {
                # Conservative island - careful, incremental changes
                "mutation_rate": 0.3,
                "prompt_style": "conservative",
                "llm_temperature": 0.3,
            },
            {
                # Balanced island - moderate exploration
                "mutation_rate": 0.6,
                "prompt_style": "balanced",
                "llm_temperature": 0.6,
            },
            {
                # Creative island - bold, experimental changes
                "mutation_rate": 0.9,
                "prompt_style": "creative",
                "llm_temperature": 0.9,
            },
            {
                # Analytical island - systematic improvements
                "mutation_rate": 0.5,
                "prompt_style": "analytical",
                "llm_temperature": 0.5,
            },
        ],
    },
    iterations=8,
)
def parse_data(text):
    """Parse structured data from various text formats.

    Should handle JSON-like, CSV-like, and custom formats.
    Returns a list of dictionaries.
    """
    # Initial naive implementation
    result = []
    lines = text.strip().split("\n")
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            result.append({key.strip(): value.strip()})
    return result


@main_entrypoint
def main():
    """Test the parser on various formats."""

    # Test cases with different formats
    test_cases = [
        # Simple key-value
        {"input": "name: John\nage: 30\ncity: NYC", "expected": [{"name": "John"}, {"age": "30"}, {"city": "NYC"}]},
        # CSV-like
        {
            "input": "name,age,city\nJohn,30,NYC\nJane,25,LA",
            "expected": [{"name": "John", "age": "30", "city": "NYC"}, {"name": "Jane", "age": "25", "city": "LA"}],
        },
        # JSON-like
        {
            "input": '{"name": "John", "age": 30}\n{"name": "Jane", "age": 25}',
            "expected": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}],
        },
        # Mixed format with edge cases
        {
            "input": "user:admin:true\nstatus: active : valid\ncount::5",
            "expected": [{"user": "admin:true"}, {"status": "active : valid"}, {"count": ":5"}],
        },
        # Empty and whitespace
        {"input": "  \n\nkey: value\n  \n", "expected": [{"key": "value"}]},
    ]

    # Evaluate parser
    total_correct = 0
    total_cases = 0
    errors = []
    execution_times = []

    for i, test in enumerate(test_cases):
        start = time.time()
        try:
            result = parse_data(test["input"])
            execution_times.append(time.time() - start)

            # Check correctness
            if result == test["expected"]:
                total_correct += 1
            else:
                errors.append(f"Test {i}: Expected {test['expected']}, got {result}")
            total_cases += 1
        except Exception as e:
            errors.append(f"Test {i}: Exception: {e!s}")
            execution_times.append(0.1)  # Penalty
            total_cases += 1

    # Calculate metrics
    accuracy = total_correct / total_cases if total_cases > 0 else 0
    avg_time = sum(execution_times) / len(execution_times) if execution_times else 0.1

    # Fitness combines accuracy and efficiency
    fitness = accuracy * (1.0 / (1.0 + avg_time * 10))

    metrics = {
        "fitness": fitness,
        "accuracy": accuracy,
        "execution_time": avg_time,
        "correct_cases": total_correct,
        "total_cases": total_cases,
        "errors": len(errors),
        "error_details": errors[:3] if errors else [],  # First 3 errors
    }

    print(f"Metrics: {json.dumps(metrics, indent=2)}")
    return metrics


if __name__ == "__main__":
    main()


# Running this example:
# EVOLVE=1 python examples/heterogeneous_islands_example.py
#
# Benefits of heterogeneous islands:
#
# 1. **Conservative Island** (Low mutation, Low temperature):
#    - Makes careful, incremental improvements
#    - Good at refining existing parsing logic
#    - Less likely to break working code
#
# 2. **Balanced Island** (Medium settings):
#    - Explores moderate changes
#    - Good general-purpose evolution
#    - Balances exploration and exploitation
#
# 3. **Creative Island** (High mutation, High temperature):
#    - Makes bold, experimental changes
#    - Might discover novel parsing approaches
#    - Can escape local optima
#
# 4. **Analytical Island** (Medium mutation, focused prompts):
#    - Systematic improvements
#    - Good at handling edge cases
#    - Methodical approach to problem-solving
#
# With fully connected topology:
# - All islands share their best solutions
# - Allows rapid spread of good ideas
# - Creative solutions can be refined by conservative islands
# - Different approaches can be combined
#
# You might see:
# - Creative island discovering regex patterns
# - Conservative island refining error handling
# - Analytical island systematically handling edge cases
# - Solutions migrating and combining across islands
