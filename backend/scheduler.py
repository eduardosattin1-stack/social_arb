import time
import schedule
from source_runner import run_all_sources
from ai_pipeline import process_unprocessed_posts


def job():
    print("\n--- Running scheduled ingestion cycle ---")
    total = run_all_sources()
    print(f"Ingested {total} new posts")

    print("Running AI pipeline...")
    process_unprocessed_posts()
    print("--- Cycle complete ---\n")


schedule.every(1).hours.do(job)

if __name__ == "__main__":
    print("Starting Social Radar Background Worker...")
    job()
    while True:
        schedule.run_pending()
        time.sleep(1)
