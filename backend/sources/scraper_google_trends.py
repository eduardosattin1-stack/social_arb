from datetime import datetime, timezone
from sources.base import SourceAdapter, RawPost, CadenceTier, TOSPosture


class GoogleTrendsAdapter(SourceAdapter):
    name = "google_trends"
    cadence = CadenceTier.DAILY
    geo_scope = "per_country"
    lang_hint = "multilingual"
    tos_posture = TOSPosture.SCRAPE_WITH_CARE
    rate_limit = "10 req/hour"

    def __init__(self, config: dict):
        super().__init__(config)
        self.countries = config.get("countries", ["US", "BR", "DE", "GB", "IN", "JP", "KR"])
        self.interests = config.get("interests", [
            "artificial intelligence", "bitcoin", "tesla", "chatgpt",
        ])

    def fetch(self) -> list[RawPost]:
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl="en-US", tz=360)
        except Exception as e:
            print(f"pytrends import failed: {e}")
            return []

        posts = []
        for interest in self.interests[:2]:
            try:
                pytrends.build_payload(
                    [interest],
                    cat=0,
                    timeframe="now 7-d",
                    geo="US",
                )
                data = pytrends.interest_over_time()
                if not data.empty:
                    latest = data[interest].iloc[-1]
                    posts.append(RawPost(
                        source="GoogleTrends",
                        post_id=f"trends_{interest.replace(' ', '_')}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                        content=f"Google Trends interest for '{interest}': {latest}",
                        author="google_trends",
                        timestamp=datetime.now(timezone.utc),
                        url=f"https://trends.google.com/trends/explore?q={interest.replace(' ', '+')}",
                        metadata={"interest_value": int(latest)},
                    ))
                    self.on_success()
            except Exception as e:
                print(f"Google Trends error for {interest}: {e}")
                self.on_failure()
        return posts
