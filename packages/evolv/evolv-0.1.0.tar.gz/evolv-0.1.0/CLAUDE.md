# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the Evolv framework.

## 🎯 Claude Code Working Principles

When working on Evolv, follow these principles for maximum efficiency:

1. **Think First, Act Second**: Use deep thinking for complex problems before implementing
2. **Test-Driven Development**: Write failing tests before implementation
3. **Incremental Progress**: Make small, verifiable changes rather than large rewrites
4. **Parallel Workflows**: Use multiple terminal sessions for tests, type checking, and editing
5. **Fail Fast**: Run `make pr-ready` frequently to catch issues early
6. **Learn from History**: Check docs/error-log.md and ADRs before implementing

**📚 For maximum autonomy, see: [SUPER_AGENTIC_MODE.md](SUPER_AGENTIC_MODE.md)**
**🎩 For advanced features, see: [HIDDEN_FEATURES.md](docs/HIDDEN_FEATURES.md)**

### Optimal Workflow for New Features
```
1. Read issue → 2. Search codebase → 3. Write tests → 4. Implement → 5. Verify → 6. Document
```

### When Stuck
- Check `docs/error-log.md` for similar issues
- Use Task tool for complex searches across codebase
- Run minimal reproduction scripts
- Add debug logging with `EVOLVE_DEBUG=1`

## 🚀 Automation Scripts

### Claude Tasks Helper
A specialized automation script for common development tasks:

```bash
# Start working on a new issue
python scripts/claude_tasks.py new_issue 42

# Find all usages of a class
python scripts/claude_tasks.py find_usage "Program"

# Run performance benchmarks
python scripts/claude_tasks.py benchmark async

# Compare performance after changes
python scripts/claude_tasks.py compare_benchmark async

# Run tests matching a pattern
python scripts/claude_tasks.py test_pattern "test_async"

# Debug a specific test
python scripts/claude_tasks.py debug_test "src/tests/test_coordinator.py::test_evolution"

# Apply common quick fixes
python scripts/claude_tasks.py quick_fix
```

### Code Templates
Pre-built templates for common implementations:

```bash
# Templates available in .claude/templates/
- new_strategy.py         # Template for new evolution strategies
- test_new_strategy.py    # Test template for strategies
- feature_workflow.md     # Step-by-step feature implementation guide

# Usage example:
# 1. Copy template: cp .claude/templates/new_strategy.py src/evolve/strategies/my_strategy.py
# 2. Replace placeholders with actual implementation
# 3. Follow TDD workflow in feature_workflow.md
```

## Quick Start

```bash
# 1. Install dependencies
uv sync --all-extras
uv tool install aider-chat

# 2. Set up environment
export OPEN_ROUTER_API_KEY="your_key_here"
modal token new  # For cloud execution

# 3. Run evolution
EVOLVE=1 python examples/simple_example.py
```

## Development Commands

### Testing
```bash
# Run all tests with verbose output
uv run pytest -s -v

# Run specific test file
uv run pytest -s -v src/tests/test_coordinator.py

# Run tests with coverage
uv run pytest -v --cov=src/evolve --cov-report=term-missing

# Run end-to-end tests with real APIs
./scripts/test_e2e.py --scenario simple --verbose
./scripts/test_e2e.py --scenario all --iterations 5
```

### Code Quality
```bash
# Install development dependencies
uv sync --all-extras

# Run linting and auto-fix issues
uv run ruff check . --fix
uv run ruff format .

# Check linting without fixes
uv run ruff check .
uv run ruff format --check .

# Run type checking (currently relaxed settings)
uv run mypy src/evolve

# Run all pre-commit hooks
pre-commit run --all-files

# Install pre-commit hooks (one-time setup)
uv tool install pre-commit --with pre-commit-uv
pre-commit install
```

### Package Management
```bash
# Install dependencies in development mode
uv install -e .

# Add new dependency
uv add package-name

# Install Aider as a tool (required external tool)
uv tool install aider-chat
```

