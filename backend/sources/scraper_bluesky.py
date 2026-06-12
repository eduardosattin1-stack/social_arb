import httpx
from datetime import datetime, timezone
from sources.base import SourceAdapter, RawPost, CadenceTier, TOSPosture


class BlueskyAdapter(SourceAdapter):
    name = "bluesky"
    cadence = CadenceTier.FAST
    geo_scope = "global"
    lang_hint = "multilingual"
    tos_posture = TOSPosture.PUBLIC_FEED
    rate_limit = "30 req/min"

    def __init__(self, config: dict):
        super().__init__(config)
        self.instances = config.get("instances", [
            "https://bsky.social",
            "https://public.api.bsky.app",
        ])

    def fetch(self) -> list[RawPost]:
        posts = []
        for instance in self.instances:
            try:
                resp = httpx.get(
                    f"{instance}/xrpc/app.bsky.feed.searchPosts",
                    params={"q": "AI OR crypto OR EV OR tech", "limit": 10},
                    headers={"User-Agent": "SocialArb/1.0"},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("posts", [])[:5]:
                        record = item.get("record", {})
                        posts.append(RawPost(
                            source="Bluesky",
                            post_id=f"bsky_{item.get('uri', '').split('/')[-1]}",
                            content=record.get("text", "")[:1000],
                            author=record.get("did", "unknown"),
                            timestamp=datetime.fromisoformat(
                                record.get("createdAt", datetime.now(timezone.utc).isoformat())
                            ),
                            url=item.get("uri", ""),
                        ))
                    self.on_success()
                    break
            except Exception as e:
                print(f"Bluesky error on {instance}: {e}")
                self.on_failure()
        return posts
