# Evolv Framework: Technical Implementation Guide

## Overview

This guide provides in-depth technical details about the Evolv framework's implementation, architecture decisions, and extension points for developers who want to understand or modify the framework.

## Core Architecture

### Module Structure

```
src/evolve/
├── __init__.py          # Public API exports
├── coordinator.py       # Main orchestration logic
├── database.py          # Program storage and sampling
├── executor.py          # Sandboxed code execution
├── dspy.py             # LLM integration for suggestions
├── aider.py            # Code modification via Aider
├── config.py           # Configuration management
└── errors.py           # Custom exception hierarchy
```

### Data Flow

```
User Code → @evolve decorator → EvolutionCoordinator
                                        ↓
                              Initial Execution (Modal)
                                        ↓
                                 ProgramDatabase
                                        ↓
                              Evolution Loop:
                                Parent Selection
                                        ↓
                              DSPy (LLM Suggestion)
                                        ↓
                                 Aider (Apply Changes)
                                        ↓
                               Execute Variant (Modal)
                                        ↓
                                Update Database
                                        ↓
                                  Best Program
```

## Key Components Deep Dive

### 1. EvolutionCoordinator (coordinator.py)

The central orchestrator managing the entire evolution process.

**Key Responsibilities:**
- Decorator implementation and metadata capture
- Mode detection (normal vs evolution)
- Evolution loop orchestration
- State management across iterations

**Important Methods:**
- `evolve()`: Decorator factory for marking evolution targets
- `main_entrypoint()`: Decorator for controlling execution modes
- `_orchestrate_evolution()`: Main evolution loop implementation
- `_get_evolution_target()`: Extracts AST and metadata

**Design Decisions:**
- Singleton pattern for coordinator instance
- Global state management for simplicity
- AST-based code extraction for reliability

### 2. ProgramDatabase (database.py)

Manages the evolutionary history and program selection.

**Core Classes:**
- `Program`: Dataclass holding code, metrics, and execution results
- `ProgramDatabase`: Storage and retrieval of program versions
- `SamplingStrategy`: Abstract base for selection algorithms
- `LinearSamplingStrategy`: Sequential parent selection
- `RandomSamplingStrategy`: Stochastic parent selection

**Key Features:**
- In-memory storage with O(1) lookups
- Automatic best program tracking
- Configurable primary metric
- Score normalization and error handling

**Extension Points:**
- Custom `SamplingStrategy` implementations
- Alternative storage backends (Redis, SQLite)
- Multi-objective optimization support

### 3. Executor (executor.py)

Handles safe, isolated code execution using Modal.

**Execution Environment:**
- Modal cloud containers
- Configurable package installation
- Directory mounting support
- Metrics collection via JSON

**Key Methods:**
- `run()`: Main execution entry point
- `_modal_run()`: Modal-decorated remote execution
- `_create_modal_executor()`: Dynamic Modal app creation

**Safety Features:**
- Isolated execution environment
- Resource limits (timeout, memory)
- Error capture and propagation
- Clean metrics extraction

### 4. DSPy Integration (dspy.py)

Generates improvement suggestions using LLMs.

**Components:**
- `CodeImprover`: DSPy signature for improvements
- `CodeImprovementModule`: DSPy module implementation
- `code_improvement_desc()`: Main interface function

**Prompt Engineering:**
- Context-aware prompts with full code
- Goal-driven suggestions
- Specific, actionable improvements
- Natural language descriptions

**Configuration:**
- OpenRouter API integration
- Configurable model selection
- Temperature and generation parameters

### 5. Aider Integration (aider.py)

Applies LLM-suggested changes to code.

**Process Flow:**
1. Write code to temporary file
2. Invoke Aider with improvement description
3. Parse Aider output for success
4. Extract modified entity using AST
5. Return complete modified code

**Key Features:**
- Non-interactive Aider operation
- AST-based entity extraction
- Error handling and validation
- Preservation of code structure

## Configuration System

### Configuration Hierarchy

1. **Default Values** (in code)
2. **Config File** (`evolve.json`)
3. **Environment Variables**
4. **Programmatic Override**

### Available Settings

```python
@dataclass
class EvolveConfig:
    api_key: str                    # OpenRouter API key
    model: str = "openrouter/openai/gpt-4o-mini"
    default_iterations: int = 3
    primary_metric: str = "fitness"
    temperature: float = 0.7
    modal_gpu: Optional[str] = None
    mount_dir: Optional[str] = None
    extra_packages: List[str] = field(default_factory=list)
```

