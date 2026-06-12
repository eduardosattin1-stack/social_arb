import httpx
from datetime import datetime, timezone
from sources.base import SourceAdapter, RawPost, CadenceTier, TOSPosture


class SteamAdapter(SourceAdapter):
    name = "steam"
    cadence = CadenceTier.DAILY
    geo_scope = "global"
    lang_hint = "en"
    tos_posture = TOSPosture.OFFICIAL_API
    rate_limit = "10 req/min"

    def __init__(self, config: dict):
        super().__init__(config)
        self.app_ids = config.get("app_ids", [
            "730", "440", "570", "1091500", "1245620",
        ])

    def fetch(self) -> list[RawPost]:
        posts = []
        for app_id in self.app_ids[:3]:
            try:
                resp = httpx.get(
                    f"https://store.steampowered.com/api/appdetails",
                    params={"appids": app_id},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json().get(app_id, {})
                    if data.get("success"):
                        info = data.get("data", {})
                        posts.append(RawPost(
                            source="Steam",
                            post_id=f"steam_{app_id}",
                            content=f"Steam game: {info.get('name', '')} - {info.get('short_description', '')[:200]}",
                            author="steam_store",
                            timestamp=datetime.now(timezone.utc),
                            url=f"https://store.steampowered.com/app/{app_id}",
                            metadata={"app_id": app_id},
                        ))
                        self.on_success()
            except Exception as e:
                print(f"Steam error for {app_id}: {e}")
                self.on_failure()
        return posts
