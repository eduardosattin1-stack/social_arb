import httpx
from datetime import datetime, timezone
from sources.base import SourceAdapter, RawPost, CadenceTier, TOSPosture
from config import YOUTUBE_API_KEY


class YouTubeAdapter(SourceAdapter):
    name = "youtube"
    cadence = CadenceTier.DAILY
    geo_scope = "global"
    lang_hint = "multilingual"
    tos_posture = TOSPosture.OFFICIAL_API
    rate_limit = "10k units/day"

    def __init__(self, config: dict):
        super().__init__(config)
        self.queries = config.get("queries", [
            "AI review", "crypto news", "EV unboxing", "tech earnings",
        ])
        self.api_key = YOUTUBE_API_KEY

    def fetch(self) -> list[RawPost]:
        if not self.api_key:
            print("YouTube API key not set, skipping")
            return []

        posts = []
        for query in self.queries[:2]:
            try:
                resp = httpx.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "maxResults": 3,
                        "order": "date",
                        "key": self.api_key,
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    for item in resp.json().get("items", []):
                        snippet = item.get("snippet", {})
                        video_id = item.get("id", {}).get("videoId", "")
                        published = snippet.get("publishedAt", "")
                        try:
                            timestamp = datetime.fromisoformat(published.replace("Z", "+00:00"))
                        except Exception:
                            timestamp = datetime.now(timezone.utc)

                        posts.append(RawPost(
                            source="YouTube",
                            post_id=f"yt_{video_id}",
                            content=f"{snippet.get('title', '')}. {snippet.get('description', '')[:500]}",
                            author=snippet.get("channelTitle", "unknown"),
                            timestamp=timestamp,
                            url=f"https://youtube.com/watch?v={video_id}",
                        ))
                    self.on_success()
            except Exception as e:
                print(f"YouTube error for {query}: {e}")
                self.on_failure()
        return posts
