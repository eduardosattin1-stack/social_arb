import httpx
from datetime import datetime, timezone
from sources.base import SourceAdapter, RawPost, CadenceTier, TOSPosture


class AppStoreAdapter(SourceAdapter):
    name = "app_store"
    cadence = CadenceTier.DAILY
    geo_scope = "per_country"
    lang_hint = "multilingual"
    tos_posture = TOSPosture.PUBLIC_FEED
    rate_limit = "1 req/min"

    RSS_BASE = "https://rss.marketingtools.apple.com/api/v2"

    def __init__(self, config: dict):
        super().__init__(config)
        self.countries = config.get("countries", ["US", "GB", "JP", "DE", "BR"])

    def fetch(self) -> list[RawPost]:
        posts = []
        for country in self.countries[:3]:
            try:
                resp = httpx.get(
                    f"{self.RSS_BASE}/{country}/apps/top-free/10/apps.json",
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    feed = data.get("feed", {})
                    results = feed.get("results", [])
                    for i, app in enumerate(results[:5]):
                        posts.append(RawPost(
                            source="AppStore",
                            post_id=f"app_{country}_{app.get('id', '')}",
                            content=f"#{i+1} Top Free App in {country}: {app.get('name', '')} by {app.get('artistName', '')}",
                            author=app.get("artistName", "unknown"),
                            timestamp=datetime.now(timezone.utc),
                            url=app.get("url", ""),
                            metadata={"rank": i + 1, "country": country},
                        ))
                    self.on_success()
            except Exception as e:
                print(f"App Store error for {country}: {e}")
                self.on_failure()
        return posts
