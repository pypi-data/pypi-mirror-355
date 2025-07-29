import numpy as np
from .baseRegressor import BaseRegressor

class PolynomialRegression(BaseRegressor):
    def __init__(self, n_degree=2, random_state=None):
        self.weights = np.array([])  # Initialize weights as a numpy array
        self.bias = 0
        self.n_degree = n_degree
        self.random_state = random_state
        self.loss_history = []
        self.weights_history = []

    def featureTransform(self, X):
        """
        Transform input X to polynomial features up to degree n_degree.
        Assumes X shape = (n_samples, 1)
        Returns X_poly with shape (n_samples, n_degree+1)
        """
        X = np.asarray(X)
        n_samples = X.shape[0]
        n_features = self.n_degree + 1

        X_poly = np.empty((n_samples, n_features))
        for power in range(n_features):
            X_poly[:, power] = X[:, 0] ** power

        return X_poly

    def calc_loss(self, X, y):
        yhat = X.dot(self.weights)
        return np.sum((yhat - y) ** 2) / len(y)

    def fit(self, X, y, epochs=100, lr=0.01):
        X_poly = self.featureTransform(X)
        self.weights = np.zeros(X_poly.shape[1])

        for _ in range(epochs):
            yhat = X_poly.dot(self.weights)
            error = yhat - y
            self.weights -= lr * X_poly.T.dot(error) / len(y)

            self.loss_history.append(self.calc_loss(X_poly, y))
            self.weights_history.append(self.weights.copy()) 


    def predict(self, X):
        X_poly = self.featureTransform(X)
        X_poly = np.asarray(X_poly)            # ensure numpy array
        weights = np.asarray(self.weights)    # ensure numpy array
        return X_poly.dot(weights)

