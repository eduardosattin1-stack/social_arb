import httpx
from datetime import datetime, timezone
from sources.base import SourceAdapter, RawPost, CadenceTier, TOSPosture


class GDELTAdapter(SourceAdapter):
    name = "gdelt"
    cadence = CadenceTier.MEDIUM
    geo_scope = "global"
    lang_hint = "multilingual"
    tos_posture = TOSPosture.OFFICIAL_API
    rate_limit = "1 req/sec"

    def __init__(self, config: dict):
        super().__init__(config)
        self.themes = config.get("themes", [
            "artificial intelligence", "cryptocurrency", "electric vehicle",
            "tech stocks", "climate technology",
        ])

    def fetch(self) -> list[RawPost]:
        posts = []
        for theme in self.themes[:2]:
            try:
                resp = httpx.get(
                    "https://api.gdeltproject.org/api/v2/doc/doc",
                    params={
                        "query": theme,
                        "mode": "ArtList",
                        "maxrecords": 5,
                        "format": "json",
                        "sort": "DateDesc",
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for article in data.get("articles", []):
                        title = article.get("title", "")
                        url = article.get("url", "")
                        seendate = article.get("seendate", "")
                        try:
                            timestamp = datetime.strptime(seendate, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                        except Exception:
                            timestamp = datetime.now(timezone.utc)

                        posts.append(RawPost(
                            source="GDELT",
                            post_id=f"gdelt_{hash(url) & 0xFFFFFFFF:08x}",
                            content=f"{title}. {article.get('domain', '')}",
                            author=article.get("domain", "news"),
                            timestamp=timestamp,
                            url=url,
                            region=article.get("sourcelat", ""),
                        ))
                    self.on_success()
            except Exception as e:
                print(f"GDELT error for {theme}: {e}")
                self.on_failure()
        return posts
