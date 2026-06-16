# Portfolio Construction Policy

**Authoritative source for all numeric rules: `modules/portfolio/policy.py`** — `CAP_TARGETS`, `CONCENTRATION`, `SECTOR_TARGETS`. The UI Portfolio page and backend gap analysis are driven directly by those constants. If a rule changes, change it there; this file explains the *why* and the *behavioural context* that the code cannot carry.

**Decided:** April 2026

## Why these rules exist

**55/30/15 large/mid/small split** — Large caps provide stability and liquidity; mid/small provide alpha. Sharia constraint excludes most large-cap financials, so the portfolio naturally skews toward industrials, pharma, and IT — sectors where mid/small cap quality is high. 55% large is a floor, not a ceiling.

**15% sector max, 8% stock max** — Prevents any single thesis from being portfolio-damaging. At a 15–18 stock portfolio, these limits naturally enforce 2–3 stocks per sector.

**15–18 stock target** — Sweet spot: sufficient diversification without diluting research quality. Below 10 = one bad thesis is portfolio-damaging. Above 20 = diminishing benefit, harder to track deeply.

**8+ sectors minimum** — Sharia eliminates all financials (~37% of Nifty 50). The remaining universe is concentrated in IT, Pharma, FMCG, Industrials. Forcing 8 sectors creates genuine diversification rather than an IT-heavy proxy.

## Behavioural rules (not in policy.py)

**Growth rule:** Always fill sector gaps before adding to existing sectors. Never add a 4th stock to IT (or any sector already at 3) before all 8 target sectors have at least 1 holding.

**Benchmarking:** Do not benchmark against Nifty 50 (37% financials = structurally unavailable to Sharia investors). Track personal XIRR informally against Nifty500 Shariah Index. Portfolio construction and benchmarking are separate problems — build right first, measure alpha second.

**SIP deployment:**
1. Identify underweight sectors (check UI Portfolio page → Diagnosis, or run `./cli.py portfolio-index`)
2. Among underweight sectors, prefer momentum score ≤ 40 (dip zone)
3. Confirm Piotroski ≥ 5 and red_flags ≤ 2 before buying
4. Never buy a stock at/near its 52-week high unless there is a specific catalyst

## Current sector status

Current status is derived live from holdings. To check:
```bash
# Read current holdings from db/settings.json (personalIndexHoldingsText), then:
./cli.py portfolio-index --holdings "SYMBOL:units,..." --benchmark nifty50 --format json

# Screen a candidate before adding
./cli.py screener --symbol SYMBOL --screens "piotroski,altman_z,beneish_m,red_flags,momentum" --verbose --format json
./cli.py sharia SYMBOL --format json
```
