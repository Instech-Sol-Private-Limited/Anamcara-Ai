from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    max_features=3000
)

def rank_media(mood: str, tags: list[str], items: list[dict]):
    user_context = f"{mood} " + " ".join(tags)

    documents = [user_context]

    for item in items:
        text_parts = [
            item["title"],
            item.get("description", ""),
            item.get("artist", ""),
            " ".join(item.get("tags", []))
        ]
        documents.append(" ".join(text_parts))

    tfidf = vectorizer.fit_transform(documents)
    scores = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()

    ranked = []

    for item, score in zip(items, scores):
        ranked.append({
            **item,
            "score": round(float(score), 4)
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked