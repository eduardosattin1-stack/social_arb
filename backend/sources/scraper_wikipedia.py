import httpx
from datetime import datetime, timezone
from sources.base import SourceAdapter, RawPost, CadenceTier, TOSPosture


class WikipediaAdapter(SourceAdapter):
    name = "wikipedia"
    cadence = CadenceTier.DAILY
    geo_scope = "global"
    lang_hint = "multilingual"
    tos_posture = TOSPosture.OFFICIAL_API
    rate_limit = "200 req/sec"

    BASE_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"

    def __init__(self, config: dict):
        super().__init__(config)
        self.articles = config.get("articles", [
            "Artificial_intelligence", "Bitcoin", "Tesla,_Inc.", "ChatGPT",
        ])

    def fetch(self) -> list[RawPost]:
        posts = []
        for article in self.articles:
            try:
                resp = httpx.get(
                    f"{self.BASE_URL}/en.wikipedia/all-access/all-agents/{article}/daily/20260101/20260131",
                    headers={"User-Agent": "SocialArb/1.0"},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    if items:
                        latest = items[-1]
                        views = latest.get("views", 0)
                        posts.append(RawPost(
                            source="Wikipedia",
                            post_id=f"wiki_{article}_{latest.get('timestamp', '')}",
                            content=f"Wikipedia article '{article}' received {views} views",
                            author="wikimedia",
                            timestamp=datetime.now(timezone.utc),
                            url=f"https://en.wikipedia.org/wiki/{article}",
                            metadata={"views": views},
                        ))
                        self.on_success()
            except Exception as e:
                print(f"Wikipedia error for {article}: {e}")
                self.on_failure()
        return posts
