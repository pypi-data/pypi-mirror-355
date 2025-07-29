import numpy as np

class PCA:
    def __init__(self, n_components):
        self.n_components = n_components
        self.components = []
        self.mean = None

    def fit(self, X):
        self.mean = np.mean(X, axis=0)
        X = X - self.mean
        cov = np.cov(X.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov)
        idxs = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idxs]
        eigenvectors = eigenvectors[:, idxs]  # reorder columns
        self.components = eigenvectors[:, :self.n_components]  # keep as columns

    def transform(self, X):
        X = X - self.mean
        return np.dot(X, self.components)  # no need to transpose
