# Testing Organization

This document describes the testing infrastructure for the Evolve framework.

## Testing Tools

### 1. Unit Tests (`src/tests/`)
All unit tests are organized in the `src/tests/` directory. Run with:
```bash
uv run pytest
```

### 2. Development Testing (`scripts/test_evolution.py`)
For debugging individual examples with enhanced logging:
```bash
# Test default example
EVOLVE=1 uv run python scripts/test_evolution.py

# Test specific example
EVOLVE=1 uv run python scripts/test_evolution.py examples/simple_example.py
```

### 3. Quick Testing (`scripts/test_examples.py`)
Simple verification that all examples run without errors:
```bash
uv run python scripts/test_examples.py
```

## Example Files

All examples are located in `examples/` directory:
- `simple_example.py` - Basic Iris classification
- `breast_cancer_example.py` - Binary classification
- `regression_example.py` - California housing regression
- `custom_fitness_example.py` - Multi-objective optimization
- `map_elites_example.py` - Quality-diversity algorithm
- `island_evolution_example.py` - Parallel populations
- `heterogeneous_islands_example.py` - Different LLMs per island

## Testing Workflow

### Quick Check
```bash
# Verify all examples work
uv run python scripts/test_examples.py
```

### Debug Issues
```bash
# Use test_evolution.py for detailed logging
EVOLVE=1 uv run python scripts/test_evolution.py examples/problematic_example.py
```

### Full Validation
```bash
# Run unit tests
uv run pytest -v

# Test with Modal
EVOLVE=1 EVOLVE_EXECUTOR_TYPE=modal uv run python examples/simple_example.py
```

## Summary

- **Unit tests**: For testing framework internals
- **test_examples.py**: Quick smoke test for all examples
- **test_evolution.py**: Detailed debugging tool
- **Direct execution**: Run examples directly for specific testing
