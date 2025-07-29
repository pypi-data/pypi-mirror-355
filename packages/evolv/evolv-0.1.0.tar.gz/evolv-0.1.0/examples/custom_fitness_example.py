# Import necessary libraries
import time

# import numpy as np # Not strictly needed for this version but often used
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from evolve import evolve, main_entrypoint  # Assuming these are in evolve.py

# Define the goal for the evolution - MODIFIED
UPDATED_CUSTOM_FITNESS_GOAL = """
Evolv a DecisionTreeClassifier on Iris to optimize a custom fitness
balancing accuracy and inference_time, while tracking individual metric components.
"""


def get_dataset():
    """
    Loads the Iris dataset and splits it into training and testing sets.

    Returns:
        tuple: X_train, X_test, y_train, y_test
    """
    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test


@evolve(goal=UPDATED_CUSTOM_FITNESS_GOAL, iterations=5, strategy="random")
class Model:
    """
    A DecisionTreeClassifier model for the Iris dataset.
    The @evolve decorator will attempt to modify the hyperparameters
    of this model.
    """

    def __init__(self, criterion="gini", splitter="best", max_depth=None, min_samples_split=2, min_samples_leaf=1):
        """
        Initializes the DecisionTreeClassifier model.
        Hyperparameters are defined here and can be targets for evolution.
        """
        self.criterion = criterion
        self.splitter = splitter
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf

        self.model = DecisionTreeClassifier(
            criterion=self.criterion,
            splitter=self.splitter,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            random_state=42,
        )
        print(
            f"Model initialized with params: criterion={self.criterion}, max_depth={self.max_depth}, min_samples_split={self.min_samples_split}, etc."
        )

    def fit(self, X, y):
        """Fits the model to the training data."""
        self.model.fit(X, y)

    def predict(self, X):
        """Makes predictions using the trained model."""
        return self.model.predict(X)

    def estimate_inference_time(self, X):
        """
        Simulates inference time.
        For simplicity, this returns a small fraction of the number of samples in X.
        A more realistic estimation would involve timing actual predictions.
        """
        # Simulate some base time + per-sample time
        # This is a placeholder; actual inference time depends on model complexity and data
        simulated_time = 0.001 + 0.00001 * len(X)
        return simulated_time


@main_entrypoint
def main():
    """
    Main function to run the classification model training and custom fitness evaluation.
    This function will be called by the Evolv library.
    """
    X_train, X_test, y_train, y_test = get_dataset()

    start_training_time = time.time()

    model_instance = Model()
    model_instance.fit(X_train, y_train)

    end_training_time = time.time()
    training_time = end_training_time - start_training_time

    y_pred = model_instance.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    inference_time = model_instance.estimate_inference_time(X_test)

    fitness_penalty_factor = 0.1
    custom_fitness = accuracy - (fitness_penalty_factor * inference_time)

    # This structured metrics dictionary is a conceptual step towards
    # AlphaEvolv's EvaluationScores, allowing for detailed tracking of
    # different objectives that contribute to the overall fitness.
    metrics = {
        "fitness": custom_fitness,  # The overall score the @evolve decorator will try to maximize
        "components": {  # Individual parts of the fitness, for detailed tracking
            "accuracy": accuracy,
            "inference_time": inference_time,
        },
        "training_time": training_time,
    }

    print(f"Metrics: {metrics}")
    return metrics


if __name__ == "__main__":
    print("Running custom fitness example directly...")
    main()
    print("Custom fitness example finished.")
