# Best Practices for Defining Metrics in Evolve Examples

Effective metric design is paramount when using evolutionary algorithms, including this `evolve` library. The metrics you define directly guide the evolutionary process. Poorly designed metrics can lead to suboptimal results, exploitation of loopholes, or stagnation. This guide draws inspiration from advanced systems like Google DeepMind's AlphaEvolve to help you define robust and meaningful metrics for your `@evolve` decorated models.

## 1. Core Principles for Metric Design

*   **Clarity and Unambiguity**: Your metric should have a clear, precise definition. Avoid vague or subjective measures that can be interpreted in multiple ways.
*   **Measurability**: The metric must be quantifiable and consistently calculable from the output or behavior of your evolved program/model.
*   **Alignment with True Goals**: Ensure your metric accurately reflects the actual desired outcome. It's easy to define a proxy metric that, when optimized, doesn't actually achieve the real-world goal.
*   **Sensitivity to Change**: The metric should be sensitive enough to reflect meaningful improvements in your solution, but not so noisy that it obscures real progress.
*   **Computational Feasibility**: Calculating the metric should be computationally tractable within the timeframe of your evolution iterations. Overly complex metrics can significantly slow down the process.

## 2. Drawing Inspiration from AlphaEvolve's Metrics Architecture

AlphaEvolve employs a sophisticated, multi-dimensional evaluation framework. While our current `evolve` library is simpler, we can adopt the underlying principles:

### a. Multi-Dimensional Thinking (`EvaluationScores` Concept)
AlphaEvolve's `EvaluationScores` often include:
    *   **Custom Metrics**: Problem-specific performance measures (e.g., accuracy, MSE, task completion rate). This is your primary fitness driver.
    *   **Length Scores**: Often negative to favor shorter, simpler code. In our context, this could translate to preferring models with fewer parameters if that's a desirable trait, or simpler generated functions.
    *   **Simplicity Scores**: Inverse complexity ratios. Could be approximated by analyzing the complexity of generated model configurations or code.
    *   **Evaluation Latency**: Time taken to evaluate the solution.

    **For `@evolve`**: When your `main()` function (decorated with `@main_entrypoint`) returns the `metrics` dictionary, consider including multiple components beyond just the primary `fitness` value. Our `custom_fitness_example.py` shows returning:
    ```python
    metrics = {
        "fitness": custom_fitness,
        "components": {
            "accuracy": accuracy,
            "inference_time": inference_time
        },
        # Potentially add other components:
        # "model_size": get_model_size(model),
        # "evaluation_latency": time.time() - eval_start_time,
    }
    ```
    This allows for richer data logging and post-hoc analysis, even if only a single `fitness` value currently drives the evolution.

### b. Defining Primary vs. Secondary Metrics
Clearly distinguish the primary metric that the `@evolve` decorator's `fitness` field should optimize from other secondary metrics that are useful for logging and analysis.

### c. Handling Optimization Direction (Minimize/Maximize)
AlphaEvolve systems can be configured for minimization or maximization. The `@evolve` decorator implicitly maximizes the `fitness` value.
    *   **If your goal is to minimize a metric** (e.g., Mean Squared Error, latency), you must invert it before assigning it to `fitness`. For example: `metrics["fitness"] = -mse`.

### d. Robust Error Handling in Metric Calculation
AlphaEvolve assigns extreme penalty values for programs that fail evaluation.
    *   **For `@evolve`**: Your `main()` function should gracefully handle errors during model training or prediction. If an error occurs that makes a candidate solution invalid:
        *   Return a very poor fitness value (e.g., `-float('inf')` if maximizing, or `float('inf')` if your raw score is minimized then negated).
        *   Optionally, include an error flag or message in your returned metrics dictionary for logging:
          ```python
          try:
              # ... train and predict ...
              mse = mean_squared_error(y_test, y_pred)
              metrics["fitness"] = -mse
          except Exception as e:
              metrics["fitness"] = -float('inf')
              metrics["error"] = str(e)
          return metrics
          ```

## 3. Strategies for Custom Fitness Functions

### a. Combining Multiple Objectives
If your `fitness` needs to balance competing objectives (e.g., accuracy vs. speed, performance vs. size):
    *   **Weighted Sums**: This is the simplest approach (e.g., `fitness = w1*accuracy - w2*inference_time`). Choosing appropriate weights (`w1`, `w2`) can be challenging and problem-dependent.
    *   **Normalization**: When combining metrics with different scales, normalize them (e.g., to a 0-1 range) before combining.
    *   **Lexicographical Ordering (Conceptual)**: Prioritize objectives. Optimize for the first; among those with similar primary scores, optimize for the second, etc. This is harder to implement directly in a single fitness value but can be a design principle.
    *   **Pareto Fronts (Advanced Concept)**: True multi-objective optimization often involves finding a set of solutions representing different trade-offs (a Pareto front). While the current `evolve` library might not directly support evolving Pareto fronts, designing metrics that explore different aspects of this front can be beneficial. The `ADDITIONAL_EXAMPLES.md` discusses this further.

## 4. Avoiding Common Pitfalls

*   **"Gaming" the Metric**: Ensure your metric doesn't have loopholes that allow the evolutionary process to find trivial or incorrect solutions that still score well.
    *   *Example*: If optimizing code speed, ensure correctness is also a primary component of fitness. Otherwise, it might evolve an empty function that runs fast but does nothing.
*   **Overly Complex Fitness Functions**: While comprehensive, a fitness function that is too complex can be hard to debug, slow to compute, and may obscure the evolutionary search landscape. Start simple and add complexity iteratively.
*   **Ignoring Qualitative Aspects**: Some desirable traits (e.g., code readability, maintainability, elegance of a solution) are hard to quantify. AlphaEvolve uses LLM-generated feedback for this. While this library doesn't have that built-in, be aware of this limitation. Future extensions might explore this.

## 5. Iterative Refinement

Metric design is often an iterative process. Start with a reasonable metric, run some evolutionary experiments, analyze the results, and then refine your metric based on the observed behavior and outcomes. Don't be afraid to adjust your metrics as you gain more insight into your problem domain and how the `evolve` library interacts with it.

---

By considering these best practices, you can create more effective and insightful examples, and better guide the `evolve` library towards discovering genuinely innovative solutions.
