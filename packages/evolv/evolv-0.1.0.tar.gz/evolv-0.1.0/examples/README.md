# Evolve Examples

This directory contains example scripts demonstrating various features of the Evolve framework.

## Examples Overview

### 🚀 **simple_example.py** (Start Here!)
The simplest possible example - evolves a DecisionTree classifier on the Iris dataset in just 30 lines of code.

```bash
# Run normally
python simple_example.py

# Run with evolution
EVOLVE=1 python simple_example.py
```

### 📊 **regression_example.py**
Demonstrates evolving a Ridge regression model on the California Housing dataset.
- Shows how to evolve regression models
- Includes data preprocessing steps
- Uses mean squared error as the fitness metric

### ⚙️ **custom_fitness_example.py**
Advanced example showing custom fitness functions that balance multiple objectives.
- Custom fitness combining accuracy and inference time
- Detailed metrics tracking
- Shows how to evolve class-based models

## Additional Resources

- [ADDITIONAL_EXAMPLES.md](./ADDITIONAL_EXAMPLES.md) - Advanced concepts and future directions
- [METRICS_BEST_PRACTICES.md](./METRICS_BEST_PRACTICES.md) - Guide for designing effective metrics

### Prerequisites

Before running these examples, ensure you have the necessary dependencies installed:
```bash
pip install scikit-learn numpy
```

You also need to ensure that the `evolve` library (from the `src` directory) is accessible in your `PYTHONPATH`. From the root of this repository, you can typically run the examples like this:

```bash
PYTHONPATH=$PYTHONPATH:$(pwd)/src python examples/your_example_name.py
```

### Available Examples

1.  **`simple_example.py`** (Start Here!):
    *   **Description**: The simplest possible example - evolves a DecisionTree classifier on the Iris dataset in just 30 lines of code.
    *   **To Run**:
        ```bash
        PYTHONPATH=$PYTHONPATH:$(pwd)/src python examples/simple_example.py
        ```

2.  **`breast_cancer_example.py`**:
    *   **Description**: Classification example using the Breast Cancer dataset with LogisticRegression. Shows a straightforward binary classification task with feature scaling.
    *   **To Run**:
        ```bash
        PYTHONPATH=$PYTHONPATH:$(pwd)/src python examples/breast_cancer_example.py
        ```

3.  **`regression_example.py`**:
    *   **Description**: This example demonstrates how to use the Evolve library for a regression task. It uses the California Housing dataset from `sklearn.datasets` and evolves a `RandomForestRegressor` to minimize Mean SquaredError.
    *   **To Run**:
        ```bash
        PYTHONPATH=$PYTHONPATH:$(pwd)/src python examples/regression_example.py
        ```

4.  **`custom_fitness_example.py`**:
    *   **Description**: This example showcases the use of a custom fitness function. It uses the Iris dataset for a classification task and evolves a `DecisionTreeClassifier`. The fitness function is a custom one that balances model accuracy with a simulated inference time.
    *   **To Run**:
        ```bash
        PYTHONPATH=$PYTHONPATH:$(pwd)/src python examples/custom_fitness_example.py
        ```

5.  **`map_elites_example.py`**:
    *   **Description**: Demonstrates the MAP-Elites quality-diversity algorithm for evolving diverse high-performing solutions. Shows how to define feature dimensions and maintain an archive of solutions.
    *   **To Run**:
        ```bash
        PYTHONPATH=$PYTHONPATH:$(pwd)/src python examples/map_elites_example.py
        ```

6.  **`island_evolution_example.py`**:
    *   **Description**: Shows island-based evolution with multiple populations evolving in parallel. Demonstrates migration between islands and population diversity.
    *   **To Run**:
        ```bash
        PYTHONPATH=$PYTHONPATH:$(pwd)/src python examples/island_evolution_example.py
        ```

7.  **`heterogeneous_islands_example.py`**:
    *   **Description**: Advanced island evolution with different LLM models and mutation rates per island. Showcases heterogeneous population strategies.
    *   **To Run**:
        ```bash
        PYTHONPATH=$PYTHONPATH:$(pwd)/src python examples/heterogeneous_islands_example.py
        ```
