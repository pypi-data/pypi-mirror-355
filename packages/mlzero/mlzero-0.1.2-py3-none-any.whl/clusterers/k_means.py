import numpy as np

class Kmeans:
    def __init__(self, n_clusters=2, max_iterations=100):
        self.n_clusters = n_clusters
        self.max_iterations = max_iterations
        self.centroids = None
        self.centroid_history=[]

    @staticmethod
    def euclideanDist(x1, x2):
        return np.sqrt(np.sum((x1 - x2) ** 2))
    

    def fit_predict(self, X, iterations=200):
        self.set_initial(X)
        old_centroids = self.centroids
        for _ in range(iterations):
            X_color = self.assign_centroids(X)
            new_centroids = self.move_centroids(X, X_color)

            if old_centroids is not None and np.allclose(old_centroids, new_centroids):
                self.centroids = new_centroids
                self.centroid_history.append(new_centroids)
                break

            old_centroids = new_centroids
            self.centroids = new_centroids
            self.centroid_history.append(new_centroids)

        return X_color, self.centroids

    def set_initial(self, X):
        np.random.seed(42)
        random_indices = np.random.choice(len(X), size=self.n_clusters, replace=False)
        self.centroids = X[random_indices]

    def assign_centroids(self, X):
        X_color = []
        if self.centroids is None:
            raise ValueError("Centroids have not been initialized. Call set_initial first.")
        for row in X:
            distances = []
            for centroid in self.centroids:
                distance = self.euclideanDist(row, centroid)
                distances.append(distance)
            X_color.append(np.argmin(distances))
        return np.array(X_color)

    def move_centroids(self, X, X_color):
        new_centroids = []
        for i in range(self.n_clusters):
            Xdash = X[np.array(X_color) == i]
            new_centroids.append(np.mean(Xdash, axis=0))
        return np.array(new_centroids)
    
    def history(self):
        return self.centroid_history
