import numpy as np
from .baseRegressor import BaseRegressor

class L1Regressor(BaseRegressor):
    def __init__(self, lam=1.0, random_state=42) -> None:
        self.weights = np.array([])  # Initialize weights as a numpy array
        self.bias = 0
        self.lam = lam
        self.random_state = random_state
        self.loss_history = []
        self.weights_history = []
        self.bias_history = []

    def calc_loss(self, X, y):
        n = y.shape[0]
        yhat = X.dot(self.weights) + self.bias
        loss = np.sum((yhat - y) ** 2)/n + self.lam * np.sum(np.abs(self.weights))
        return loss
    

    def fit(self, X, y, epochs=100, lr=0.01):
        n = len(y)

        randomGen = np.random.RandomState(self.random_state)
        self.weights = randomGen.normal(loc=0.0, scale=0.01, size=X.shape[1])
        
        for _ in range(epochs):
            yhat = X.dot(self.weights) + self.bias
            dl_dw = X.T.dot(yhat - y) / n + self.lam * np.sign(self.weights)
            dl_db = np.sum(yhat - y) / n


            self.weights -= lr * dl_dw
            self.bias -= lr * dl_db

            loss = self.calc_loss(X, y)
            self.loss_history.append(loss)
            self.weights_history.append(self.weights.copy())
            self.bias_history.append(self.bias)

    def predict(self, X):
        return X.dot(self.weights) + self.bias

