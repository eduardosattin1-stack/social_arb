from datetime import datetime, timezone, timedelta
from database import get_db_connection


def aggregate_hourly_metrics():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            em.entity_id,
            date_trunc('hour', p.timestamp) as ts_hour,
            p.source as platform,
            p.region,
            COUNT(*) as mention_count,
            SUM(COALESCE(p.score, 1)) as weighted_mentions,
            AVG(p.sentiment) as sentiment_mean,
            STDDEV(p.sentiment) as sentiment_std,
            AVG(CASE WHEN em.intent IN ('purchased', 'intends_to_purchase', 'switching_to') THEN 1.0 ELSE 0.0 END) as intent_purchase_share,
            AVG(CASE WHEN em.intent IN ('switching_from', 'canceled_churned') THEN 1.0 ELSE 0.0 END) as intent_churn_share,
            AVG(CASE WHEN em.intent = 'sold_out_unavailable' THEN 1.0 ELSE 0.0 END) as scarcity_share,
            COUNT(DISTINCT p.author) as unique_authors
        FROM entity_mentions em
        JOIN posts p ON em.post_id = p.id
        WHERE p.timestamp > NOW() - interval '24 hours'
        GROUP BY em.entity_id, date_trunc('hour', p.timestamp), p.source, p.region
    """)

    rows = cursor.fetchall()
    inserted = 0

    for row in rows:
        try:
            cursor.execute('''
                INSERT INTO entity_metrics_hourly (
                    entity_id, ts_hour, platform, region,
                    mention_count, weighted_mentions, sentiment_mean, sentiment_std,
                    intent_purchase_share, intent_churn_share, scarcity_share, unique_authors
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (
                row["entity_id"], row["ts_hour"], row["platform"], row["region"],
                row["mention_count"], row["weighted_mentions"],
                round(row["sentiment_mean"], 3) if row["sentiment_mean"] else 0,
                round(row["sentiment_std"], 3) if row["sentiment_std"] else 0,
                round(row["intent_purchase_share"], 3) if row["intent_purchase_share"] else 0,
                round(row["intent_churn_share"], 3) if row["intent_churn_share"] else 0,
                round(row["scarcity_share"], 3) if row["scarcity_share"] else 0,
                row["unique_authors"],
            ))
            inserted += 1
        except Exception as e:
            print(f"Error inserting metric: {e}")

    conn.close()
    print(f"Aggregated {inserted} hourly metric rows.")
    return inserted


if __name__ == "__main__":
    print("Running hourly aggregation...")
    aggregate_hourly_metrics()