### Environment Setup
```bash
# Configure Modal token (required for sandbox execution)
modal token new

# Set required environment variables
export OPEN_ROUTER_API_KEY="your_key_here"
export OPENROUTER_MODEL="openrouter/openai/gpt-4.1"  # optional
export EVOLVE_ITERATIONS="3"  # optional
export PRIMARY_METRIC="fitness"  # optional
```

### Running Evolution
```bash
# Basic evolution
EVOLVE=1 python your_script.py

# With custom iterations
EVOLVE=1 EVOLVE_ITERATIONS=5 python your_script.py

# Async parallel evolution (4 variants at once)
EVOLVE=1 EVOLVE_PARALLEL=4 python your_script.py

# With specific strategy
EVOLVE=1 EVOLVE_STRATEGY=tournament python your_script.py

# Local execution (no Modal required)
EVOLVE=1 EVOLVE_EXECUTOR=local python your_script.py
```

## Architecture Overview

**Evolv** is an AI-driven framework that automatically improves Python code through evolutionary algorithms, using LLMs to generate and apply intelligent modifications.

### Core Components

1. **AsyncEvolutionCoordinator** (`src/evolve/coordinator_async.py`) ✅
   - Async-first architecture for 3-5x performance improvement
   - Parallel variant generation and evaluation
   - Progress tracking and resource management via semaphores
   - Backward compatible with sync mode

