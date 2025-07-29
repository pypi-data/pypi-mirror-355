import numpy as np
import matplotlib.pyplot as plt
from small_neural_net.mnl import MultiNeuronLinearGD

np.random.seed(42)

# Parameters
SAMPLES = 10
FEATURES = 6
EPOCHS = 100
LR = 0.0001

# Generate random input and output data
X = np.random.randint(1, 101, size=(SAMPLES, FEATURES))
y = np.random.randint(1, 101, size=(SAMPLES, 1))

# Initialize and train the model
model = MultiNeuronLinearGD(samples=SAMPLES, features=FEATURES, lr=LR, epochs=EPOCHS)
model.fit(X, y)

# Predictions
y_final = model.predict(X)

print("Input (X):\n", X)
print("\nWeights:\n", model.weights)
print("\nTarget (y):\n", y.ravel())
print("Predictions:\n", y_final.ravel())
print("\nFinal Loss:", model.loss_history[-1])

plt.plot(range(EPOCHS), model.loss_history, label="Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Loss over Epochs - MultiNeuronLinearGD")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
