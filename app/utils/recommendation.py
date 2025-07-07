import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# Load model once
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load precomputed embeddings once
with open("course_embeddings.pkl", "rb") as f:
    embeddings = pickle.load(f)

def recommend_courses(completed_ids, all_course_ids, top_n=5):
    """
    Args:
        completed_ids: list of completed course IDs
        all_course_ids: list of all candidate course IDs
        top_n: how many recommendations to return
    Returns:
        List of course IDs sorted by similarity
    """
    # Compute the average embedding of completed courses
    completed_vectors = [embeddings[cid] for cid in completed_ids if cid in embeddings]
    if not completed_vectors:
        return []  # no completed embeddings
    
    avg_vector = np.mean(completed_vectors, axis=0)
    
    # Compute similarity to all candidates not in completed
    candidates = [cid for cid in all_course_ids if cid not in completed_ids]
    sims = []
    for cid in candidates:
        v = embeddings[cid]
        sim = np.dot(avg_vector, v) / (np.linalg.norm(avg_vector) * np.linalg.norm(v))
        sims.append((cid, sim))
    
    # Sort by similarity descending
    sims.sort(key=lambda x: x[1], reverse=True)
    
    top = [cid for cid, _ in sims[:top_n]]
    return top
