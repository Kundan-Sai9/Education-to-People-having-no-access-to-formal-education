
from sklearn.neighbors import NearestNeighbors
import numpy as np
import joblib

# Sample fake data
X = np.array([
    [1, 0, 1],
    [0, 1, 0],
    [1, 1, 0],
])

model = NearestNeighbors(n_neighbors=2)
model.fit(X)

joblib.dump(model, 'recommendation_model.pkl')
print("Model trained and saved.")
