from datetime import datetime, timezone, timedelta
from database import get_db_connection
from gap_engine import compute_gap_score
from anomaly_detector import detect_velocity_anomaly, detect_cross_platform
import json


def generate_signals():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT entity_id FROM entity_metrics_hourly")
    entity_ids = [r["entity_id"] for r in cursor.fetchall()]

    signals = []

    for eid in entity_ids:
        gap = compute_gap_score(eid)
        velocity = detect_velocity_anomaly(eid)
        cross_platform = detect_cross_platform(eid)

        corroboration = cross_platform["corroboration"] if cross_platform else 1
        velocity_z = velocity["z_score"] if velocity else 0

        cursor.execute("SELECT name FROM entities WHERE id = %s", (eid,))
        entity = cursor.fetchone()
        entity_name = entity["name"] if entity else "Unknown"

        cursor.execute("SELECT ticker FROM entity_tickers WHERE entity_id = %s", (eid,))
        ticker_row = cursor.fetchone()
        tickers = ticker_row["ticker"] if ticker_row else None

        direction = "long" if gap["gap_score"] > 0 else "watch"
        if gap.get("tradeable"):
            direction = "long"

        signal_score = gap["gap_score"] * gap["materiality"] * corroboration * 1.5

        if signal_score > 1.0:
            cursor.execute("""
                SELECT id FROM signals
                WHERE entity_id = %s AND created_at > NOW() - interval '72 hours'
            """, (eid,))
            existing = cursor.fetchone()
            if existing:
                continue

            cursor.execute("""
                INSERT INTO signals (
                    entity_id, tickers, direction, signal_score, gap_score,
                    demand_index, awareness_index, velocity_z, corroboration,
                    materiality, novelty, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'new')
                RETURNING id
            """, (
                eid, tickers, direction, round(signal_score, 3),
                gap["gap_score"], gap["demand_index"], gap["awareness_index"],
                velocity_z, corroboration, gap["materiality"],
                False,
            ))
            result = cursor.fetchone()
            if result:
                signals.append({
                    "signal_id": result["id"],
                    "entity": entity_name,
                    "tickers": tickers,
                    "score": round(signal_score, 3),
                    "gap": gap["gap_score"],
                    "direction": direction,
                })

    conn.close()
    print(f"Generated {len(signals)} new signals.")
    return signals


if __name__ == "__main__":
    signals = generate_signals()
    for s in signals:
        print(f"  [{s['direction'].upper()}] {s['entity']} ({s['tickers']}): score={s['score']}, gap={s['gap']}")
