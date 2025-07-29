# MAP-Elites Strategy Guide

## Overview

MAP-Elites (Multidimensional Archive of Phenotypic Elites) is a quality-diversity algorithm that maintains a diverse collection of high-performing solutions across user-defined behavioral dimensions. Unlike traditional optimization that seeks a single best solution, MAP-Elites illuminates the entire solution space.

## Key Concepts

### Behavior Space
- **Features**: Measurable characteristics of your code (speed, complexity, memory usage)
- **Grid**: Discretized feature space divided into cells
- **Elites**: Best-performing solution for each cell

### Benefits
1. **Diversity**: Prevents premature convergence
2. **Trade-offs**: Discovers solutions with different characteristics
3. **Stepping Stones**: Uses diverse solutions to reach breakthroughs
4. **Robustness**: Maintains multiple good solutions

## Basic Usage

```python
from evolve import evolve, main_entrypoint

@evolve(
    goal="Create diverse high-performing solutions",
    strategy="map_elites",
    strategy_config={
        "features": [
            ("speed", (0.1, 10.0), 20),      # Feature name, (min, max), bins
            ("memory_mb", (1, 100), 20)      # 20x20 = 400 cells total
        ],
        "selection": "uniform"               # or "curiosity"
    }
)
def my_algorithm(data):
    # Your implementation
    pass
```

## Feature Configuration

### Built-in Features

| Feature | Description | Typical Range |
|---------|-------------|---------------|
| `execution_time` | Runtime in seconds | (0.001, 10.0) |
| `memory_usage` | Memory in MB | (1, 1000) |
| `code_length` | Characters in code | (100, 10000) |
| `num_lines` | Lines of code | (10, 1000) |
| `complexity` | Cyclomatic complexity | (1, 50) |
| `num_functions` | Function definitions | (0, 20) |
| `max_nesting` | Maximum nesting depth | (0, 10) |
| `num_loops` | Number of loops | (0, 20) |

### Custom Features

```python
def count_list_comprehensions(program):
    """Count list comprehensions in the code."""
    import ast
    tree = ast.parse(program.evolve_code)
    return float(sum(1 for node in ast.walk(tree)
                    if isinstance(node, ast.ListComp)))

@evolve(
    goal="Optimize with different coding styles",
    strategy="map_elites",
    strategy_config={
        "features": [
            ("performance", (0.0, 1.0), 10),
            ("list_comps", (0, 10), 10)
        ],
        "custom_extractors": {
            "list_comps": count_list_comprehensions
        }
    }
)
```

## Selection Methods

### Uniform Selection
- Samples randomly from occupied cells
- Good for broad exploration
- Default option

### Curiosity Selection
- Biases selection toward isolated solutions
- Explores under-represented regions
- Better for discovering novel approaches

```python
strategy_config={
    "features": [...],
    "selection": "curiosity"  # Explore sparse regions
}
```

## Advanced Examples

### Multi-Objective Optimization
```python
@evolve(
    goal="Balance accuracy, speed, and code simplicity",
    strategy="map_elites",
    strategy_config={
        "features": [
            ("accuracy", (0.5, 1.0), 25),
            ("execution_time", (0.001, 1.0), 20),
            ("complexity", (1, 30), 15)
        ],
        "selection": "curiosity"
    },
    iterations=10  # More iterations for 3D exploration
)
def ml_classifier(X, y):
    # Classifier implementation
    pass
```

### Algorithm Evolution
```python
@evolve(
    goal="Discover diverse pathfinding algorithms",
    strategy="map_elites",
    strategy_config={
        "features": [
            ("path_length", (1.0, 2.0), 20),  # Optimality ratio
            ("nodes_explored", (10, 1000), 20),
            ("memory_usage", (1, 100), 10)
        ]
    }
)
def pathfind(grid, start, goal):
    # A* initially, may evolve to BFS, DFS, JPS, etc.
    pass
```

## Metrics and Monitoring

MAP-Elites provides rich metrics:

```python
# In your main function, metrics are automatically tracked
metrics = {
    "fitness": 0.95,           # Primary optimization metric
    "execution_time": 0.023,   # Used for behavior characterization
    "memory_bytes": 1048576,   # Converted to memory_usage feature
    "accuracy": 0.87           # Can be both fitness and feature
}
```

Archive metrics include:
- **Coverage**: Percentage of cells occupied
- **Improvements**: Number of elite replacements
- **Best per dimension**: Top fitness for each feature

## Best Practices

### 1. Feature Selection
- Choose 2-3 orthogonal features
- Ensure features capture meaningful variation
- Use appropriate ranges and bin counts

### 2. Grid Resolution
- 10-25 bins per dimension is typical
- Total cells = product of all bin counts
- Balance resolution vs. computation

### 3. Custom Extractors
- Make extractors robust to parsing errors
- Return sensible defaults for edge cases
- Keep extraction fast

### 4. Fitness Design
- Primary metric should reflect overall quality
- Features should capture behavioral diversity
- Don't use fitness as a feature

## Troubleshooting

### Low Coverage
- Increase iterations
- Use curiosity selection
- Check if features are too restrictive

### No Improvement
- Verify features are meaningful
- Check that LLM understands the goal
- Ensure fitness metric is well-defined

### Slow Convergence
- Reduce grid resolution
- Focus on 2 key features
- Increase parallel variants

## Visualization

MAP-Elites data is perfect for visualization:

```python
# Access archive data
strategy = StrategyFactory.create("map_elites")
viz_data = strategy.get_archive_visualization()

# Contains:
# - viz_data["grid"]: 2D/3D fitness values
# - viz_data["coverage_history"]: Coverage over time
# - viz_data["dimensions"]: Feature specifications
# - viz_data["events"]: Recent improvements
```

## When to Use MAP-Elites

✅ **Good for:**
- Multi-objective problems
- Exploring trade-offs
- Discovering diverse solutions
- Understanding solution space
- Robust optimization

❌ **Not ideal for:**
- Single-objective optimization
- Known optimal solutions
- Very high-dimensional spaces
- Time-critical optimization

## Integration with Evolve

MAP-Elites integrates seamlessly:
- Works with all executors (Modal, Local)
- Compatible with async architecture
- Supports all LLM providers
- Combines with other features

Remember: MAP-Elites is about discovering diversity, not just optimizing fitness!
