from datetime import datetime, timezone
from database import get_db_connection


def get_new_signals():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, e.name as entity_name
        FROM signals s
        JOIN entities e ON s.entity_id = e.id
        WHERE s.status = 'new'
        ORDER BY s.signal_score DESC
        LIMIT 10
    """)
    signals = []
    for sig in cursor.fetchall():
        signals.append({
            "id": sig["id"],
            "entity": sig["entity_name"],
            "tickers": sig["tickers"],
            "direction": sig["direction"],
            "score": float(sig["signal_score"]) if sig["signal_score"] else 0,
            "gap_score": float(sig["gap_score"]) if sig["gap_score"] else 0,
            "demand_index": float(sig["demand_index"]) if sig["demand_index"] else 0,
            "awareness_index": float(sig["awareness_index"]) if sig["awareness_index"] else 0,
            "created_at": sig["created_at"].isoformat() if sig["created_at"] else None,
        })

    conn.close()
    return signals


if __name__ == "__main__":
    signals = get_new_signals()
    for s in signals:
        print(f"  [{s['direction'].upper()}] {s['entity']} ({s['tickers']}): score={s['score']}")
