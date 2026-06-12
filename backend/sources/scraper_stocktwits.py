import httpx
from datetime import datetime, timezone
from sources.base import SourceAdapter, RawPost, CadenceTier, TOSPosture


class StockTwitsAdapter(SourceAdapter):
    name = "stocktwits"
    cadence = CadenceTier.MEDIUM
    geo_scope = "us"
    lang_hint = "en"
    tos_posture = TOSPosture.PUBLIC_FEED
    rate_limit = "10 req/min"

    def __init__(self, config: dict):
        super().__init__(config)
        self.tickers = config.get("tickers", [
            "AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "META",
        ])

    def fetch(self) -> list[RawPost]:
        posts = []
        for ticker in self.tickers[:3]:
            try:
                resp = httpx.get(
                    f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json",
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for msg in data.get("messages", [])[:3]:
                        body = msg.get("body", "")
                        created = msg.get("created_at", "")
                        try:
                            timestamp = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        except Exception:
                            timestamp = datetime.now(timezone.utc)

                        posts.append(RawPost(
                            source="StockTwits",
                            post_id=f"st_{msg.get('id', '')}",
                            content=f"[{ticker}] {body}",
                            author=msg.get("user", {}).get("username", "unknown"),
                            timestamp=timestamp,
                            url=f"https://stocktwits.com/message/{msg.get('id', '')}",
                            metadata={"ticker": ticker, "side": "awareness"},
                        ))
                    self.on_success()
            except Exception as e:
                print(f"StockTwits error for {ticker}: {e}")
                self.on_failure()
        return posts
