import requests
from datetime import datetime, timezone
from database import get_db_connection

MASTODON_INSTANCES = [
    "https://mastodon.social",
    "https://fosstodon.org",
    "https://techhub.social",
]


def scrape_mastodon(limit=10):
    print("Scraping Mastodon trending posts...")
    all_posts = []

    for instance in MASTODON_INSTANCES:
        try:
            resp = requests.get(
                f"{instance}/api/v1/trends/statuses",
                params={"limit": limit},
                timeout=10,
                headers={"User-Agent": "SocialRadar/1.0"},
            )
            if resp.status_code != 200:
                continue

            for status in resp.json():
                content = status.get("content", "")
                if not content:
                    continue

                import re
                content = re.sub(r"<[^>]+>", "", content).strip()
                if not content:
                    continue

                created = status.get("created_at", "")
                try:
                    timestamp = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except Exception:
                    timestamp = datetime.now(timezone.utc)

                account = status.get("account", {})

                all_posts.append({
                    "source": "Mastodon",
                    "post_id": f"mastodon_{status.get('id', '')}",
                    "content": content[:1000],
                    "author": account.get("acct", "unknown"),
                    "timestamp": timestamp,
                    "url": status.get("url", ""),
                })
        except Exception as e:
            print(f"Mastodon scrape failed for {instance}: {e}")

    print(f"Fetched {len(all_posts)} posts from Mastodon.")
    return all_posts


def save_posts(posts):
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
                post["source"], post["post_id"], post["content"],
                post["author"], post["timestamp"], post["url"],
            ))
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"Error saving Mastodon post: {e}")

    conn.close()
    print(f"Saved {saved_count} new posts from Mastodon.")


def run_scraper():
    posts = scrape_mastodon()
    save_posts(posts)


if __name__ == "__main__":
    run_scraper()
