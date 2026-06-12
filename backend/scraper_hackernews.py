import requests
from datetime import datetime, timezone
from database import get_db_connection


def scrape_hackernews(limit=15):
    print("Scraping Hacker News for Tech Trends...")
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []

        story_ids = response.json()[:limit]
        posts = []

        for story_id in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story_res = requests.get(story_url, timeout=10)
            if story_res.status_code == 200:
                story_data = story_res.json()
                if not story_data:
                    continue

                timestamp = datetime.fromtimestamp(
                    story_data.get("time", 0), tz=timezone.utc
                )

                posts.append({
                    "source": "HackerNews",
                    "post_id": f"hn_{story_id}",
                    "content": story_data.get("title", ""),
                    "author": story_data.get("by", ""),
                    "timestamp": timestamp,
                    "url": story_data.get("url", ""),
                    "score": story_data.get("score", 0),
                    "num_comments": story_data.get("descendants", 0),
                })
        return posts
    except Exception as e:
        print(f"HackerNews scraping failed: {e}")
        return []


def save_posts(posts):
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
                post["score"], post["num_comments"]
            ))
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"Error saving post: {e}")

    conn.close()
    print(f"Saved {saved_count} new posts from HackerNews.")


if __name__ == "__main__":
    posts = scrape_hackernews()
    save_posts(posts)
