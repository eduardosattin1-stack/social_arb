from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import get_db_connection
from config import DATABASE_URL
from routes_signals import register_signal_routes

app = FastAPI(title="Social Radar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_signal_routes(app)


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