## Error Handling

### Exception Hierarchy

```
EvolveError (base)
├── ConfigurationError
│   ├── MissingAPIKeyError
│   └── InvalidConfigError
├── ExecutionError
│   ├── TimeoutError
│   └── SandboxError
├── EvolutionError
│   ├── NoImprovementError
│   └── ConvergenceError
└── IntegrationError
    ├── AiderError
    └── DSPyError
```

### Error Recovery Strategies

1. **Execution Failures**: Mark program as failed, continue evolution
2. **LLM Failures**: Retry with backoff, skip iteration if persistent
3. **Aider Failures**: Log and continue with next iteration
4. **Critical Failures**: Clean shutdown with state preservation

## Testing Architecture

### Test Structure

```
src/tests/
├── test_coordinator.py   # Decorator and orchestration tests
├── test_database.py      # Storage and sampling tests
├── test_executor.py      # Execution isolation tests
├── test_dspy.py         # LLM integration tests
└── test_aider.py        # Code modification tests
```

### Testing Patterns

1. **Fixtures**: Reset coordinator state between tests
2. **Mocking**: External services (Modal, Aider, LLM)
3. **Integration**: End-to-end evolution scenarios
4. **Property Testing**: Sampling strategy invariants

## Performance Considerations

### Optimization Strategies

1. **Parallel Execution**: Future support for concurrent evaluations
2. **Caching**: LLM responses and execution results
3. **Early Stopping**: Convergence detection
4. **Resource Limits**: Configurable timeouts and memory

### Bottlenecks and Mitigations

1. **LLM Latency**: Batch suggestions, async calls
2. **Modal Startup**: Warm containers, connection pooling
3. **AST Parsing**: Incremental parsing, caching
4. **Database Growth**: Pruning strategies, external storage

## Extension Guide

### Adding New Sampling Strategies

```python
class MyStrategy(SamplingStrategy):
    def sample(self, programs: List[Program]) -> Program:
        # Custom selection logic
        return selected_program
```

### Custom Metrics Collection

```python
@evolve(goal="Optimize for custom metric")
def my_function():
    # Function logic
    pass

@main_entrypoint
def main():
    result = my_function()
    return {
        "fitness": result.accuracy,
        "latency": result.time,
        "memory": result.memory_usage
    }
```

### Alternative LLM Providers

Modify `dspy.py` to use different providers:
```python
# Replace OpenRouter with custom provider
dspy.settings.configure(
    lm=YourLLMProvider(api_key=config.api_key)
)
```

## Best Practices

### For Framework Users

1. **Clear Goals**: Specific, measurable optimization targets
2. **Comprehensive Metrics**: Include all relevant performance indicators
3. **Incremental Evolution**: Start with small iteration counts
4. **Version Control**: Commit before major evolution runs
5. **Resource Monitoring**: Watch Modal usage and costs

### For Framework Contributors

1. **Maintain Simplicity**: Resist adding complexity
2. **Document Changes**: Update both code and markdown docs
3. **Test Coverage**: Add tests for new features
4. **Backwards Compatibility**: Preserve decorator API
5. **Performance Impact**: Profile changes for overhead

## Future Architecture Considerations

### Planned Enhancements

1. **Persistent Database**: SQLite backend option
2. **Multi-Objective**: Pareto frontier tracking
3. **Distributed Evolution**: Multi-machine coordination
4. **Progressive Evaluation**: Cascade from simple to complex
5. **Evolution Analytics**: Visualization and insights

### API Stability Commitments

- Decorator signatures will remain stable
- Configuration additions will be backwards compatible
- New features will be opt-in
- Breaking changes only in major versions

## Security Considerations

### Code Execution Safety

1. **Sandboxing**: All evolution runs in Modal containers
2. **No Local Execution**: User code never runs locally
3. **Resource Limits**: Configurable CPU, memory, time limits
4. **API Key Protection**: Never logged or transmitted

### Best Practices

1. Review generated code before production use
2. Set appropriate resource limits
3. Use version control for code history
4. Monitor API usage and costs
5. Validate metrics collection

## Conclusion

The Evolv framework represents a careful balance between simplicity and capability, making evolutionary code improvement accessible while maintaining extensibility for advanced use cases. Its architecture enables rapid experimentation while providing clear paths for enhancement as needs grow.
