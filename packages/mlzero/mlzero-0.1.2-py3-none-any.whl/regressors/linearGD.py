import numpy as np
from .baseRegressor import BaseRegressor
class LinearRegressionGD(BaseRegressor):
    def __init__(self):
        self.weights = np.array([])  # Initialize weights as a numpy array
        self.bias = 0
        self.loss_history = []
        self.weight_history = []
        self.bias_history = []

    def calc_loss(self, x, y):
        yhat = x * self.weights + self.bias
        loss = np.sum((yhat - y) ** 2) / (2 * len(y))
        return loss

    def fit(self, x, y, epochs=100, lr=0.01):
        n = len(x)
        for i in range(epochs):
            yhat = x * self.weights + self.bias
            dldw = np.sum((yhat - y) * x) / n
            dldb = np.sum((yhat - y)) / n

            self.weights -= lr * dldw
            self.bias -= lr * dldb

            loss = self.calc_loss(x, y)
            self.loss_history.append(loss) 
            self.weight_history.append(self.weights)
            self.bias_history.append(self.bias)

    def predict(self, x):
        return x * self.weights + self.bias

