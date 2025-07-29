"""
Minimal example showing how to use Evolv to optimize a function.
This example evolves a simple classifier to maximize accuracy.
"""

from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from evolve import evolve, main_entrypoint


def get_dataset():
    """Load and split the Iris dataset. This is outside the evolve decorator for security."""
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test


@evolve(goal="Maximize accuracy of DecisionTree on Iris dataset by evolving hyperparameters")
def create_and_train_model(X_train, y_train, max_depth=3, min_samples_split=2):
    """Create and train a DecisionTree model. Only the model logic can be evolved."""
    # Train model with evolving parameters
    clf = DecisionTreeClassifier(max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
    clf.fit(X_train, y_train)
    return clf


@main_entrypoint
def main():
    # Load data outside of evolved function for security
    X_train, X_test, y_train, y_test = get_dataset()

    # Train model using evolved function
    model = create_and_train_model(X_train, y_train)

    # Evaluate model outside of evolved function
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Return metrics
    metrics = {"fitness": accuracy}
    print(f"Accuracy: {accuracy:.4f}")
    return metrics


if __name__ == "__main__":
    # Run with: EVOLVE=1 python simple_example.py
    print("Running simple example...")
    result = main()
    print(f"Result: {result}")
