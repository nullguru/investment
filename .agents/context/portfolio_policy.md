# Portfolio Construction Policy

Agreed construction rules for this portfolio. Reference in every advisor council response, screener recommendation, and rebalancing suggestion. Do not override unless the user explicitly asks to revisit.

**Decided:** April 2026

## Cap Allocation Target

| Segment | Target | Index Reference |
|---|---|---|
| Large Cap | **55%** | Nifty 100 constituents |
| Mid Cap | **30%** | Nifty Midcap 150 |
| Small Cap | **15%** | Nifty Smallcap 250 |

## Concentration Limits

| Rule | Limit |
|---|---|
| Max per sector (% of portfolio value) | **15%** |
| Max stocks per sector | **2–3** |
| Max per single stock | **8%** |
| Min sectors | **8** |
| Target total stocks | **15–18** |
| Hard max stocks | **20** |

## Target Sector Map

| Sector | Target Weight | Status (April 2026) |
|---|---|---|
| IT / Software | 12–15% | ⚠ Overweight — 3 stocks (TCS, INFY, HCLTECH). Do not add more. |
| Pharma / Healthcare | 10–12% | ✓ Present (SUNPHARMA, CIPLA) |
| FMCG / Consumer Staples | 8–10% | ⚠ Underweight — only 1 stock (HINDUNILVR). Add second when portfolio grows. |
| Industrial / Capital Goods | 10–12% | ✓ Present (CUMMINSIND, HAVELLS) |
| Auto / Auto Ancillary | 8–10% | ✗ Missing — priority sector to fill next |
| Energy (non-banking) | 7–10% | ✓ Present (GAIL) |
| Consumer Discretionary | 8–10% | ✓ Present (SAFARI) |
| Specialty Chemicals | 5–8% | ✗ Missing — small/mid cap alpha slot; run Sharia + screener check before adding |
| Healthcare Devices / Diagnostics | 5–8% | ✗ Missing — optional; add when conviction stock found |

## Growth Rule

> Always fill sector gaps before adding to existing sectors. Never add a 4th stock to IT (or any sector at 3 stocks) before all 8 target sectors have at least 1 holding.

## Benchmarking Policy

- **Do not** benchmark against Nifty 50 (37% financials = structurally unavailable to Sharia investors)
- Track personal XIRR informally against Nifty500 Shariah Index
- Portfolio construction and benchmarking are separate problems — build right first, measure alpha second

## SIP Deployment Rule

When deploying monthly SIP or opportunistic lump sums:
1. Identify underweight sectors vs target map above
2. Among underweight sectors, run momentum screen — prefer stocks with momentum score ≤ 40 (dip zone)
3. Confirm Piotroski ≥ 5 and red_flags ≤ 2 before buying
4. Never buy a stock already at/near 52-week high unless there is a specific catalyst

## CLI Commands for Policy Review

```bash
# Current portfolio vs benchmark
./cli.py portfolio-index --holdings "INFY.NS:24,HINDUNILVR.NS:21,SUNPHARMA.NS:20,CIPLA.NS:24,GAIL.NS:226,TATATECH.NS:56,HAVELLS.NS:9,CUMMINSIND.NS:16,SAFARI.NS:16,TCS.NS:9,HCLTECH.NS:23" --benchmark nifty50 --format json

# Screen a candidate stock before adding
./cli.py screener --symbol SYMBOL --screens "piotroski,altman_z,beneish_m,red_flags,momentum" --verbose --format json
./cli.py sharia SYMBOL --format json
```
