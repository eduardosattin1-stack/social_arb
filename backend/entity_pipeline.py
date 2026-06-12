from entity_graph import build_alias_lookup, resolve_entities
from intent_classifier import classify_intent
from database import get_db_connection


def extract_entities_from_post(post_id: int, content: str, alias_lookup: dict) -> list[dict]:
    matches = resolve_entities(content, alias_lookup)
    results = []
    for entity_id, matched_text in matches:
        intent, intent_score = classify_intent(content)
        results.append({
            "post_id": post_id,
            "entity_id": entity_id,
            "matched_text": matched_text,
            "method": "alias",
            "intent": intent,
            "intent_score": intent_score,
        })
    return results


def process_entity_mentions():
    alias_lookup = build_alias_lookup()
    print(f"Loaded {len(alias_lookup)} aliases.")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.content
        FROM posts p
        LEFT JOIN entity_mentions em ON p.id = em.post_id
        WHERE em.id IS NULL
    """)
    posts = cursor.fetchall()

    total_mentions = 0
    for post in posts:
        mentions = extract_entities_from_post(post["id"], post["content"], alias_lookup)
        for m in mentions:
            try:
                cursor.execute('''
                    INSERT INTO entity_mentions (post_id, entity_id, matched_text, method, intent, intent_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (m["post_id"], m["entity_id"], m["matched_text"], m["method"], m["intent"], m["intent_score"]))
                total_mentions += 1
            except Exception as e:
                print(f"Error inserting mention: {e}")

    conn.close()
    print(f"Extracted {total_mentions} entity mentions from {len(posts)} posts.")
    return total_mentions


if __name__ == "__main__":
    print("Starting entity extraction pipeline...")
    process_entity_mentions()
