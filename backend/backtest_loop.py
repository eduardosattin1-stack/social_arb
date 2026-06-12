import httpx
from datetime import datetime, timezone, timedelta
from database import get_db_connection
from config import NEWS_API_KEY


def get_historical_price(ticker: str, date: str) -> float | None:
    if not ticker or ticker == "PRIVATE":
        return None

    try:
        resp = httpx.get(
            f"https://api.stockdata.org/v1/data/quote",
            params={"api_token": NEWS_API_KEY, "symbols": ticker},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data"):
                return float(data["data"][0].get("price", 0))
    except Exception:
        pass
    return None


def snapshot_signal_prices():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.tickers, s.created_at
        FROM signals s
        WHERE s.tickers IS NOT NULL
          AND s.tickers != 'PRIVATE'
          AND NOT EXISTS (
              SELECT 1 FROM signal_backtest sb WHERE sb.signal_id = s.id
          )
    """)
    signals = cursor.fetchall()

    if not signals:
        print("No new signals to snapshot.")
        conn.close()
        return

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_backtest (
            id SERIAL PRIMARY KEY,
            signal_id INTEGER REFERENCES signals(id),
            ticker TEXT,
            price_at_signal REAL,
            price_at_5d REAL,
            price_at_21d REAL,
            price_at_63d REAL,
            return_5d REAL,
            return_21d REAL,
            return_63d REAL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    print(f"Snapshotting prices for {len(signals)} signals...")
    saved = 0
    for sig in signals:
        tickers = [t.strip() for t in (sig["tickers"] or "").split(",") if t.strip()]
        for ticker in tickers[:1]:
            price = get_historical_price(ticker)
            if price:
                cursor.execute("""
                    INSERT INTO signal_backtest (signal_id, ticker, price_at_signal)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (sig["id"], ticker, price))
                saved += 1

    conn.commit()
    conn.close()
    print(f"Snapshotted {saved} prices.")


def update_backtest_returns():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sb.id, sb.ticker, sb.price_at_signal, sb.created_at,
               s.created_at as signal_date
        FROM signal_backtest sb
        JOIN signals s ON sb.signal_id = s.id
        WHERE sb.price_at_5d IS NULL
          AND sb.created_at < NOW() - interval '7 days'
    """)
    rows = cursor.fetchall()

    if not rows:
        print("No backtest rows to update yet.")
        conn.close()
        return

    print(f"Updating returns for {len(rows)} rows...")
    for row in rows:
        current_price = get_historical_price(row["ticker"])
        if current_price and row["price_at_signal"]:
            days_since = (datetime.now(timezone.utc) - row["created_at"]).days

            ret = (current_price - row["price_at_signal"]) / row["price_at_signal"]

            if days_since >= 5 and not row.get("price_at_5d"):
                cursor.execute("UPDATE signal_backtest SET price_at_5d = %s, return_5d = %s WHERE id = %s",
                               (current_price, ret, row["id"]))
            if days_since >= 21 and not row.get("price_at_21d"):
                cursor.execute("UPDATE signal_backtest SET price_at_21d = %s, return_21d = %s WHERE id = %s",
                               (current_price, ret, row["id"]))
            if days_since >= 63 and not row.get("price_at_63d"):
                cursor.execute("UPDATE signal_backtest SET price_at_63d = %s, return_63d = %s WHERE id = %s",
                               (current_price, ret, row["id"]))

    conn.commit()
    conn.close()
    print("Backtest returns updated.")


def get_backtest_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_signals,
            AVG(return_5d) as avg_return_5d,
            AVG(return_21d) as avg_return_21d,
            AVG(return_63d) as avg_return_63d,
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
    top = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return {"stats": stats, "top_signals": top}


if __name__ == "__main__":
    print("Running backtest loop...")
    snapshot_signal_prices()
    update_backtest_returns()
    stats = get_backtest_stats()
    print(f"\nBacktest stats: {stats['stats']}")
