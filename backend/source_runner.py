import importlib
import time
from datetime import datetime, timezone
from sources.registry import load_registry, get_enabled_sources
from sources.base import RawPost
from database import get_db_connection


def get_adapter(source_name: str, config: dict):
    adapter_map = {
        "hackernews": "scraper_hackernews",
        "mastodon": "scraper_mastodon",
        "reddit": "scraper_reddit",
        "newsapi": "scraper_newsapi",
        "bluesky": "sources.scraper_bluesky",
        "gdelt": "sources.scraper_gdelt",
        "youtube": "sources.scraper_youtube",
        "google_trends": "sources.scraper_google_trends",
        "wikipedia": "sources.scraper_wikipedia",
        "app_store": "sources.scraper_app_store",
        "stocktwits": "sources.scraper_stocktwits",
        "steam": "sources.scraper_steam",
        "github": "sources.scraper_github",
    }

    module_path = adapter_map.get(source_name)
    if not module_path:
        return None

    try:
        module = importlib.import_module(module_path)
        run_func = getattr(module, "run_scraper", None) or getattr(module, "scrape_" + source_name, None)
        if run_func:
            return type("AdapterRunner", (), {"fetch": lambda self: run_func() or []})()
        class_name = "".join(w.capitalize() for w in source_name.split("_")) + "Adapter"
        adapter_class = getattr(module, class_name, None)
        if not adapter_class:
            for attr_name in dir(module):
                if attr_name.endswith("Adapter") and source_name.lower().replace("_", "") in attr_name.lower():
                    adapter_class = getattr(module, attr_name)
                    break
        if adapter_class:
            return adapter_class(config)
    except Exception as e:
        print(f"Failed to load adapter for {source_name}: {e}")
    return None


def save_posts(posts: list):
    conn = get_db_connection()
    cursor = conn.cursor()
    saved_count = 0
    for post in posts:
        try:
            cursor.execute('''
                INSERT INTO posts (source, post_id, content, author, timestamp, url)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (post_id) DO NOTHING
            ''', (
                post.source if hasattr(post, 'source') else post.get("source", ""),
                post.post_id if hasattr(post, 'post_id') else post.get("post_id", ""),
                post.content if hasattr(post, 'content') else post.get("content", ""),
                post.author if hasattr(post, 'author') else post.get("author", ""),
                post.timestamp if hasattr(post, 'timestamp') else post.get("timestamp", datetime.now(timezone.utc)),
                post.url if hasattr(post, 'url') else post.get("url", ""),
            ))
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"Error saving post: {e}")

    conn.close()
    return saved_count


def run_source(source_name: str, config: dict) -> int:
    if not config.get("enabled", True):
        return 0

    adapter = get_adapter(source_name, config)
    if not adapter:
        print(f"No adapter found for {source_name}")
        return 0

    try:
        posts = adapter.fetch()
        if posts:
            saved = save_posts(posts)
            print(f"  {source_name}: {len(posts)} fetched, {saved} saved")
            return saved
    except Exception as e:
        print(f"  {source_name} failed: {e}")
    return 0


def run_all_sources():
    registry = load_registry()
    total = 0
    for source_name, config in registry.items():
        total += run_source(source_name, config)
    return total


if __name__ == "__main__":
    print(f"--- Running all sources at {datetime.now(timezone.utc)} ---")
    total = run_all_sources()
    print(f"--- Total: {total} new posts ---")
