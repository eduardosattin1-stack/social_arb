from database import get_db_connection
from transformers import pipeline
import re

print("Loading multilingual NLP models...")
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
    top_k=None,
)
print("Models loaded.")

TOPIC_KEYWORDS = {
    "crypto": ["bitcoin", "ethereum", "crypto", "blockchain", "defi", "nft", "web3", "solana"],
    "ai_tech": ["ai", "artificial intelligence", "machine learning", "llm", "gpt", "chatgpt", "openai", "claude"],
    "gaming": ["gaming", "game", "playstation", "xbox", "nintendo", "steam", "esports"],
    "fintech": ["fintech", "payment", "banking", "neobank", "stripe", "paypal", "venmo"],
    "electric_vehicles": ["ev", "electric vehicle", "tesla", "rivian", "lucid", "charging"],
    "social_media": ["tiktok", "instagram", "twitter", "youtube", "spotify", "meta"],
    "healthcare": ["health", "medical", "pharma", "biotech", "fda", "drug"],
    "climate": ["climate", "sustainability", "green energy", "solar", "wind power", "carbon"],
    "retail": ["retail", "ecommerce", "amazon", "shopify", "consumer", "shopping"],
    "geopolitics": ["tariff", "sanctions", "trade war", "regulation", "policy", "election"],
}


def detect_language(text: str) -> str:
    sample = text[:500]
    non_ascii = sum(1 for c in sample if ord(c) > 127)
    ratio = non_ascii / max(len(sample), 1)
    if ratio < 0.05:
        return "en"
    elif ratio > 0.3:
        return "unknown"
    return "mixed"


def analyze_sentiment(text: str) -> float:
    try:
        result = sentiment_analyzer(text[:512])
        if isinstance(result, list) and len(result) > 0:
            scores = result[0] if isinstance(result[0], list) else result
            score_map = {}
            for item in scores:
                label = item["label"].lower()
                score_map[label] = item["score"]
            if "positive" in score_map and "negative" in score_map:
                return round(score_map["positive"] - score_map["negative"], 2)
            elif "positive" in score_map:
                return round(score_map["positive"], 2)
            elif "negative" in score_map:
                return round(-score_map["negative"], 2)
    except Exception as e:
        print(f"Sentiment error: {e}")
    return 0.0


def extract_region(text: str) -> str:
    text_lower = text.lower()
    europe = ["europe", "eu ", "london", "paris", "berlin", "uk", "france", "germany", "spain", "italy"]
    asia = ["asia", "china", "japan", "india", "tokyo", "beijing", "korea", "taiwan", "singapore"]
    americas = ["america", "us ", "usa", "canada", "brazil", "new york", "california", "mexico", "latam"]

    if any(kw in text_lower for kw in europe):
        return "Europe"
    elif any(kw in text_lower for kw in asia):
        return "Asia"
    elif any(kw in text_lower for kw in americas):
        return "Americas"
    return "Global"


def classify_topic(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[topic] = score
    if scores:
        return max(scores, key=scores.get)
    return None


def process_unprocessed_posts():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, content FROM posts WHERE sentiment IS NULL")
    posts = cursor.fetchall()

    processed_count = 0
    for post in posts:
        post_id = post["id"]
        content = post["content"]

        sentiment_score = analyze_sentiment(content)
        region = extract_region(content)
        topic = classify_topic(content)
        lang = detect_language(content)

        cursor.execute(
            "UPDATE posts SET sentiment = %s, region = %s, topic = %s, lang = %s WHERE id = %s",
            (sentiment_score, region, topic, lang, post_id)
        )
        processed_count += 1

    conn.close()
    if processed_count > 0:
        print(f"Processed {processed_count} posts through AI pipeline.")
    return processed_count


if __name__ == "__main__":
    print("Starting AI Processing Pipeline...")
    process_unprocessed_posts()
