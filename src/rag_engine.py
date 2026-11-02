from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def retrieve(query, chunks, active_ids=None, top_k=4):
    candidates = [c for c in chunks if active_ids is None or c["doc_id"] in active_ids]
    if not candidates:
        return []
    texts = [c["text"] for c in candidates]
    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=12000)
        matrix = vectorizer.fit_transform(texts + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    except ValueError:
        return []
    ranked = sorted(zip(scores, candidates), key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in ranked[:top_k] if score > 0]

def build_context(matches, max_chars=5000):
    sections, used = [], 0
    for item in matches:
        label = f"[Source: {item['filename']} — {item['source']}]"
        block = f"{label}\n{item['text']}"
        if used + len(block) > max_chars:
            block = block[:max(0, max_chars-used)]
        if block:
            sections.append(block)
            used += len(block)
        if used >= max_chars:
            break
    return "\n\n".join(sections)
