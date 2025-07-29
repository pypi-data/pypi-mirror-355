#!/usr/bin/env python
"""Demonstration of Enhanced LLM Prompting with Inspiration Programs.

This example shows how the evolution process uses high-scoring programs
as inspiration to guide the improvement of new variants.

Run with: EVOLVE=1 python examples/inspiration_demo.py
"""

import logging
import time

from sklearn.datasets import load_wine
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from evolve import evolve, main_entrypoint

# Enable detailed logging to see inspiration programs in action
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_dataset():
    """Load and split the wine dataset."""
    data = load_wine()
    X, y = data.data, data.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test


@evolve(
    goal="Improve classification accuracy by learning from high-scoring variants. Consider ensemble methods, hyperparameter tuning, and feature engineering.",
    iterations=3,
    strategy="tournament",  # Tournament strategy will select diverse parents
)
class WineClassifier:
    """A classifier for the wine dataset that can evolve."""

    def __init__(self):
        # Start with a basic RandomForest
        self.model = RandomForestClassifier(
            n_estimators=10,  # Small number to leave room for improvement
            random_state=42,
        )

    def fit(self, X, y):
        """Train the model."""
        self.model.fit(X, y)

    def predict(self, X):
        """Make predictions."""
        return self.model.predict(X)


@main_entrypoint
def main():
    """Main entry point that evaluates the classifier."""
    X_train, X_test, y_train, y_test = get_dataset()

    start_time = time.time()

    # Create and train classifier
    classifier = WineClassifier()
    classifier.fit(X_train, y_train)

    # Make predictions
    y_pred = classifier.predict(X_test)

    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    elapsed_time = time.time() - start_time

    metrics = {
        "fitness": accuracy,
        "time": elapsed_time,
    }

    print(f"Accuracy: {accuracy:.4f}, Time: {elapsed_time:.4f}s")
    return metrics


if __name__ == "__main__":
    main()
