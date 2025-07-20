import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# Load model once
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load precomputed embeddings once (with error handling)
embeddings = {}
embeddings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'course_embeddings.pkl')
if os.path.exists(embeddings_file):
    with open(embeddings_file, "rb") as f:
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
    # Check if embeddings exist
    if not embeddings:
        return []  # No embeddings available yet
        
    # Compute the average embedding of completed courses
    completed_vectors = [embeddings[cid] for cid in completed_ids if cid in embeddings]
    if not completed_vectors:
        return []  # no completed embeddings
    
    avg_vector = np.mean(completed_vectors, axis=0)
    
    # Compute similarity to all candidates not in completed
    candidates = [cid for cid in all_course_ids if cid not in completed_ids]
    sims = []
    for cid in candidates:
        if cid in embeddings:  # Added safety check
            v = embeddings[cid]
            sim = np.dot(avg_vector, v) / (np.linalg.norm(avg_vector) * np.linalg.norm(v))
            sims.append((cid, sim))
    
    # Sort by similarity descending
    sims.sort(key=lambda x: x[1], reverse=True)
    
    top = [cid for cid, _ in sims[:top_n]]
    return top
