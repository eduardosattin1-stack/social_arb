from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db_connection
from datetime import datetime, timezone


class VerdictRequest(BaseModel):
    signal_id: int
    verdict: str
    note: Optional[str] = ""


class SignalResponse(BaseModel):
    id: int
    entity_name: str
    tickers: Optional[str]
    direction: str
    signal_score: float
    gap_score: float
    demand_index: float
    awareness_index: float
    velocity_z: float
    corroboration: int
    materiality: float
    novelty: bool
    status: str
    created_at: str


def register_signal_routes(app: FastAPI):

    @app.get("/api/signals")
    def get_signals(status: str = "new", limit: int = 20):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT s.*, e.name as entity_name
                FROM signals s
                JOIN entities e ON s.entity_id = e.id
                WHERE s.status = %s
                ORDER BY s.signal_score DESC
                LIMIT %s
            """, (status, limit))
            signals = []
            for row in cursor.fetchall():
                sig = dict(row)
                sig["created_at"] = sig["created_at"].isoformat() if sig["created_at"] else None
                sig["signal_score"] = float(sig["signal_score"]) if sig["signal_score"] else 0
                sig["gap_score"] = float(sig["gap_score"]) if sig["gap_score"] else 0
                sig["demand_index"] = float(sig["demand_index"]) if sig["demand_index"] else 0
                sig["awareness_index"] = float(sig["awareness_index"]) if sig["awareness_index"] else 0
                sig["velocity_z"] = float(sig["velocity_z"]) if sig["velocity_z"] else 0
                sig["materiality"] = float(sig["materiality"]) if sig["materiality"] else 0
                signals.append(sig)
        except Exception:
            signals = []
        conn.close()
        return signals

    @app.get("/api/signals/{signal_id}")
    def get_signal(signal_id: int):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT s.*, e.name as entity_name
                FROM signals s
                JOIN entities e ON s.entity_id = e.id
                WHERE s.id = %s
            """, (signal_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Signal not found")
            sig = dict(row)
            sig["created_at"] = sig["created_at"].isoformat() if sig["created_at"] else None
            for key in ["signal_score", "gap_score", "demand_index", "awareness_index", "velocity_z", "materiality"]:
                sig[key] = float(sig[key]) if sig[key] else 0
        finally:
            conn.close()
        return sig

    @app.post("/api/signals/verdict")
    def submit_verdict(req: VerdictRequest):
        if req.verdict not in ("investigating", "passed", "positioned", "closed"):
            raise HTTPException(status_code=400, detail="Invalid verdict")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO verdicts (signal_id, verdict, note)
                VALUES (%s, %s, %s)
            """, (req.signal_id, req.verdict, req.note))

            cursor.execute("""
                UPDATE signals SET status = %s WHERE id = %s
            """, (req.verdict, req.signal_id))

            return {"status": "ok", "signal_id": req.signal_id, "verdict": req.verdict}
        finally:
            conn.close()

    @app.get("/api/health/sources")
    def source_health():
        from sources.registry import load_registry
        registry = load_registry()
        health = []
        for name, config in registry.items():
            health.append({
                "name": name,
                "enabled": config.get("enabled", False),
                "cadence": config.get("cadence", "unknown"),
                "tos_posture": config.get("tos_posture", "unknown"),
            })
        return health

    @app.get("/api/entities")
    def get_entities(limit: int = 50):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT e.id, e.name, e.type,
                       (SELECT ticker FROM entity_tickers WHERE entity_id = e.id LIMIT 1) as ticker,
                       (SELECT mcap_usd FROM entity_tickers WHERE entity_id = e.id LIMIT 1) as mcap_usd,
                       (SELECT mono_brand FROM entity_tickers WHERE entity_id = e.id LIMIT 1) as mono_brand,
                       (SELECT COUNT(*) FROM entity_mentions em WHERE em.entity_id = e.id) as mention_count
                FROM entities e
                ORDER BY mention_count DESC
                LIMIT %s
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @app.get("/api/entities/{entity_id}/mentions")
    def get_entity_mentions(entity_id: int, limit: int = 20):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT em.*, p.content, p.source, p.timestamp, p.url
                FROM entity_mentions em
                JOIN posts p ON em.post_id = p.id
                WHERE em.entity_id = %s
                ORDER BY p.timestamp DESC
                LIMIT %s
            """, (entity_id, limit))
            mentions = []
            for row in cursor.fetchall():
                m = dict(row)
                m["timestamp"] = m["timestamp"].isoformat() if m["timestamp"] else None
                mentions.append(m)
        finally:
            conn.close()
        return mentions

    @app.get("/api/entities/{entity_id}/history")
    def get_entity_history(entity_id: int, hours: int = 168):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    date_trunc('hour', ts_hour) as hour,
                    SUM(mention_count) as mentions,
                    AVG(sentiment_mean) as sentiment,
                    AVG(intent_purchase_share) as intent_purchase,
                    SUM(unique_authors) as authors
                FROM entity_metrics_hourly
                WHERE entity_id = %s
                  AND ts_hour > NOW() - interval '%s hours'
                GROUP BY date_trunc('hour', ts_hour)
                ORDER BY hour
            """, (entity_id, hours))
            history = []
            for row in cursor.fetchall():
                h = dict(row)
                h["hour"] = h["hour"].isoformat() if h["hour"] else None
                h["mentions"] = h["mentions"] or 0
                h["sentiment"] = round(float(h["sentiment"]), 3) if h["sentiment"] else 0
                h["intent_purchase"] = round(float(h["intent_purchase"]), 3) if h["intent_purchase"] else 0
                h["authors"] = h["authors"] or 0
                history.append(h)
        finally:
            conn.close()
        return history

    @app.get("/api/entities/{entity_id}/intent")
    def get_entity_intent(entity_id: int):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    em.intent,
                    COUNT(*) as count,
                    AVG(em.intent_score) as avg_score
                FROM entity_mentions em
                WHERE em.entity_id = %s
                  AND em.intent != 'neutral'
                GROUP BY em.intent
                ORDER BY count DESC
            """, (entity_id,))
            intents = [dict(row) for row in cursor.fetchall()]
            for i in intents:
                i["avg_score"] = round(float(i["avg_score"]), 3) if i["avg_score"] else 0
        finally:
            conn.close()
        return intents

    @app.get("/api/clusters")
    def get_topic_clusters(limit: int = 20):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT topic_id, label, keywords, count, created_at
                FROM topic_clusters
                ORDER BY count DESC
                LIMIT %s
            """, (limit,))
            clusters = []
            for row in cursor.fetchall():
                c = dict(row)
                c["created_at"] = c["created_at"].isoformat() if c["created_at"] else None
                clusters.append(c)
        except Exception:
            clusters = []
        finally:
            conn.close()
        return clusters

    @app.get("/api/backtest")
    def get_backtest():
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_signals,
                    COALESCE(AVG(return_5d), 0) as avg_return_5d,
                    COALESCE(AVG(return_21d), 0) as avg_return_21d,
                    COALESCE(AVG(return_63d), 0) as avg_return_63d,
                    SUM(CASE WHEN return_21d > 0.05 THEN 1 ELSE 0 END) as winners_21d,
                    COUNT(CASE WHEN return_21d IS NOT NULL THEN 1 END) as measured_21d
                FROM signal_backtest
            """)
            stats = dict(cursor.fetchone())

            cursor.execute("""
                SELECT s.entity_name, s.tickers, sb.return_21d, sb.created_at
                FROM signal_backtest sb
                JOIN signals s ON sb.signal_id = s.id
                WHERE sb.return_21d IS NOT NULL
                ORDER BY sb.return_21d DESC
                LIMIT 10
            """)
            top = []
            for row in cursor.fetchall():
                t = dict(row)
                t["created_at"] = t["created_at"].isoformat() if t["created_at"] else None
                t["return_21d"] = round(float(t["return_21d"]), 4) if t["return_21d"] else 0
                top.append(t)

            for k in ["avg_return_5d", "avg_return_21d", "avg_return_63d"]:
                stats[k] = round(float(stats[k]), 4) if stats[k] else 0
        except Exception:
            stats = {"total_signals": 0, "avg_return_5d": 0, "avg_return_21d": 0, "avg_return_63d": 0, "winners_21d": 0, "measured_21d": 0}
            top = []
        finally:
            conn.close()
        return {"stats": stats, "top_signals": top}

    @app.get("/api/trends/daily")
    def get_daily_trends(days: int = 30):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    date_trunc('day', timestamp) as day,
                    COUNT(*) as total_posts,
                    COUNT(DISTINCT source) as sources,
                    COALESCE(AVG(sentiment), 0) as avg_sentiment,
                    COUNT(CASE WHEN sentiment > 0.1 THEN 1 END) as positive,
                    COUNT(CASE WHEN sentiment < -0.1 THEN 1 END) as negative
                FROM posts
                WHERE timestamp > NOW() - interval '%s days'
                GROUP BY date_trunc('day', timestamp)
                ORDER BY day
            """, (days,))
            trends = []
            for row in cursor.fetchall():
                t = dict(row)
                t["day"] = t["day"].isoformat() if t["day"] else None
                t["avg_sentiment"] = round(float(t["avg_sentiment"]), 3)
                trends.append(t)
        except Exception:
            trends = []
        finally:
            conn.close()
        return trends

    @app.get("/api/entities/top")
    def get_top_entities(metric: str = "mentions", limit: int = 20):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            order_col = "mention_count" if metric == "mentions" else "mention_count"
            cursor.execute(f"""
                SELECT e.id, e.name, e.type,
                       (SELECT ticker FROM entity_tickers WHERE entity_id = e.id LIMIT 1) as ticker,
                       (SELECT mcap_usd FROM entity_tickers WHERE entity_id = e.id LIMIT 1) as mcap_usd,
                       (SELECT COUNT(*) FROM entity_mentions em WHERE em.entity_id = e.id) as mention_count,
                       (SELECT AVG(em.intent_score) FROM entity_mentions em WHERE em.entity_id = e.id AND em.intent = 'purchased') as purchase_intent,
                       (SELECT AVG(p.sentiment) FROM entity_mentions em JOIN posts p ON em.post_id = p.id WHERE em.entity_id = e.id) as avg_sentiment
                FROM entities e
                ORDER BY {order_col} DESC
                LIMIT %s
            """, (limit,))
            entities = []
            for row in cursor.fetchall():
                ent = dict(row)
                ent["mention_count"] = ent["mention_count"] or 0
                ent["purchase_intent"] = round(float(ent["purchase_intent"]), 3) if ent["purchase_intent"] else 0
                ent["avg_sentiment"] = round(float(ent["avg_sentiment"]), 3) if ent["avg_sentiment"] else 0
                entities.append(ent)
        except Exception:
            entities = []
        finally:
            conn.close()
        return entities
