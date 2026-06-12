from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class TOSPosture(Enum):
    OFFICIAL_API = "official_api"
    PUBLIC_FEED = "public_feed"
    SCRAPE_WITH_CARE = "scrape_with_care"
    PAID_REQUIRED = "paid_required"


class CadenceTier(Enum):
    FAST = "fast"
    MEDIUM = "medium"
    DAILY = "daily"


@dataclass
class RawPost:
    source: str
    post_id: str
    content: str
    author: str
    timestamp: datetime
    url: str = ""
    lang: str = ""
    region: str = ""
    upvotes: int = 0
    comments: int = 0
    metadata: dict = field(default_factory=dict)


class SourceAdapter(ABC):
    name: str
    cadence: CadenceTier
    geo_scope: str
    lang_hint: str
    tos_posture: TOSPosture
    rate_limit: str

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", True)
        self.last_success_at: Optional[datetime] = None
        self.consecutive_failures: int = 0

    @abstractmethod
    def fetch(self) -> list[RawPost]:
        pass

    def on_success(self):
        self.last_success_at = datetime.now(timezone.utc)
        self.consecutive_failures = 0

    def on_failure(self):
        self.consecutive_failures += 1

    @property
    def is_circuit_broken(self) -> bool:
        return self.consecutive_failures >= 3

    def health_check(self) -> dict:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "consecutive_failures": self.consecutive_failures,
            "circuit_broken": self.is_circuit_broken,
        }
