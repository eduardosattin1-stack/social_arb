import math
from datetime import datetime, timezone, timedelta
from database import get_db_connection


def compute_zscore(current, mean, std) -> float:
    if std == 0 or std is None or mean is None:
        return 0.0
    c, m, s = float(current or 0), float(mean or 0), float(std or 0)
    if s == 0:
        return 0.0
    return round((c - m) / s, 2)


def get_demand_index(entity_id: int) -> float:
    conn = get_db_connection()
    cursor = conn.cursor()

    components = []

    cursor.execute("""
        WITH daily AS (
            SELECT SUM(mention_count) as daily_total
            FROM entity_metrics_hourly
            WHERE entity_id = %s
            GROUP BY date_trunc('day', ts_hour)
        )
        SELECT
            MAX(daily_total) as current,
            AVG(daily_total) as mean,
            STDDEV(daily_total) as std
        FROM daily
    """, (entity_id,))
    row = cursor.fetchone()
    if row and row["mean"]:
        z = compute_zscore(row["current"], row["mean"], row["std"])
        components.append(z)

    cursor.execute("""
        WITH hourly_intent AS (
            SELECT AVG(intent_purchase_share) as intent_val
            FROM entity_metrics_hourly
            WHERE entity_id = %s AND ts_hour > NOW() - interval '24 hours'
        )
        SELECT
            intent_val as current_intent,
            (SELECT AVG(intent_purchase_share) FROM entity_metrics_hourly WHERE entity_id = %s) as mean_intent,
            (SELECT STDDEV(intent_purchase_share) FROM entity_metrics_hourly WHERE entity_id = %s) as std_intent
        FROM hourly_intent
    """, (entity_id, entity_id, entity_id))
    row = cursor.fetchone()
    if row and row["mean_intent"]:
        z = compute_zscore(row["current_intent"], row["mean_intent"], row["std_intent"])
        components.append(z)

    conn.close()

    if not components:
        return 0.0
    return round(float(sum(components)) / len(components), 2)


def get_awareness_index(entity_id: int) -> float:
    conn = get_db_connection()
    cursor = conn.cursor()

    components = []

    cursor.execute("SELECT name, aliases FROM entities WHERE id = %s", (entity_id,))
    entity = cursor.fetchone()
    if not entity:
        conn.close()
        return 0.0

    name_lower = entity["name"].lower()
    alias_list = [a.strip().lower() for a in (entity["aliases"] or "").split(",") if a.strip()]
    search_terms = [name_lower] + alias_list[:3]

    like_clauses = " OR ".join(["LOWER(content) LIKE %s"] * len(search_terms))
    like_params = [f"%{t}%" for t in search_terms]

    cursor.execute(f"""
        SELECT COUNT(*) as news_count
        FROM posts
        WHERE source LIKE 'News:%%'
          AND timestamp > NOW() - interval '24 hours'
          AND ({like_clauses})
    """, like_params)
    row = cursor.fetchone()
    if row and row["news_count"]:
        components.append(min(row["news_count"] / 10, 3.0))

    cursor.execute("""
        SELECT SUM(mention_count) as st_count
        FROM entity_metrics_hourly
        WHERE entity_id = %s AND platform = 'StockTwits' AND ts_hour > NOW() - interval '24 hours'
    """, (entity_id,))
    row = cursor.fetchone()
    if row and row["st_count"]:
        components.append(min(row["st_count"] / 5, 3.0))

    conn.close()

    if not components:
        return 0.0
    return round(float(sum(components)) / len(components), 2)


def compute_gap_score(entity_id: int) -> dict:
    demand = get_demand_index(entity_id)
    awareness = get_awareness_index(entity_id)
    gap = round(demand - awareness, 2)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT et.mono_brand, et.mcap_usd
        FROM entity_tickers et
        WHERE et.entity_id = %s
        LIMIT 1
    """, (entity_id,))
    ticker_info = cursor.fetchone()
    conn.close()

    materiality = 0.5
    mono_brand = False
    if ticker_info:
        mono_brand = ticker_info.get("mono_brand", False)
        mcap = ticker_info.get("mcap_usd", 100000000000)
        if mcap and mcap > 0:
            materiality = min(max(0.9 if mono_brand else 1.0 / math.log10(mcap), 0.05), 1.0)

    return {
        "entity_id": entity_id,
        "demand_index": demand,
        "awareness_index": awareness,
        "gap_score": gap,
        "materiality": round(materiality, 3),
        "mono_brand": mono_brand,
        "tradeable": demand >= 2.0 and awareness <= 0.5 and materiality >= 0.15,
    }


def compute_all_gaps():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT entity_id FROM entity_metrics_hourly")
    entity_ids = [r["entity_id"] for r in cursor.fetchall()]
    conn.close()

    gaps = []
    for eid in entity_ids:
        gap = compute_gap_score(eid)
        if abs(gap["gap_score"]) > 0.5:
            gaps.append(gap)

    gaps.sort(key=lambda x: x["gap_score"], reverse=True)
    print(f"Computed gap scores for {len(entity_ids)} entities, {len(gaps)} with significant gaps.")
    return gaps


if __name__ == "__main__":
    gaps = compute_all_gaps()
    for g in gaps[:5]:
        print(f"  Entity {g['entity_id']}: Demand={g['demand_index']}, Awareness={g['awareness_index']}, Gap={g['gap_score']}")
