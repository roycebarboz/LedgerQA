# 11: Tiered caching + rate-limited live fallback

**What to build:** A strict lookup order — cache, then batch-populated local store, then live SEC EDGAR call as last resort. Live calls are throttled below SEC's 10 req/sec threshold and carry a compliant User-Agent. No agent tool-call ever hits EDGAR directly without first checking the cache.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] A repeated lookup for the same company/filing/concept is served from cache, not a fresh live call
- [ ] Live calls are throttled to a safe ceiling (e.g. 8 req/sec) below SEC's ban threshold
- [ ] All live calls carry a compliant User-Agent set globally at startup
- [ ] Cache miss falls through to batch store, then live call, in that order, never skipping a tier
