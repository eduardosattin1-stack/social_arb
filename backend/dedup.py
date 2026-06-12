import hashlib
from database import get_db_connection


def compute_simhash(text: str, hashbits: int = 64) -> int:
    text = text.lower().strip()
    tokens = text.split()
    v = [0] * hashbits
    for token in tokens:
        token_hash = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(hashbits):
            if token_hash & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1
    fingerprint = 0
    for i in range(hashbits):
        if v[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint


def hamming_distance(h1: int, h2: int) -> int:
    return bin(h1 ^ h2).count("1")


def find_duplicates(hours: int = 48, threshold: int = 5) -> list[int]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, content, score
        FROM posts
        WHERE created_at > NOW() - interval '%s hours'
        ORDER BY created_at DESC
    """, (hours,))
    posts = cursor.fetchall()

    seen_hashes = []
    duplicate_ids = []

    for post in posts:
        h = compute_simhash(post["content"])
        is_dup = False
        for existing_h, existing_id, existing_score in seen_hashes:
            if hamming_distance(h, existing_h) <= threshold:
                if post["score"] <= existing_score:
                    duplicate_ids.append(post["id"])
                is_dup = True
                break
        if not is_dup:
            seen_hashes.append((h, post["id"], post.get("score", 0)))

    conn.close()
    return duplicate_ids


def get_engagement_weight(upvotes: int, platform: str = "generic") -> float:
    import math
    base = 1 + math.log(1 + upvotes)
    platform_multipliers = {
        "Reddit": 1.2,
        "HackerNews": 1.0,
        "Twitter": 0.8,
        "Mastodon": 0.9,
        "StockTwits": 1.1,
    }
    multiplier = platform_multipliers.get(platform, 1.0)
    return round(base * multiplier, 2)


if __name__ == "__main__":
    dupes = find_duplicates()
    print(f"Found {len(dupes)} duplicates in last 48h")
