# Import necessary libraries
import time

from sklearn.datasets import fetch_california_housing
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

from evolve import evolve, main_entrypoint  # Assuming these are in evolve.py

# Define the goal for the evolution
REGRESSION_GOAL = """
Improve the Mean Squared Error of a RandomForestRegressor model
on the California Housing dataset by evolving its hyperparameters.
The model should predict housing prices accurately.
"""


def get_dataset():
    """
    Loads the California Housing dataset and splits it into training and testing sets.

    Returns:
        tuple: X_train, X_test, y_train, y_test
    """
    housing = fetch_california_housing()
    X, y = housing.data, housing.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test


@evolve(goal=REGRESSION_GOAL, iterations=5, strategy="random")
class Model:
    """
    A RandomForestRegressor model for the California Housing dataset.
    The @evolve decorator will attempt to modify the hyperparameters
    of this model (if they are exposed as attributes that can be modified,
    or if the evolution strategy involves re-instantiating the model with new params).
    For this example, we assume the decorator might modify `self.model`'s params
    or the class itself if the Evolv library supports such mechanisms.
    """

    def __init__(self, n_estimators=100, max_depth=None, min_samples_split=2, min_samples_leaf=1):
        """
        Initializes the RandomForestRegressor model.
        Hyperparameters are defined here and can be targets for evolution.
        """
        # These parameters can be evolved by the Evolv library
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf

        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            random_state=42,
        )
        print(
            f"Model initialized with params: n_estimators={self.n_estimators}, max_depth={self.max_depth}, min_samples_split={self.min_samples_split}, min_samples_leaf={self.min_samples_leaf}"
        )

    def fit(self, X, y):
        """Fits the model to the training data."""
        self.model.fit(X, y)

    def predict(self, X):
        """Makes predictions using the trained model."""
        return self.model.predict(X)


@main_entrypoint
def main():
    """
    Main function to run the regression model training and evaluation.
    This function will be called by the Evolv library.
    """
    X_train, X_test, y_train, y_test = get_dataset()

    start_time = time.time()

    # Create an instance of the Model.
    # If Evolv is modifying class attributes or re-instantiating,
    # the parameters used here might be suggestions from the evolution process.
    model_instance = Model()

    # Fit the model
    model_instance.fit(X_train, y_train)

    # Make predictions
    y_pred = model_instance.predict(X_test)

    end_time = time.time()

    # Calculate Mean Squared Error
    mse = mean_squared_error(y_test, y_pred)

    # Define metrics for Evolv. 'fitness' is the primary metric to optimize.
    # Lower MSE is better, so we negate it for maximization.
    metrics = {
        "fitness": -mse,  # Negative MSE because evolve maximizes
        "mse": mse,  # Store actual MSE for reference
        "time": end_time - start_time,
    }

    print(f"Metrics: {metrics}")
    return metrics


if __name__ == "__main__":
    # This allows direct execution of the script for testing/debugging.
    # The Evolv library would typically call the `main` function directly.
    print("Running regression example directly...")
    main()
    print("Regression example finished.")
