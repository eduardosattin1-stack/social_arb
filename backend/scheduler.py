import time
import schedule
from datetime import datetime, timezone
from source_runner import run_all_sources
from ai_pipeline import process_unprocessed_posts
from entity_pipeline import process_entity_mentions
from metrics_aggregator import aggregate_hourly_metrics
from signal_generator import generate_signals
from backtest_loop import snapshot_signal_prices, update_backtest_returns


def hourly_job():
    print(f"\n--- Hourly cycle at {datetime.now(timezone.utc)} ---")
    total = run_all_sources()
    print(f"Ingested {total} new posts")

    process_unprocessed_posts()
    process_entity_mentions()
    aggregate_hourly_metrics()
    signals = generate_signals()
    print(f"Generated {len(signals)} signals")

    snapshot_signal_prices()
    update_backtest_returns()
    print("--- Hourly cycle complete ---\n")


def nightly_job():
    print(f"\n--- Nightly clustering at {datetime.now(timezone.utc)} ---")
    try:
        from topic_clusterer import cluster_topics, save_topics_to_db
        topics = cluster_topics()
        if topics:
            save_topics_to_db(topics)
    except Exception as e:
        print(f"Clustering error: {e}")
    print("--- Nightly clustering complete ---\n")


schedule.every(1).hours.do(hourly_job)
schedule.every().day.at("02:00").do(nightly_job)

if __name__ == "__main__":
    print("Starting Social Radar Background Worker...")
    hourly_job()
    while True:
        schedule.run_pending()
        time.sleep(1)
