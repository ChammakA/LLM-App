import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_relevant_notes(query, k=3, threshold=0.1):
    """Return top-k previous notes similar to the query"""
    try:
        with open("data/patch_notes.json", "r") as f:
            PATCH_NOTES = json.load(f)
    except FileNotFoundError:
        PATCH_NOTES = []

    if not PATCH_NOTES:
        return []

    vectorizer = TfidfVectorizer()
    NOTE_VECTORS = vectorizer.fit_transform(PATCH_NOTES)

    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, NOTE_VECTORS)[0]
    top_idx = sims.argsort()[-k:][::-1]

    return [PATCH_NOTES[i] for i in top_idx if sims[i] > threshold]