import numpy as np

class MultiNeuronLinearGD:
    def __init__(self, samples, features, lr=0.0001, epochs=100, random_state=42):
        np.random.seed(random_state)
        self.samples = samples
        self.features = features
        self.lr = lr
        self.epochs = epochs
        self.weights = np.random.randint(0, 10, size=(features, features)).astype(float)
        self.bias = 0.0
        self.loss_history = []

    def forward(self, X):
        """
        Custom forward pass for multi-neuron linear model.
        Each row in X (input sample) is multiplied with weights[i % features]
        """
        y_pred = []
        for i in range(self.samples):
            weighted_sum = np.dot(X[i], self.weights[i % self.features]) + self.bias
            y_pred.append(weighted_sum)
        return np.array(y_pred).reshape(-1, 1)

    def compute_loss(self, y_pred, y_true):
        return np.mean((y_pred - y_true) ** 2) / 2

    def fit(self, X, y):
        for epoch in range(self.epochs):
            y_pred = self.forward(X)
            error = y_pred - y
            dW = np.zeros_like(self.weights)
            dB = np.sum(error)
            for i in range(self.samples):
                dW[i % self.features] += error[i] * X[i]
            self.weights -= self.lr * dW / self.samples
            self.bias -= self.lr * dB / self.samples
            loss = self.compute_loss(y_pred, y)
            self.loss_history.append(loss)

    def predict(self, X):
        return self.forward(X)
