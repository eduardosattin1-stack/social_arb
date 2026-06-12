import re
from database import get_db_connection


def clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_posts_for_clustering(days: int = 14, min_length: int = 20) -> list[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, content, source, timestamp
        FROM posts
        WHERE timestamp > NOW() - interval '%s days'
          AND LENGTH(content) > %s
        ORDER BY timestamp DESC
    """, (days, min_length))
    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posts


def cluster_topics():
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import CountVectorizer

    print("Fetching posts for clustering...")
    posts = fetch_posts_for_clustering()
    if len(posts) < 20:
        print(f"Only {len(posts)} posts found, need at least 20 for clustering.")
        return []

    docs = [clean_html(p["content"]) for p in posts]
    doc_ids = [p["id"] for p in posts]

    print(f"Clustering {len(docs)} documents...")

    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    vectorizer = CountVectorizer(stop_words="english", min_df=2, max_df=0.95)

    topic_model = BERTopic(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer,
        min_topic_size=5,
        nr_topics="auto",
        verbose=True,
    )

    topics, probs = topic_model.fit_transform(docs)

    topic_info = topic_model.get_topic_info()
    results = []

    for _, row in topic_info.iterrows():
        topic_id = row["Topic"]
        if topic_id == -1:
            continue
        topic_words = topic_model.get_topic(topic_id)
        keywords = [w for w, _ in topic_words[:8]]
        count = row["Count"]

        topic_docs = [doc_ids[i] for i, t in enumerate(topics) if t == topic_id]

        results.append({
            "topic_id": topic_id,
            "keywords": keywords,
            "label": " ".join(keywords[:3]),
            "count": count,
            "post_ids": topic_docs[:20],
        })

    print(f"Found {len(results)} topics.")
    return results


def save_topics_to_db(topics: list[dict]):
    import json
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_clusters (
            id SERIAL PRIMARY KEY,
            topic_id INTEGER,
            label TEXT,
            keywords TEXT,
            count INTEGER,
            post_ids TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    cursor.execute("DELETE FROM topic_clusters")

    for t in topics:
        cursor.execute("""
            INSERT INTO topic_clusters (topic_id, label, keywords, count, post_ids)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            t["topic_id"],
            t["label"],
            ",".join(t["keywords"]),
            t["count"],
            json.dumps(t["post_ids"]),
        ))

    conn.commit()
    conn.close()
    print(f"Saved {len(topics)} topic clusters to database.")


if __name__ == "__main__":
    print("Starting BERTopic clustering...")
    topics = cluster_topics()
    if topics:
        save_topics_to_db(topics)
        for t in topics[:5]:
            print(f"  Topic {t['topic_id']}: {t['label']} ({t['count']} posts)")
