# Evolv Scripts

This directory contains utility scripts for the Evolv framework.

## test_evolution.py

Quick testing script for debugging individual examples with enhanced logging.

### Purpose

- Run individual examples with detailed logging
- Debug evolution issues with better visibility
- Quick development testing without comprehensive validation
- Logs to both console and `evolution.log` file

### Usage

```bash
# Test default example (breast_cancer_example.py)
EVOLVE=1 uv run python scripts/test_evolution.py

# Test specific example
EVOLVE=1 uv run python scripts/test_evolution.py examples/simple_example.py

# Enable debug logging
DEBUG=1 EVOLVE=1 uv run python scripts/test_evolution.py
```

### Features

- Clear evolution configuration display
- Reduced noise from external libraries (httpx, LiteLLM, modal, aider)
- Warnings when EVOLVE environment variable is not set
- Detailed error traces on failures
- Logs saved to `evolution.log` for later analysis

## test_e2e.py

Comprehensive end-to-end testing script for validating the entire Evolv workflow with real external APIs.

### Purpose

- Validates evolution actually improves code performance
- Tests integration between all components (DSPy, Aider, Modal/Local executor)
- Generates detailed reports for analysis
- Ensures the framework works correctly with real LLM APIs

### Usage

```bash
# Run all example scenarios
./scripts/test_e2e.py

# Run specific scenarios
./scripts/test_e2e.py --scenarios examples/simple_example.py examples/regression_example.py

# Use local executor instead of Modal
./scripts/test_e2e.py --executor local

# Run with more iterations
./scripts/test_e2e.py --iterations 5

# Enable verbose logging
./scripts/test_e2e.py --verbose

# Save report to custom location
./scripts/test_e2e.py --output my_report.json
```

### Requirements

1. **Environment Variables**:
   - `OPEN_ROUTER_API_KEY`: Required for LLM access
   - `MODAL_TOKEN_ID`: Required if using Modal executor

2. **Tools**:
   - Aider installed: `uv tool install aider-chat`
   - Modal CLI (if using Modal): `pip install modal`

3. **Local Development**:
   - Use `--executor local` to run without Modal dependency
   - Configure resource limits via environment variables:
     - `LOCAL_EXECUTOR_MEMORY_MB=512`
     - `LOCAL_EXECUTOR_CPU_PERCENT=80`

### Output

The script generates:
- `e2e_test.log`: Detailed execution logs
- `e2e_report.json`: Structured test results including:
  - Success/failure status per scenario
  - Performance improvements (initial vs final fitness)
  - Execution times
  - Error details if any

### Example Report

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_scenarios": 3,
  "passed": 3,
  "failed": 0,
  "results": [
    {
      "scenario": "simple_example",
      "success": true,
      "iterations_run": 3,
      "initial_fitness": 0.65,
      "final_fitness": 0.89,
      "improvement": 36.9,
      "duration_seconds": 45.2,
      "variants_generated": 6
    }
  ]
}
```

### Best Practices

1. **API Costs**: Be aware that running E2E tests uses real API calls and incurs costs
2. **Timeouts**: Default timeout is 5 minutes per scenario
3. **Parallel Execution**: The script uses conservative parallelism (2 variants) for stability
4. **Local Testing**: Use local executor during development to avoid Modal costs

### Troubleshooting

- **"Missing environment variable"**: Set required API keys
- **"Aider not installed"**: Run `uv tool install aider-chat`
- **"Evolution was not enabled"**: Check EVOLVE environment variable is set
- **Timeout errors**: Increase timeout or reduce iterations
- **Memory errors with local executor**: Increase `LOCAL_EXECUTOR_MEMORY_MB`
