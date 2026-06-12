import math
from datetime import datetime, timezone, timedelta
from database import get_db_connection


def compute_zscore(current: float, mean: float, std: float) -> float:
    if std == 0 or std is None:
        return 0.0
    return round((current - mean) / std, 2)


def detect_velocity_anomaly(entity_id: int, lookback_days: int = 30) -> dict | None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            AVG(mention_count) as mean_mentions,
            STDDEV(mention_count) as std_mentions
        FROM entity_metrics_hourly
        WHERE entity_id = %s
          AND ts_hour > NOW() - interval '%s days'
    """, (entity_id, lookback_days))

    stats = cursor.fetchone()
    if not stats or not stats["mean_mentions"]:
        conn.close()
        return None

    cursor.execute("""
        SELECT SUM(mention_count) as today_mentions
        FROM entity_metrics_hourly
        WHERE entity_id = %s
          AND ts_hour > date_trunc('day', NOW())
    """, (entity_id,))

    today = cursor.fetchone()
    conn.close()

    if not today or not today["today_mentions"]:
        return None

    z = compute_zscore(today["today_mentions"], stats["mean_mentions"], stats["std_mentions"])

    if z >= 2.5:
        return {
            "entity_id": entity_id,
            "detector": "velocity",
            "z_score": z,
            "current": today["today_mentions"],
            "mean": round(stats["mean_mentions"], 2),
        }
    return None


def detect_intent_shift(entity_id: int, lookback_days: int = 30) -> dict | None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            AVG(intent_purchase_share) as mean_intent,
            STDDEV(intent_purchase_share) as std_intent
        FROM entity_metrics_hourly
        WHERE entity_id = %s
          AND ts_hour > NOW() - interval '%s days'
    """, (entity_id, lookback_days))

    stats = cursor.fetchone()
    if not stats or not stats["mean_intent"]:
        conn.close()
        return None

    cursor.execute("""
        SELECT AVG(intent_purchase_share) as current_intent
        FROM entity_metrics_hourly
        WHERE entity_id = %s
          AND ts_hour > NOW() - interval '24 hours'
    """, (entity_id,))

    current = cursor.fetchone()
    conn.close()

    if not current or not current["current_intent"]:
        return None

    z = compute_zscore(current["current_intent"], stats["mean_intent"], stats["std_intent"])

    if z >= 2.0:
        return {
            "entity_id": entity_id,
            "detector": "intent_shift",
            "z_score": z,
            "current_intent": round(current["current_intent"], 3),
            "mean_intent": round(stats["mean_intent"], 3),
        }
    return None


def detect_novelty(entity_id: int, days_threshold: int = 14, min_mentions: int = 50) -> dict | None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT created_at FROM entities WHERE id = %s", (entity_id,))
    entity = cursor.fetchone()
    if not entity:
        conn.close()
        return None

    created = entity["created_at"]
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    days_since = (datetime.now(timezone.utc) - created).days

    cursor.execute("""
        SELECT SUM(mention_count) as total_mentions
        FROM entity_metrics_hourly
        WHERE entity_id = %s
          AND ts_hour > NOW() - interval '7 days'
    """, (entity_id,))

    result = cursor.fetchone()
    conn.close()

    total = result["total_mentions"] if result and result["total_mentions"] else 0

    if days_since <= days_threshold and total >= min_mentions:
        return {
            "entity_id": entity_id,
            "detector": "novelty",
            "days_since_creation": days_since,
            "total_mentions": total,
        }
    return None


def detect_cross_platform(entity_id: int, z_threshold: float = 1.5) -> dict | None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT platform, AVG(mention_count) as mean_mentions
        FROM entity_metrics_hourly
        WHERE entity_id = %s
          AND ts_hour > NOW() - interval '48 hours'
        GROUP BY platform
    """, (entity_id,))

    platforms = cursor.fetchall()
    conn.close()

    if len(platforms) < 2:
        return None

    corroboration = len([p for p in platforms if p["mean_mentions"] > 0])

    if corroboration >= 2:
        return {
            "entity_id": entity_id,
            "detector": "cross_platform",
            "corroboration": corroboration,
            "platforms": [p["platform"] for p in platforms],
        }
    return None


def run_anomaly_detection():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT entity_id FROM entity_metrics_hourly")
    entity_ids = [r["entity_id"] for r in cursor.fetchall()]
    conn.close()

    anomalies = []
    for eid in entity_ids:
        for detector in [detect_velocity_anomaly, detect_intent_shift, detect_novelty, detect_cross_platform]:
            result = detector(eid)
            if result:
                anomalies.append(result)

    print(f"Detected {len(anomalies)} anomalies across {len(entity_ids)} entities.")
    return anomalies


if __name__ == "__main__":
    anomalies = run_anomaly_detection()
    for a in anomalies[:5]:
        print(f"  [{a['detector']}] Entity {a['entity_id']}: z={a.get('z_score', 'N/A')}")
