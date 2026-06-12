import httpx
from datetime import datetime, timezone
from sources.base import SourceAdapter, RawPost, CadenceTier, TOSPosture


class GitHubAdapter(SourceAdapter):
    name = "github"
    cadence = CadenceTier.DAILY
    geo_scope = "global"
    lang_hint = "en"
    tos_posture = TOSPosture.OFFICIAL_API
    rate_limit = "60 req/hour"

    def __init__(self, config: dict):
        super().__init__(config)
        self.languages = config.get("languages", ["python", "typescript", "rust"])

    def fetch(self) -> list[RawPost]:
        posts = []
        for lang in self.languages[:2]:
            try:
                resp = httpx.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": f"language:{lang} created:>2026-01-01",
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 3,
                    },
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=15,
                )
                if resp.status_code == 200:
                    for repo in resp.json().get("items", [])[:3]:
                        posts.append(RawPost(
                            source="GitHub",
                            post_id=f"gh_{repo.get('id', '')}",
                            content=f"Trending repo: {repo.get('full_name', '')} - {repo.get('description', '')[:200]}",
                            author=repo.get("owner", {}).get("login", "unknown"),
                            timestamp=datetime.fromisoformat(
                                repo.get("created_at", datetime.now(timezone.utc).isoformat())
                            ),
                            url=repo.get("html_url", ""),
                            metadata={"stars": repo.get("stargazers_count", 0)},
                        ))
                    self.on_success()
            except Exception as e:
                print(f"GitHub error for {lang}: {e}")
                self.on_failure()
        return posts
