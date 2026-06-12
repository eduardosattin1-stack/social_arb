import os
from database import get_db_connection


def resolve_unknown_entities():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT em.matched_text
        FROM entity_mentions em
        WHERE em.entity_id IS NULL
           OR em.matched_text NOT IN (SELECT name FROM entities)
        LIMIT 50
    """)
    unknown_texts = [row["matched_text"] for row in cursor.fetchall()]

    if not unknown_texts:
        print("No unknown entities to resolve.")
        conn.close()
        return []

    print(f"Found {len(unknown_texts)} unknown entities to resolve.")

    from transformers import pipeline

    print("Loading zero-shot classifier...")
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    ENTITY_TYPES = ["company", "product", "brand", "person", "theme", "technology"]
    TICKER_CANDIDATES = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC",
        "NFLX", "DIS", "CRM", "ADBE", "PYPL", "SQ", "SHOP", "SE", "MELI",
        "NKE", "LULU", "SBUX", "MCD", "TGT", "WMT", "COST", "HD", "LOW",
        "JPM", "BAC", "GS", "MS", "V", "MA", "AXP",
        "PFE", "JNJ", "UNH", "ABBV", "MRK", "LLY", "NVO",
        "XOM", "CVX", "COP", "SLB",
        "NEE", "ENPH", "SEDG", "FSLR",
        "PLTR", "CRWD", "ZS", "NET", "DDOG", "MDB", "SNOW",
        "COIN", "MSTR", "HOOD",
        "IONQ", "RGTI", "QBTS",
        "SMR", "OKLO", "CCJ",
        "MP", "ALB", "LTHM",
        "SYM", "ISRG",
    ]

    resolved = []
    for text in unknown_texts:
        try:
            type_result = classifier(text, ENTITY_TYPES, multi_label=False)
            entity_type = type_result["labels"][0]

            ticker_result = classifier(text, TICKER_CANDIDATES[:20], multi_label=False)
            best_ticker = ticker_result["labels"][0] if ticker_result["scores"][0] > 0.3 else None

            resolved.append({
                "query": text,
                "type": entity_type,
                "ticker": best_ticker,
                "confidence": round(type_result["scores"][0], 3),
            })

            cursor.execute("""
                INSERT INTO resolution_cache (query_text, entity_type, ticker, confidence)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (query_text) DO UPDATE SET
                    ticker = EXCLUDED.ticker,
                    confidence = EXCLUDED.confidence
            """, (text, entity_type, best_ticker, type_result["scores"][0]))

        except Exception as e:
            print(f"Error resolving '{text}': {e}")

    conn.commit()
    conn.close()

    print(f"Resolved {len(resolved)} entities.")
    return resolved


if __name__ == "__main__":
    results = resolve_unknown_entities()
    for r in results[:10]:
        print(f"  {r['query']}: type={r['type']}, ticker={r['ticker']}, conf={r['confidence']}")
