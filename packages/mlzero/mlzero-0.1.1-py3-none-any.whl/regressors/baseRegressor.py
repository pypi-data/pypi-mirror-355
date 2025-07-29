from abc import ABC, abstractmethod
import numpy as np

class BaseRegressor(ABC):
    @abstractmethod
    def fit(self, X, y):
        """Fit the model to training data."""
        pass

    @abstractmethod
    def predict(self, X):
        """Make predictions using the trained model."""
        pass

    def score(self, X, y):
        """Default implementation of R^2 score."""
        y_pred = self.predict(X)
        u = np.sum((y - y_pred) ** 2)
        v = np.sum((y - np.mean(y)) ** 2)
        return 1 - u/v
