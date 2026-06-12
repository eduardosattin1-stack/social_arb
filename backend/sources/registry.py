import yaml
from pathlib import Path
from typing import Dict, Type
from sources.base import SourceAdapter, CadenceTier

REGISTRY_PATH = Path(__file__).parent / "registry.yaml"


def load_registry() -> Dict[str, dict]:
    with open(REGISTRY_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("sources", {})


ADAPTER_MAP: Dict[str, str] = {
    "hackernews": "sources.scraper_hackernews.HackerNewsAdapter",
    "mastodon": "sources.scraper_mastodon.MastodonAdapter",
    "reddit": "sources.scraper_reddit.RedditAdapter",
    "newsapi": "sources.scraper_newsapi.NewsAPIAdapter",
    "bluesky": "sources.scraper_bluesky.BlueskyAdapter",
    "gdelt": "sources.scraper_gdelt.GDELTAdapter",
    "youtube": "sources.scraper_youtube.YouTubeAdapter",
    "google_trends": "sources.scraper_google_trends.GoogleTrendsAdapter",
    "wikipedia": "sources.scraper_wikipedia.WikipediaAdapter",
    "app_store": "sources.scraper_app_store.AppStoreAdapter",
    "stocktwits": "sources.scraper_stocktwits.StockTwitsAdapter",
    "steam": "sources.scraper_steam.SteamAdapter",
    "github": "sources.scraper_github.GitHubAdapter",
}


def get_sources_by_cadence(cadence: str) -> list[str]:
    registry = load_registry()
    return [
        name
        for name, config in registry.items()
        if config.get("cadence") == cadence and config.get("enabled", True)
    ]


def get_enabled_sources() -> list[str]:
    registry = load_registry()
    return [name for name, config in registry.items() if config.get("enabled", True)]


def get_source_config(source_name: str) -> dict:
    registry = load_registry()
    return registry.get(source_name, {})
