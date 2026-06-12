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
                       et.ticker, et.mcap_usd, et.mono_brand,
                       (SELECT COUNT(*) FROM entity_mentions em WHERE em.entity_id = e.id) as mention_count
                FROM entities e
                LEFT JOIN entity_tickers et ON e.id = et.entity_id
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