2. **Evolution Strategies** (`src/evolve/strategies/`) ✅
   - **Modular System**: Base classes for custom strategies
   - **LinearStrategy**: Sequential evolution (default)
   - **RandomStrategy**: Random parent selection
   - **TournamentStrategy**: Competition-based selection
   - **MAP-Elites**: Quality-diversity optimization (PR #35)
   - **Island Evolution**: Parallel populations with migration (PR #36)

3. **Executors** (`src/evolve/executor_async.py`) ✅
   - **AsyncModalExecutor**: Cloud execution with Modal
   - **AsyncLocalExecutor**: Simplified local execution
   - Configurable timeouts and resource limits
   - Automatic metrics extraction from `metrics.json`

4. **AI Integration**
   - **AsyncDSPyModule** (`src/evolve/llm_async.py`): Async LLM calls via OpenRouter
   - **AsyncAiderModule** (`src/evolve/aider_async.py`): Parallel code modifications
   - Context-aware prompting with evolution history
   - Automatic retry and error handling

### Evolution Workflow

1. **Setup**: Decorate target function/class with `@evolve` and main with `@main_entrypoint`
2. **Execution**: Set `EVOLVE=1` to activate evolution mode
3. **Evolution Loop** (async by default):
   - Initial code evaluated to establish baseline
   - For each iteration (parallel variants):
     - Strategy selects parent programs
     - LLM generates improvement suggestions
     - Aider applies modifications
     - Variants execute in parallel
     - Best performers added to database
4. **Result**: Best evolved code printed and saved

### Key Features

- **🚀 Async-First**: 3-5x faster with parallel variant generation
- **🧬 Modular Strategies**: Pluggable algorithms (Linear, Tournament, MAP-Elites, Islands)
- **☁️ Flexible Execution**: Modal cloud or local subprocess
- **📊 Metrics-Driven**: Evolution guided by custom fitness functions
- **🔄 Automatic Rollback**: Failed variants don't affect evolution
- **📈 Progress Tracking**: Real-time updates with tqdm

## Project Structure

```
evolve/
├── src/evolve/
│   ├── coordinator_async.py    # Async evolution orchestrator
│   ├── strategies/             # Evolution algorithms
│   │   ├── base.py            # Strategy interfaces
│   │   ├── basic.py           # Linear, Random, Tournament
│   │   ├── map_elites.py      # Quality-diversity optimization
│   │   └── islands.py         # Parallel populations
│   ├── executor_async.py       # Modal/Local execution
│   ├── llm_async.py           # LLM integration
│   └── aider_async.py         # Code modification
├── examples/
│   ├── simple_example.py      # Iris classification
│   ├── regression_example.py  # California housing
│   └── island_evolution_example.py  # Advanced strategies
├── scripts/
│   └── test_e2e.py           # End-to-end testing
└── docs/
    └── strategies/            # Strategy documentation
```

## External Dependencies

- **Aider**: AI coding assistant (installed via `uv tool install aider-chat`)
- **Modal**: Cloud execution platform (requires account and `modal token new`)
- **OpenRouter**: LLM API access (requires `OPEN_ROUTER_API_KEY`)

## Testing Strategy

### Unit Tests
- Comprehensive mocking of external services (Modal, Aider, LLMs)
- Async test fixtures with `pytest-asyncio`
- State isolation between tests
- ~95% code coverage

### Integration Tests
- Strategy-specific test suites
- Performance benchmarks for async vs sync
- Concurrency and resource limit testing

### End-to-End Tests
```bash
# Test with real APIs (requires keys)
./scripts/test_e2e.py --scenario simple
./scripts/test_e2e.py --scenario all --iterations 5

# Scenarios available:
# - simple: Basic Iris classification
# - regression: California housing
# - custom: Multi-metric fitness
# - strategies: Compare all strategies
# - async: Performance benchmarks
```

## Configuration

### Environment Variables
```bash
# Required
OPEN_ROUTER_API_KEY="sk-or-..."      # OpenRouter API key

# Optional
OPENROUTER_MODEL="openai/gpt-4"      # LLM model (default: gpt-4o-mini)
EVOLVE_ITERATIONS="5"                 # Evolution iterations (default: 3)
PRIMARY_METRIC="accuracy"             # Metric to optimize (default: fitness)
EVOLVE_EXECUTOR="local"               # Executor type: modal/local (default: modal)
LOCAL_EXECUTOR_TIMEOUT="30"           # Local execution timeout in seconds
EVOLVE_PARALLEL="4"                   # Parallel variants (default: 4)
EVOLVE_STRATEGY="tournament"          # Evolution strategy (default: linear)
```

### Modal Configuration
- Sandbox includes: pandas, scikit-learn, numpy, matplotlib
- Default timeout: 60 seconds
- Memory: 1GB per execution
- CPU: 1.0 core allocation

### Aider Configuration
- Non-interactive mode enabled
- Auto-commits disabled
- AST-based code extraction

## Development Standards

### Code Style
- **Line length**: 120 characters
- **Formatting**: Ruff (compatible with Black)
- **Import sorting**: Handled by Ruff's isort rules
- **Type hints**: Encouraged but not strictly enforced (mypy in permissive mode)

### Pre-commit Hooks
The following checks run automatically on commit:
- Ruff linting and formatting
- Trailing whitespace removal
- End-of-file fixing
- YAML/TOML validation
- Large file detection (5MB limit)

### CI/CD Pipeline
GitHub Actions runs on every PR:
- Tests on Python 3.9, 3.10, 3.11, and 3.12
- Linting and formatting verification
- Test coverage reporting
- Pre-commit validation

### Dependency Management
- Always use `uv add` to add dependencies (not manual pyproject.toml edits)
- Install tools with `uv tool install` for isolation
- Run `uv sync --all-extras` after pulling changes

## Current Development Status (v2.0)

### ✅ Completed Features
1. **Modular Strategy System** (#1, PR #32)
   - Base classes and factory pattern
   - Linear, Random, Tournament strategies
   - Full test coverage

2. **Async-First Architecture** (#6, PR #33)
   - 3-5x performance improvement
   - Parallel variant generation
   - Progress tracking with tqdm
   - Backward compatible

3. **End-to-End Testing** (#15, PR #34)
   - Comprehensive test script
   - Real API validation
   - Performance benchmarks

### 🚧 In Progress
1. **MAP-Elites Strategy** (#2, PR #35)
   - Quality-diversity optimization
   - Multi-dimensional archives
   - Feature extraction system

2. **Island-Based Evolution** (#3, PR #36)
   - Parallel populations
   - Migration topologies
   - Heterogeneous LLM support

### 📋 Upcoming Features
- **Multi-Objective Optimization** (#21): Pareto frontiers
- **Enhanced LLM Prompting** (#20): Context-aware suggestions
- **Parallel Variant Generation** (#23): Further performance gains
- **Visual Evolution Demos** (#26): Interactive visualizations

## Usage Examples

### Basic Evolution
```python
from evolve import evolve, main_entrypoint

@evolve(goal="Improve accuracy while reducing complexity")
def classify(X, y):
    # Your ML code here
    return model

@main_entrypoint
def main():
    # Load data and evaluate
    metrics = {"fitness": accuracy}
    return metrics
```

### Advanced Strategies
```python
# MAP-Elites for multi-objective optimization
@evolve(
    goal="Balance speed and accuracy",
    strategy="map_elites",
    strategy_config={
        "features": [
            ("speed", (0.0, 1.0), 20),
            ("accuracy", (0.0, 1.0), 20)
        ],
        "initial_population": 50,
        "crossover_rate": 0.3
    }
)

# Island evolution with heterogeneous populations
@evolve(
    goal="Find diverse high-quality solutions",
    strategy="heterogeneous_islands",
    strategy_config={
        "num_islands": 4,
        "topology": "ring",
        "island_configs": [
            {"mutation_rate": 0.3, "llm_model": "gpt-4o-mini"},
            {"mutation_rate": 0.9, "llm_model": "claude-3-haiku"},
        ]
    }
)
```

## Development Workflows

### 🎯 Issue Resolution Workflow (TDD Approach)
```bash
# 1. Setup: Create branch and understand the issue
gh issue view XX  # Read issue details
git checkout -b feature/issue-XX-description
cat .github/issues/XX_issue_name.md  # Read full specification

# 2. Explore: Understand existing code
rg "relevant_keyword" --type py  # Find related code
grep -r "ClassName" src/  # Search for specific implementations

# 3. Plan: Write failing tests first
# Create test file or add to existing
uv run pytest -xvs src/tests/test_new_feature.py  # Verify tests fail

# 4. Implement: Make tests pass incrementally
# Write minimal code to pass each test
uv run pytest -xvs src/tests/test_new_feature.py::test_specific  # Test specific case

# 5. Verify: Run all quality checks
make pr-ready  # Runs all checks (see Makefile)

# 6. Submit: Create PR with context
gh pr create --title "feat: Implement XX" --body "Closes #XX"
```

### 🚀 Rapid Development Workflow
```bash
# For complex features, use parallel exploration
# Terminal 1: Run tests in watch mode
while true; do uv run pytest -xvs src/tests/test_feature.py; sleep 2; done

# Terminal 2: Run type checking
while true; do uv run mypy src/evolve/feature.py; sleep 2; done

# Terminal 3: Edit code
# Claude Code will see test output and adapt
```

### 🧪 Performance Testing Workflow
```bash
# 1. Baseline: Measure current performance
./scripts/test_e2e.py --scenario async --iterations 10 > baseline.txt

# 2. Implement: Make changes

# 3. Compare: Measure improvement
./scripts/test_e2e.py --scenario async --iterations 10 > improved.txt
diff baseline.txt improved.txt
```

### 🐛 Debug Workflow
```bash
# 1. Reproduce: Create minimal test case
echo "import evolve; print(evolve.__version__)" > debug.py
python debug.py

# 2. Trace: Add strategic logging
export EVOLVE_DEBUG=1  # Enable debug logging
python -m pdb debug.py  # Use debugger

# 3. Fix: Apply targeted solution
```

### ✅ Pre-PR Checklist Command
```bash
# Single command to run before any PR
make pr-ready

# Or manually:
uv run pytest -v && \
uv run ruff check . --fix && \
uv run ruff format . && \
./scripts/test_e2e.py --scenario simple --iterations 1 && \
git status
```

## 🤖 Claude Code Automation Patterns

### Tool Selection Guide
```
When to use which tool:
- Task tool: For complex searches spanning multiple files
- Grep/Glob: For targeted searches when you know the pattern
- Read: For specific file examination
- MultiEdit: For multiple changes to the same file
- Bash: For running commands and checking outputs
```

### Common Quick Fixes
```bash
# Ruff formatting error in CI
uv run ruff format src/evolve/

# Import sorting issues
uv run ruff check --select I --fix .

# Floating point test failures
# Replace: assert result == 0.9
# With: assert abs(result - 0.9) < 0.0001

# Missing type hints
# Add: from typing import Dict, List, Optional, Any

# Async test failures
# Ensure: @pytest.mark.asyncio decorator is present
```

### Subagent Patterns for Complex Tasks
```bash
# Pattern 1: Parallel Feature Implementation
# Use Task tool to delegate complex searches:
# "Find all files that import Program class and analyze their usage patterns"

# Pattern 2: Comprehensive Refactoring
# "Refactor all database access to use async patterns:
#  1. Find all database calls
#  2. Create async versions
#  3. Update all callers
#  4. Verify tests still pass"

# Pattern 3: Performance Analysis
# "Analyze performance bottlenecks in evolution loop:
#  1. Profile current implementation
#  2. Identify slow operations
#  3. Suggest optimizations
#  4. Benchmark improvements"
```

### Visual Target Workflows
```bash
# When implementing UI or visual features:
# 1. Request screenshot/mockup from user
# 2. Break down into components
# 3. Implement test-first with expected outputs
# 4. Iterate until visual matches

# For data visualizations:
# 1. Create test data
# 2. Generate plot
# 3. Save to file
# 4. Iterate based on output
```

## Important Notes

- **Always commit normally** (not `git commit -n`) to trigger pre-commit hooks
- **Test before pushing**: CI is strict about formatting and tests
- **Use async patterns**: All new features should support async execution
- **Document thoroughly**: Examples and docstrings are essential
- **Think before acting**: Use deep thinking for complex problems
- **Test incrementally**: Verify each step before proceeding

## Learning Resources

When working on Evolv, consult these resources to avoid past mistakes:

1. **Architecture Decision Records**: `docs/adr/` - Why key decisions were made
2. **Development Patterns**: `docs/development-patterns.md` - What works and what doesn't
3. **Error Log**: `docs/error-log.md` - Past errors and their solutions
4. **Codebase Map**: `docs/codebase-map.md` - Visual guide to navigate the code

### Common Gotchas

- **DSPy accepts Pydantic models directly** - No need for manual JSON formatting
- **Use approximate float comparisons in tests** - `abs(a - b) < 0.0001`
- **Run `ruff format` before pushing** - Avoids CI failures
- **Start simple** - Test library capabilities before building abstractions

## 🎯 Claude Code Efficiency Summary

This CLAUDE.md has been enhanced with best practices from Anthropic's Claude Code guide to help you work more efficiently:

### 1. **Structured Workflows**
- TDD-focused issue resolution workflow
- Performance benchmarking workflow
- Debug workflow with specific steps
- Visual target workflows for UI features

### 2. **Automation Tools**
- `make pr-ready` - Single command for all pre-PR checks
- `claude_tasks.py` - Automated common tasks
- Templates in `.claude/templates/` - Boilerplate for new features

### 3. **Quick References**
- Tool selection guide (when to use Task vs Grep vs Read)
- Common quick fixes for CI failures
- Subagent patterns for complex tasks
- Error solutions in `docs/error-log.md`

### 4. **Learning Resources**
- Architecture Decision Records (ADRs)
- Development patterns documentation
- Codebase visualization map
- Historical error log

### 5. **Key Principles**
- Think first, act second
- Test-driven development
- Incremental progress
- Fail fast with frequent checks
- Learn from documented history

**Remember**: The goal is to help you be more autonomous and efficient. Use these tools and workflows to work faster while maintaining code quality.
