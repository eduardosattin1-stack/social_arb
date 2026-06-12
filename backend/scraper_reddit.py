import httpx
import time
import random
from datetime import datetime, timezone
from database import get_db_connection
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
import html
import re

ALL_SUBREDDITS = [
    "technology", "stocks", "CryptoCurrency", "ElectricVehicles",
    "Futurology", "wallstreetbets", "worldnews", "artificial",
    "BuyItForLife", "SkincareAddiction", "running", "Costco",
    "frugal", "HomeImprovement", "EatCheapAndHealthy", "parenting",
    "india", "brasil", "europe", "mexico", "korea", "japan", "australia",
    "gadgets", "science",
]

SUBREDDITS_PER_RUN = 3


class RedditOAuthScraper:
    def __init__(self):
        self.client_id = REDDIT_CLIENT_ID
        self.client_secret = REDDIT_CLIENT_SECRET
        self.user_agent = REDDIT_USER_AGENT
        self.access_token = None
        self.token_expires = 0

    def get_access_token(self):
        if self.access_token and time.time() < self.token_expires:
            return self.access_token

        if not self.client_id or not self.client_secret:
            return None

        try:
            resp = httpx.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": self.user_agent},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data["access_token"]
                self.token_expires = time.time() + data.get("expires_in", 3600) - 60
                return self.access_token
        except Exception as e:
            print(f"Reddit OAuth failed: {e}")
        return None

    def fetch_subreddit(self, subreddit: str, limit: int = 5) -> list:
        token = self.get_access_token()
        if not token:
            return self._fetch_rss_fallback(subreddit, limit)

        try:
            resp = httpx.get(
                f"https://oauth.reddit.com/r/{subreddit}/hot",
                params={"limit": limit, "raw_json": 1},
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": self.user_agent,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return self._parse_json_response(resp.json(), subreddit)
            else:
                print(f"Reddit OAuth returned {resp.status_code} for r/{subreddit}")
                return self._fetch_rss_fallback(subreddit, limit)
        except Exception as e:
            print(f"Reddit OAuth error for r/{subreddit}: {e}")
            return self._fetch_rss_fallback(subreddit, limit)

    def _fetch_rss_fallback(self, subreddit: str, limit: int) -> list:
        import feedparser
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.rss"
            feed = feedparser.parse(url, agent=self.user_agent)
            posts = []
            for entry in feed.entries[:limit]:
                title = self._clean_html(entry.get("title", ""))
                summary = self._clean_html(entry.get("summary", ""))
                link = entry.get("link", "")
                updated = entry.get("updated", "")

                if not title:
                    continue

                content = title
                if summary:
                    content += f". {summary[:500]}"

                try:
                    timestamp = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                except Exception:
                    timestamp = datetime.now(timezone.utc)

                post_id = link.split("/")[-2] if "/" in link else link

                posts.append({
                    "source": f"Reddit:{subreddit}",
                    "post_id": f"reddit_{post_id}",
                    "content": content[:1000],
                    "author": entry.get("author", "reddit"),
                    "timestamp": timestamp,
                    "url": link,
                })
            return posts
        except Exception as e:
            print(f"Reddit RSS fallback failed for r/{subreddit}: {e}")
            return []

    def _parse_json_response(self, data: dict, subreddit: str) -> list:
        posts = []
        for item in data.get("data", {}).get("children", []):
            post = item.get("data", {})
            if post.get("stickied"):
                continue

            title = post.get("title", "")
            selftext = post.get("selftext", "")
            content = title
            if selftext:
                content += f". {selftext[:500]}"

            created = post.get("created_utc", 0)
            timestamp = datetime.fromtimestamp(created, tz=timezone.utc)
            permalink = post.get("permalink", "")

            posts.append({
                "source": f"Reddit:{subreddit}",
                "post_id": f"reddit_{post.get('id', '')}",
                "content": content[:1000],
                "author": post.get("author", "[deleted]"),
                "timestamp": timestamp,
                "url": f"https://reddit.com{permalink}",
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
            })
        return posts

    def _clean_html(self, text: str) -> str:
        text = html.unescape(text)
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()


scraper = RedditOAuthScraper()


def scrape_reddit(subreddits_per_run: int = SUBREDDITS_PER_RUN) -> list:
    selected = random.sample(ALL_SUBREDDITS, min(subreddits_per_run, len(ALL_SUBREDDITS)))
    print(f"Scraping Reddit: {', '.join(selected)}...")

    all_posts = []
    for i, sub_name in enumerate(selected):
        if i > 0:
            time.sleep(2)
        posts = scraper.fetch_subreddit(sub_name, limit=5)
        all_posts.extend(posts)
        print(f"  r/{sub_name}: {len(posts)} posts")

    print(f"Fetched {len(all_posts)} posts from Reddit.")
    return all_posts


def save_posts(posts: list):
    conn = get_db_connection()
    cursor = conn.cursor()
    saved_count = 0
    for post in posts:
        try:
            cursor.execute('''
                INSERT INTO posts (source, post_id, content, author, timestamp, url, score, num_comments)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (post_id) DO NOTHING
            ''', (
                post["source"], post["post_id"], post["content"],
                post["author"], post["timestamp"], post["url"],
                post.get("score", 0), post.get("num_comments", 0),
            ))
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"Error saving Reddit post: {e}")

    conn.close()
    print(f"Saved {saved_count} new posts from Reddit.")


def run_scraper():
    posts = scrape_reddit()
    save_posts(posts)


if __name__ == "__main__":
    run_scraper()
