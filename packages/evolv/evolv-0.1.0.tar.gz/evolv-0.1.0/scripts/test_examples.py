#!/usr/bin/env python
"""Simple test to verify examples run without errors."""

import os
import subprocess
import sys
from pathlib import Path


def test_example(example_path):
    """Run example and return True if it succeeds."""
    cmd = [sys.executable, str(example_path)]
    env = os.environ.copy()
    env.update({"EVOLVE": "1", "EVOLVE_ITERATIONS": "1", "EVOLVE_EXECUTOR_TYPE": "local"})

    print(f"Testing {example_path.name}...", end=" ", flush=True)
    result = subprocess.run(cmd, env=env, capture_output=True, timeout=120)

    if result.returncode == 0:
        print("✓")
        return True
    else:
        print("✗")
        return False


def main():
    examples = list(Path("examples").glob("*.py"))
    passed = sum(test_example(ex) for ex in examples)

    print(f"\n{passed}/{len(examples)} examples passed")
    return 0 if passed == len(examples) else 1


if __name__ == "__main__":
    sys.exit(main())
