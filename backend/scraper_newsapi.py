import requests
from datetime import datetime, timedelta, timezone
from database import get_db_connection
from config import NEWS_API_KEY

NEWS_API_BASE = "https://newsapi.org/v2"

SUBREDDITS = [
    "technology", "artificial", "CryptoCurrency", "ElectricVehicles",
    "Futurology", "business", "stocks", "worldnews",
]


def scrape_news_api(queries=None, page_size=10):
    if not NEWS_API_KEY:
        print("NEWS_API_KEY not set. Skipping NewsAPI scrape.")
        return []

    print("Scraping NewsAPI for latest articles...")
    if queries is None:
        queries = [
            "artificial intelligence",
            "cryptocurrency",
            "electric vehicles",
            "tech stocks",
            "climate technology",
        ]

    all_posts = []
    from_date = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%d")

    for query in queries:
        try:
            resp = requests.get(
                f"{NEWS_API_BASE}/everything",
                params={
                    "q": query,
                    "from": from_date,
                    "sortBy": "publishedAt",
                    "pageSize": page_size,
                    "language": "en",
                    "apiKey": NEWS_API_KEY,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                print(f"NewsAPI error for '{query}': {resp.status_code}")
                continue

            data = resp.json()
            for article in data.get("articles", []):
                title = article.get("title", "")
                description = article.get("description", "") or ""
                content = f"{title}. {description}".strip()
                if not content or content == ".":
                    continue

                published = article.get("publishedAt", "")
                try:
                    timestamp = datetime.fromisoformat(published.replace("Z", "+00:00"))
                except Exception:
                    timestamp = datetime.now(timezone.utc)

                source_name = article.get("source", {}).get("name", "NewsAPI")
                url = article.get("url", "")

                all_posts.append({
                    "source": f"News:{source_name}",
                    "post_id": f"news_{hash(url) & 0xFFFFFFFF:08x}",
                    "content": content,
                    "author": source_name,
                    "timestamp": timestamp,
                    "url": url,
                })
        except Exception as e:
            print(f"NewsAPI request failed for '{query}': {e}")

    print(f"Fetched {len(all_posts)} articles from NewsAPI.")
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
            print(f"Error saving news post: {e}")

    conn.close()
    print(f"Saved {saved_count} new articles from NewsAPI.")


def run_scraper():
    posts = scrape_news_api()
    save_posts(posts)


if __name__ == "__main__":
    run_scraper()
