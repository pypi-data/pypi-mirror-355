import numpy as np
from .baseRegressor import BaseRegressor
class LinearRegressionCF(BaseRegressor):
    def __init__(self):
        self.theta = None  # will contain weights and bias

    def fit(self, X, y):
        # Add a column of ones to X for bias term
        X_b = np.c_[np.ones((X.shape[0], 1)), X]  # shape (n_samples, n_features + 1)

        # Compute theta using normal equation
        self.theta = np.linalg.inv(X_b.T.dot(X_b)).dot(X_b.T).dot(y)

    def predict(self, X):
        X_b = np.c_[np.ones((X.shape[0], 1)), X]
        return X_b.dot(self.theta)
    


