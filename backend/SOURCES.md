# Social Arb — Source Registry

## Source Status Dashboard

| Source | Status | ToS Posture | Cadence | Rate Limit | Notes |
|--------|--------|-------------|---------|------------|-------|
| HackerNews | ✅ Live | public_feed | fast (3m) | 10 req/min | Firebase API |
| Mastodon | ✅ Live | public_feed | fast (3m) | 30 req/min | 3 instances |
| Reddit | ⚠️ Rate-limited | public_feed | medium (15m) | 1 req/5s | RSS fallback, rotating subreddits |
| NewsAPI | ✅ Live | official_api | medium (15m) | 100 req/day | Free tier |
| Bluesky | 🔄 Pending | public_feed | fast (3m) | 30 req/min | Jetstream websocket or search API |
| GDELT | 🔄 Pending | official_api | medium (15m) | 1 req/sec | Global news backbone |
| YouTube | 🔄 Pending | official_api | daily | 10k units/day | Comments for purchase intent |
| Google Trends | 🔄 Pending | scrape_with_care | daily | 10 req/hour | pytrends, expect breakage |
| Wikipedia | 🔄 Pending | official_api | daily | 200 req/sec | Attention confirmation layer |
| App Store | 🔄 Pending | public_feed | daily | 1 req/min | Per-country rank movements |
| StockTwits | 🔄 Pending | public_feed | medium (15m) | 10 req/min | Awareness-side index |
| Steam | 🔄 Pending | official_api | daily | 10 req/min | Gaming consumer behavior |
| GitHub | 🔄 Pending | official_api | daily | 60 req/hour | Developer tool adoption |

## ToS Posture Definitions

- **official_api**: Uses documented, free-tier API with proper authentication
- **public_feed**: Uses public RSS/JSON endpoints without authentication
- **scrape_with_care**: Polite scraping with delays, user-agent rotation
- **paid_required**: Requires paid subscription (Phase 4 decision)

## Adding a New Source

1. Create `sources/scraper_<name>.py` with a class extending `SourceAdapter`
2. Add entry to `sources/registry.yaml`
3. Add adapter path to `ADAPTER_MAP` in `sources/registry.py`
4. Document in this file
5. Target: < 1 hour per source

## Blocked Sources

| Source | Blocker | Workaround |
|--------|---------|------------|
| Reddit JSON | 403 from datacenter IPs | RSS feed fallback, rate-limited |
| Twitter/X | API requires $100/month minimum | Replaced with Mastodon |
