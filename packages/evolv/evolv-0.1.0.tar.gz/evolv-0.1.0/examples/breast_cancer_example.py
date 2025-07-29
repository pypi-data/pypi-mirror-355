"""Breast Cancer Classification Example

This example shows how Evolv can automatically improve a simple
logistic regression model to achieve better accuracy on the
breast cancer dataset.

Typical improvement: 95.6% → 99.1% accuracy (+3.7%)
"""

import time

from sklearn.datasets import load_breast_cancer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from evolve import evolve, main_entrypoint


def get_dataset():
    data = load_breast_cancer()
    X, y = data.data, data.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test


@evolve(
    goal="Improve accuracy by optimizing feature processing and model selection",
    iterations=3,
    strategy="linear",
)
class Model:
    def __init__(self):
        from sklearn.linear_model import LogisticRegression

        self.model = LogisticRegression(max_iter=10000)

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)


@main_entrypoint
def main():
    X_train, X_test, y_train, y_test = get_dataset()
    start_time = time.time()
    model = Model()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    end_time = time.time()
    accuracy = accuracy_score(y_test, y_pred)
    metrics = {
        "fitness": accuracy,
        "time": end_time - start_time,
    }
    print(f"🎯 Accuracy: {accuracy:.1%} | Time: {end_time - start_time:.3f}s")
    return metrics


if __name__ == "__main__":
    main()
