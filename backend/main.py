from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import get_db_connection
from config import DATABASE_URL
from routes_signals import register_signal_routes
import time
from collections import defaultdict

app = FastAPI(title="Social Radar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_signal_routes(app)

rate_limit_store = defaultdict(list)
RATE_LIMIT = 60
RATE_WINDOW = 60


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if now - t < RATE_WINDOW
    ]

    if len(rate_limit_store[client_ip]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "retry_after": RATE_WINDOW}
        )

    rate_limit_store[client_ip].append(now)
    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)[:200]}
    )


@app.get("/api/health")
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) as total_posts FROM posts")
        total_posts = cursor.fetchone()["total_posts"]

        cursor.execute("SELECT source, COUNT(*) as count FROM posts GROUP BY source")
        source_counts = {row["source"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT
                COALESCE(AVG(sentiment), 0) as avg_sentiment,
                COALESCE(SUM(CASE WHEN sentiment > 0.1 THEN 1 ELSE 0 END), 0) as positive_count,
                COALESCE(SUM(CASE WHEN sentiment < -0.1 THEN 1 ELSE 0 END), 0) as negative_count
            FROM posts
        """)
        sentiment_stats = cursor.fetchone()
    except Exception:
        total_posts = 0
        source_counts = {}
        sentiment_stats = {"avg_sentiment": 0, "positive_count": 0, "negative_count": 0}

    conn.close()
    return {
        "total_posts": total_posts,
        "source_counts": source_counts,
        "avg_sentiment": round(float(sentiment_stats["avg_sentiment"]), 3),
        "positive_count": sentiment_stats["positive_count"],
        "negative_count": sentiment_stats["negative_count"],
    }


@app.get("/api/posts")
def get_recent_posts(limit: int = 50):
    limit = min(limit, 100)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM posts ORDER BY timestamp DESC LIMIT %s", (limit,))
        posts = [dict(row) for row in cursor.fetchall()]
    except Exception:
        posts = []
    conn.close()
    return posts


@app.get("/api/trends")
def get_trends(hours: int = 24):
    hours = min(hours, 168)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                date_trunc('hour', timestamp) as hour,
                COUNT(*) as volume,
                COALESCE(AVG(sentiment), 0) as avg_sentiment
            FROM posts
            WHERE timestamp > NOW() - interval '%s hours'
            GROUP BY date_trunc('hour', timestamp)
            ORDER BY hour
        """, (hours,))
        trends = [dict(row) for row in cursor.fetchall()]
        for t in trends:
            t["hour"] = t["hour"].isoformat() if t["hour"] else None
            t["avg_sentiment"] = round(float(t["avg_sentiment"]), 3)
    except Exception:
        trends = []
    conn.close()
    return trends


@app.get("/api/regions")
def get_region_breakdown():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                COALESCE(region, 'Global') as region,
                COUNT(*) as volume,
                COALESCE(AVG(sentiment), 0) as avg_sentiment
            FROM posts
            GROUP BY region
            ORDER BY volume DESC
        """)
        regions = [dict(row) for row in cursor.fetchall()]
        for r in regions:
            r["avg_sentiment"] = round(float(r["avg_sentiment"]), 3)
    except Exception:
        regions = []
    conn.close()
    return regions


@app.get("/api/topics")
def get_topics():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                COALESCE(topic, 'Unclassified') as topic,
                COUNT(*) as volume,
                COALESCE(AVG(sentiment), 0) as avg_sentiment
            FROM posts
            WHERE topic IS NOT NULL AND topic != ''
            GROUP BY topic
            ORDER BY volume DESC
            LIMIT 20
        """)
        topics = [dict(row) for row in cursor.fetchall()]
        for t in topics:
            t["avg_sentiment"] = round(float(t["avg_sentiment"]), 3)
    except Exception:
        topics = []
    conn.close()
    return topics
