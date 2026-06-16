---
name: investment
description: Investment analysis platform and decision framework — stock screening (Sharia compliance), market data, portfolio analysis, personal Sharia index rebalancing, buy/hold/sell evaluation, any-stock idea review, and multi-advisor investment suggestions for Indian/US stocks.
---

# Investment Platform Agent Skill

This is the canonical shared agent skill for this repository.
Platform-specific wrappers in `.claude/skills/investment.md` and `.codex/skills/investment/SKILL.md` should refer here instead of duplicating workflow instructions.

## Setup

```bash
cd /Users/msaadr/Developer/Private/investment
source .venv/bin/activate
```

## CLI Reference

The CLI is the primary interface. Always use `--format json` for structured output.

### Check cache freshness (do this first)
```bash
./cli.py cache status --format json
```

### Universe (ticker lists)
```bash
# Stats
./cli.py universe --stats --format json

# List all tickers
./cli.py universe --format json --limit 20

# Filter by exchange
./cli.py universe --exchange NSE --format json
```

### Sharia compliance
```bash
# Single symbol (base name auto-resolves: TCS → TCS.NS)
./cli.py sharia TCS --format json

# All periods for a symbol
./cli.py sharia TCS --periods --format json

# List all compliant stocks
./cli.py sharia list --format json

# Filter by period
./cli.py sharia list --period "31st March 2025" --format json
```

### Compute (fetch new data)
```bash
# Specific symbols
./cli.py compute sharia --symbols "TCS,INFY,HCLTECH" --format json

# Default portfolio
./cli.py compute sharia --portfolio --format json

# Missing symbols (not yet cached)
./cli.py compute sharia --missing --limit 50 --format json
```

### Market data lookup
```bash
# Sections: overview, market, financials, valuation
./cli.py lookup TCS.NS --section financials --format json
./cli.py lookup TCS.NS --section valuation --format json
```

### Compare stocks
```bash
./cli.py compare TCS.NS INFY.NS HCLTECH.NS --format json
```

### Import external data
```bash
# BSE scrip list (after downloading CSV)
./cli.py import --type bse-scrips --file /path/to/Equity.csv --format json

# NSE market cap data (after downloading Excel)
./cli.py import --type nse-mcap --file /path/to/Average_MCAP_NSE.xlsx --format json
```

### Watchlist management
```bash
# List watchlist with Sharia enrichment
./cli.py watchlist list --format json

# Add symbols
./cli.py watchlist add TCS INFY RELIANCE --format json

# Remove a symbol
./cli.py watchlist remove RELIANCE --format json

# Clear entire watchlist
./cli.py watchlist clear --format json
```

### Benchmarks
```bash
# List all configured benchmarks
./cli.py benchmarks list --format json

# Inspect a specific benchmark (shows all constituent symbols)
./cli.py benchmarks show nifty50 --format json
./cli.py benchmarks show sensex30 --format json
```

### Compare stocks
```bash
./cli.py compare TCS.NS INFY.NS HCLTECH.NS --format json
```

### Cache management
```bash
# Status
./cli.py cache status --format json

# Clear all (or specific module)
./cli.py cache clear --format json
./cli.py cache clear --module sharia --format json
```

### Start web UI
```bash
./cli.py serve --port 8000
```

## Web Fetch Protocol

When the CLI cannot get data via API (exit code 2 or `needs_web_fetch` in JSON):

1. **BSE scrip list**: Search web for "BSE India equity list download" or go to bseindia.com → Corporates → List_Scrips → select Equity, Active → Download. Save CSV, then:
   ```bash
   ./cli.py import --type bse-scrips --file /path/to/downloaded.csv
   ```

2. **NSE market cap data**: Search web for "NSE average market cap data" or check nseindia.com. Save Excel, then:
   ```bash
   ./cli.py import --type nse-mcap --file /path/to/downloaded.xlsx
   ```

3. **Company-specific data not in yfinance**: Use web search to find the information, then report it directly to the user (no import needed for ad-hoc queries).

## Per-Stock Research (web-backed)

Research generates structured analysis for 8 sections per stock using web search. Data is stored as JSON and displayed in the UI.

### CLI
```bash
# Check what's stored
./cli.py research CUMMINSIND.NS --view --format json

# Single section
./cli.py research CUMMINSIND.NS --section thesis --view --format json

# Trigger research (returns needs_web_research signal)
./cli.py research CUMMINSIND.NS --format json
```

### Research Workflow

When the user asks to "research" a stock, do the following for each section:

1. **WebSearch** for the company + section topic (use queries below)
2. **Compile** findings into the section's JSON schema
3. **Store** via PUT to the running server:
   ```bash
   curl -s -X PUT "http://localhost:8000/api/symbol/SYMBOL/research/SECTION" \
     -H "Content-Type: application/json" -d '{"section":"...","symbol":"...","updated_at":"...","sources":[{"title":"...","url":"..."}],"data":{...}}'
   ```
4. **Report** a summary of findings in chat

### Search Queries Per Section

| Section | What to search |
|---------|---------------|
| thesis | "[Company] investment thesis 2025 2026", "[Company] bull bear case analysis" |
| industry | "[Company] industry market size growth", "[Industry name] competitive landscape India" |
| business | "[Company] business model revenue streams", "[Company] competitive advantage moat" |
| management | "[Company] CEO CFO leadership team background", "[Company] management compensation" |
| esg | "[Company] ESG rating sustainability score", "[Company] environmental social governance" |
| estimates | "[Company] analyst estimates consensus EPS revenue forecast", "[Company] price target" |
| revenue | "[Company] revenue breakdown segment geography annual report", "[Company] revenue mix" |
| catalysts | "[Company] upcoming events catalysts 2025 2026", "[Company] earnings date product launch" |

### JSON Schemas

**Thesis** `data`:
```json
{"summary":"...","bull_case":{"target":"₹2400","probability":30,"drivers":["..."],"narrative":"..."},"base_case":{"target":"₹1900","probability":50,"drivers":["..."],"narrative":"..."},"bear_case":{"target":"₹1200","probability":20,"drivers":["..."],"narrative":"..."},"key_drivers":["..."],"key_risks":["..."],"verdict":"Buy|Hold|Sell"}
```

**Industry** `data`:
```json
{"industry_name":"...","market_size":"USD 12B","growth_rate":"7.2% CAGR","trends":[{"title":"...","description":"..."}],"competitive_landscape":[{"company":"...","market_share":"...","notes":"..."}],"barriers_to_entry":["..."],"regulatory_environment":"..."}
```

**Business** `data`:
```json
{"model_summary":"...","revenue_streams":[{"name":"...","pct_of_revenue":45,"description":"...","growth":"..."}],"moat_type":"Brand|Network|Cost|Switching|Scale","moat_description":"...","competitive_advantages":["..."],"customer_concentration":"...","pricing_power":"Low|Medium|High"}
```

**Management** `data`:
```json
{"ceo":{"name":"...","since":"2020","background":"...","compensation":"..."},"cfo":{"name":"...","since":"2021","background":"...","compensation":"..."},"other_key_executives":[{"name":"...","title":"...","since":"...","background":"..."}],"board_independence_pct":60,"insider_ownership_pct":5.2,"track_record":"...","red_flags":["..."]}
```

**ESG** `data`:
```json
{"overall_rating":"AA","rating_provider":"MSCI","environmental":{"score":"...","highlights":["..."],"controversies":["..."]},"social":{"score":"...","highlights":["..."],"controversies":["..."]},"governance":{"score":"...","highlights":["..."],"controversies":["..."]},"notable_initiatives":["..."]}
```

**Estimates** `data`:
```json
{"consensus_rating":"Buy","analyst_count":12,"price_target":{"low":1200,"mean":1800,"high":2400,"currency":"INR"},"eps_estimates":[{"period":"FY2026","consensus":85.2,"low":78,"high":92}],"revenue_estimates":[{"period":"FY2026","consensus":"32000 Cr","low":"30000 Cr","high":"35000 Cr"}],"estimate_revisions":{"direction":"up|down|flat","detail":"..."}}
```

**Revenue** `data`:
```json
{"total_revenue":"INR 32,000 Cr (FY2025)","by_segment":[{"name":"...","revenue":"...","pct":45,"yoy_growth":"12%"}],"by_geography":[{"region":"...","revenue":"...","pct":70,"yoy_growth":"8%"}],"revenue_quality":"...","recurring_pct":30}
```

**Catalysts** `data`:
```json
{"upcoming":[{"date":"2026-05-15","event":"Q4 Earnings","impact":"High","description":"..."}],"recent":[{"date":"2026-03-10","event":"...","impact":"Medium","description":"..."}],"long_term":[{"catalyst":"...","timeframe":"12-18 months","description":"..."}]}
```

### Full Research Workflow Example

When user says "research CUMMINSIND.NS":
1. First get basic info: `./cli.py lookup CUMMINSIND.NS --section overview --format json`
2. For each of the 8 sections, do 2-3 web searches using the queries above
3. Compile each section into its JSON schema
4. PUT each section to the API
5. Show a summary in chat with key findings per section
6. The data is now visible in the UI under Per Stock Research tabs

## Advisor Council Decision Framework

Use this mode when the user asks questions such as:

- "Should I buy, hold, sell, add, reduce, or avoid this stock?"
- "Give me your best suggestions from these stocks."
- "Pressure-test my thesis."
- "Rank these ideas."
- "What is the risk/reward on this position?"

This mode is a modified "council of advisors" workflow. Do not answer with a single flat opinion when the user is making an investment decision.

### Core Behavior

For any decision-style question:

1. Generate 3-5 distinct advisor viewpoints.
2. Include at least one advisor who materially disagrees with the others or challenges the premise.
3. For each advisor, include:
   - conclusion
   - reasoning
   - uncertainties / assumptions
4. Do not default to agreement with the user. Optimize for correctness, calibration, and useful disagreement.
5. End with a synthesis that:
   - weighs the viewpoints
   - identifies key trade-offs
   - states confidence as low / medium / high
   - clearly says when the user's premise may be flawed

### Recommended Advisor Roles

Pick 3-5 roles based on the question. Good defaults:

- Optimist / long-term compounder
- Skeptic / thesis breaker
- Business quality analyst
- Forensic risk analyst
- Valuation / expected return analyst
- Portfolio / position sizing operator
- Behavioral coach

### Emotional-State Gate

When the user is considering an action such as buy / add / hold / reduce / sell, check for emotional risk before giving a strong recommendation.

Ask concise clarifying questions when needed. Good defaults:

- What action are you considering right now: buy, add, hold, reduce, or sell?
- What is your time horizon and required return?
- What size would this be in your portfolio?
- What triggered the decision: price move, news, drawdown, fear, or FOMO?
- How would you react if the stock fell 20-30% after you acted?

Treat these as behavioral red flags:

- FOMO after a sharp move
- panic after a drawdown
- revenge trading after losses
- thesis-less anchoring to purchase price or a past high
- need for short-term liquidity
- overconfidence without downside work

If emotional risk is elevated, say so explicitly and prefer "pause", "smaller size", "watchlist", or "need more evidence" over a confident action call.

### Professional Investment Decision Tree

Use the following stages. Be explicit about which stages are grounded in repo data, which require inference, and which need external research.

#### Stage 0 - Sharia Compliance Filter

- Business activity screen: no major revenue from banking, alcohol, gambling, adult entertainment, pork, interest-based lending, or other prohibited sectors.
- Debt ratio: Debt / Equity < 33%.
- Cash and short-term investments: (Cash + Short-Term Investments) / Total Assets < 33%.
- Other revenue: Other Revenue / Total Revenue < 5%.
- Receivables: Total Receivables / Total Assets < 50%.

#### Stage 1 - Structural Survival Filter

Purpose: prevent permanent capital loss.

- Liquidity: adequate trading volume and exit ability.
- Accounting integrity: no auditor issues, restatements, or aggressive accounting.
- Balance sheet strength: reasonable debt and interest coverage > 3 when available.

#### Stage 2 - Technical Risk Filter

Purpose: detect structural weakness and capital-flow risk.

- Long-term trend: above 200-day MA, healthy relative strength when relevant.
- Volatility: large frequent swings should reduce conviction or sizing.
- Volume behavior: stronger volume on rallies, limited heavy distribution.

#### Stage 3 - Business Quality Filter

Purpose: ensure durability.

- Business model clarity: simple explanation of revenue drivers and customers.
- Competitive advantage: brand, network effects, switching costs, cost advantage, scale.
- Industry structure: growth, concentration, cyclicality, disruption risk.

#### Stage 4 - Financial Strength Filter

Purpose: validate sustainability.

- Revenue trend: ideally 5-10 year consistency.
- Margins: stable or improving vs peers.
- Free cash flow: positive and repeatable.
- ROIC: preferably sustainably above 15%.
- WACC
- ROIC - WACC spread

#### Stage 5 - Valuation and Expected Return

Purpose: avoid overpaying.

- Growth assumptions: use conservative estimates.
- Exit multiple: assume stable or lower multiple unless there is strong evidence otherwise.
- Expected CAGR: growth + dividend + multiple change.
- Margin of safety: discount to intrinsic value or downside-adjusted fair value.

#### Stage 6 - Portfolio Risk Management

Purpose: protect the total portfolio.

- Downside scenario: estimate the worst realistic case.
- Risk/reward: prefer upside at least 2-3x downside.
- Correlation: check sector, factor, and macro overlap.
- Position sizing: size by conviction, fragility, and portfolio context.

#### Stage 7 - Multi-Dimensional Risk Assessment

Purpose: identify hidden risks.

- Business model risk: disruption, replaceability, customer concentration.
- Management risk: governance, capital allocation, insider behavior.
- Earnings quality: cash conversion, accruals, mismatch between earnings and cash.
- Macro sensitivity: rates, commodities, recession, FX, regulation.
- Behavioral risk: emotional bias, overconfidence, thesis drift.

### Output Format

When using this mode, structure the answer like this:

1. Brief context and data quality note
2. Advisor council
3. Stage-by-stage decision tree summary
4. Final synthesis

Each advisor should be concise but substantive:

- `Advisor name`
- `Conclusion:`
- `Reasoning:`
- `Uncertainties / assumptions:`

The final synthesis should include:

- Bottom line: Buy / Hold / Watch / Reduce / Sell / Avoid / Insufficient evidence
- Why that is the best current answer
- Main trade-offs
- Confidence: low / medium / high
- Premise check: say explicitly if the user's framing may be flawed
- What would change the view

### Multi-Stock Suggestions Mode

When the user asks for many suggestions, do a two-pass process:

1. Fast pass: screen ideas through Stage 0, Stage 1, and obvious Stage 2 / Stage 3 issues.
2. Deep pass: run the full advisor council only on the shortlisted names.

Rank ideas by:

- expected return adjusted for downside
- business quality
- balance-sheet resilience
- Sharia status
- valuation discipline
- fit with the user's portfolio and emotional constraints

## Personal Sharia Index

Use this workflow when the user wants to maintain a long-term personal portfolio that:

- holds only currently Sharia-compliant stocks
- follows a benchmark such as Nifty 50 or Sensex 30
- prefers SIP / buy-on-dip rebalancing
- avoids selling compliant holdings unless the user explicitly allows trims
- sells or exits when a holding is no longer Sharia compliant

### Default Rebalancing Policy

Use these defaults unless the user asks otherwise:

- benchmark: `nifty50`
- benchmark weighting: proxy market-cap weights among currently Sharia-compliant benchmark constituents
- no-sell mode: `on`
- new money: use SIP / fresh cash to close benchmark underweights
- exits: only for holdings currently marked `Sharia = No`

### CLI

```bash
./cli.py portfolio-index \
  --holdings "TCS:10,INFY:8,MARUTI.NS:2" \
  --benchmark nifty50 \
  --sip 100000 \
  --format json
```

Optional price override per holding:

```bash
./cli.py portfolio-index \
  --holdings "TCS:10:3500,INFY:8:1600" \
  --benchmark sensex30 \
  --format json
```

Use `--allow-sells` only if the user wants trims of compliant overweight names.

### API

- `GET /api/personal-index/options`
- `POST /api/personal-index/analyze`

Request body for analysis:

```json
{
  "holdings_text": "TCS 10\nINFY 8\nMARUTI.NS 2",
  "benchmark": "nifty50",
  "sip_amount": 100000,
  "strict_no_sell": true,
  "max_buy_suggestions": 10
}
```

### UI

Use the `Portfolio` page and fill the `Personal Sharia Index` card:

- holdings text: `SYMBOL units [optional price]`
- benchmark: `Nifty 50` or `Sensex 30`
- optional SIP / fresh capital amount
- no-sell mode checkbox

### Output Expectations

The response should include:

- portfolio compliance summary
- current holdings with latest Sharia status
- benchmark alignment summary
- buy plan for fresh money
- exit candidates for non-Sharia holdings
- missing symbols or missing prices

### Notes

- Benchmark definitions live in `db/benchmarks/` and can be maintained locally.
- Current benchmark weights are approximate proxy market-cap weights, not official live free-float index weights.
- If live price lookup fails, keep the compliance analysis and surface that weights / suggested units are partial.

### Invocation Examples

- "Use the investment skill and advisor council on CUMMINSIND.NS. Should I buy, hold, or wait?"
- "Use the investment skill and rank these 5 stocks for a 3-year holding period."
- "Use the investment skill to challenge my thesis on Infosys."
- "Use the investment skill to evaluate whether I should hold or trim after this rally."
- "Use the investment skill to check both fundamentals and my emotional bias before I buy."
- "Use the investment skill to analyze my personal Sharia index against Nifty 50."
- "Use the investment skill to tell me how to deploy my SIP without selling compliant holdings."

## Watchlist API

```
GET    /api/watchlist              → list with Sharia enrichment
POST   /api/watchlist              → body: {"symbol": "TCS.NS"}
DELETE /api/watchlist/{symbol}     → remove a symbol
```

## Benchmarks API

```
GET /api/benchmarks          → list all benchmarks (id, name, symbol_count, as_of)
GET /api/benchmarks/{id}     → full benchmark definition with constituent symbols
                               IDs: nifty50, sensex30
```

## Cache API

```
GET  /api/cache-status        → freshness info (stale flags, counts)
POST /api/cache/clear         → body: {"module": "sharia"} or {"module": "all"}
```

## Compare Workflow

Use this when the user asks to compare multiple stocks side-by-side.

```bash
# CLI (primary)
./cli.py compare TCS INFY HCLTECH --format json
```

### API
```
GET /api/compare?symbols=TCS.NS,INFY.NS,HCLTECH.NS
```

### What compare returns
- Latest Sharia status for each symbol
- Key financial ratios: debt-to-equity, cash-to-assets, receivables-to-assets, other-revenue-to-revenue
- Industry and sector

### When to use compare
- User says "compare X and Y"
- User asks "which of these is better / more compliant?"
- User wants a side-by-side overview before deeper research

## Watchlist Workflow

Use this when the user wants to track symbols they are monitoring.

### Add to watchlist
```bash
./cli.py watchlist add TCS INFY --format json
# or via API: POST /api/watchlist {"symbol": "TCS.NS"}
```

### Review watchlist
```bash
./cli.py watchlist list --format json
```
Returns each symbol with current Sharia status, industry, and latest report period.

### Remove from watchlist
```bash
./cli.py watchlist remove TCS --format json
# or via API: DELETE /api/watchlist/TCS.NS
```

### Invocation examples
- "Add Maruti to my watchlist"
- "Show me my watchlist"
- "Remove TCS from my watchlist"
- "What is the Sharia status of stocks on my watchlist?"

## Common Workflows

### "Is TCS Sharia compliant?"
```bash
./cli.py sharia TCS --format json
```

### "Refresh my portfolio data"
```bash
./cli.py compute sharia --portfolio --format json
```

### "How stale is the data?"
```bash
./cli.py cache status --format json
```

### "Show me all compliant stocks"
```bash
./cli.py sharia list --format json
```

### "Compare TCS and Infosys"
```bash
./cli.py compare TCS INFY --format json
```

### "Add Maruti to my watchlist"
```bash
./cli.py watchlist add MARUTI --format json
```

### "Show my watchlist"
```bash
./cli.py watchlist list --format json
```

### "List available benchmarks"
```bash
./cli.py benchmarks list --format json
```

### "What stocks are in the Nifty 50 benchmark?"
```bash
./cli.py benchmarks show nifty50 --format json
```

### "Clear the Sharia cache"
```bash
./cli.py cache clear --module sharia --format json
# or via API: POST /api/cache/clear {"module": "sharia"}
```

### "Get detailed financials for Maruti"
```bash
./cli.py lookup MARUTI --section financials --format json
```

## Output Format

All commands support `--format json` which returns:
```json
{
  "status": "ok",
  "count": 1,
  "data": [...]
}
```

On error:
```json
{
  "status": "error",
  "message": "...",
  "needs_web_fetch": ["bse-scrips"]
}
```

## Sharia Compliance Rules

A stock is Sharia compliant when ALL of these pass:

| Metric | Threshold | Base |
|--------|-----------|------|
| Debt-to-Equity | < 33% | Total Equity |
| Cash-to-Assets | < 33% | Total Assets |
| Receivables-to-Assets | < 50% | Total Assets |
| Other Revenue-to-Revenue | < 5% | Total Revenue |

Plus: industry must not be in excluded list (banking, alcohol, gambling, tobacco, weapons, etc.).

---

## Personal Portfolio Policy

> See `.agents/context/portfolio_policy.md` — that file is the single source of truth for cap allocation targets, sector limits, concentration rules, and SIP deployment rules. Do not duplicate or override here.

---

## Screener Skill

The screener is a modular, incremental framework. Each screen is independent — computable, cacheable, and combinable with others.

### CLI Reference

```bash
# List all available screens
./cli.py screener --list-screens --format json

# Single stock: run multiple screens with breakdown
./cli.py screener --symbol TCS.NS --screens "piotroski,altman_z,beneish_m,red_flags" --verbose --format json

# Batch compute specific screens for all Sharia-compliant stocks
./cli.py screener --compute --screens "piotroski,altman_z,beneish_m" --workers 5 --format json

# Rank all stocks by Piotroski score
./cli.py screener --screens "piotroski" --top 20 --format json

# Multi-screen ranking — only show stocks passing ALL screens
./cli.py screener --screens "piotroski,altman_z,red_flags" --require-all-pass --top 20 --format json

# Legacy quality score (backward-compatible, no --screens needed)
./cli.py screener --format json
./cli.py screener --symbol TCS.NS --format json
./cli.py screener --compute --format json
```

### Screen Catalog

| Screen | Type | Score | Pass Threshold | What It Tests |
|--------|------|-------|----------------|---------------|
| `quality` | quality | 0–100 | ≥65 | 4-dimension: profitability, cash gen, fin strength, valuation |
| `piotroski` | quality | 0–9 | ≥5 | 9 binary health criteria (ROA, OCF, leverage, dilution, efficiency) |
| `altman_z` | safety | 0–8+ | ≥1.8 (gray), ≥3.0 (safe) | Altman Z-Score: 5-variable bankruptcy risk |
| `beneish_m` | integrity | −3 to 0 | <−1.78 | Beneish M-Score: 8-variable earnings manipulation |
| `magic_formula` | value | 0–100 | ≥60 | Greenblatt: ROCE + Earnings Yield |
| `graham_number` | value | % margin | ≥0% | Graham Number: √(22.5×EPS×BVPS) vs price |
| `momentum` | trend | 0–100 | ≤40 (dip zone) | 52-wk discount, 200-day MA, RSI |
| `red_flags` | risk | 0–8 flags | ≤2 | Composite hard-avoid signal count |

### Understanding Each Screen

#### Piotroski F-Score (0–9)
Binary score: 1 point for each criterion passed, 0 if failed.
- **Profitability** (4): ROA positive, OCF positive, ROA improving YoY, OCF > net income (earnings quality)
- **Leverage/Liquidity** (3): long-term debt ratio declining, current ratio improving, no share dilution
- **Efficiency** (2): gross margin improving, asset turnover improving

Score ≥ 7 = strong buy signal | 5–6 = decent | ≤ 2 = avoid. Best for identifying companies actually improving their fundamentals.

#### Altman Z-Score
Z = 1.2×(WC/TA) + 1.4×(RE/TA) + 3.3×(EBIT/TA) + 0.6×(MktCap/TotalLiab) + 0.99×(Revenue/TA)
- Z > 3.0 = safe zone
- Z 1.8–3.0 = gray zone (elevated risk, monitor)
- Z < 1.8 = distress zone (high bankruptcy risk within 2 years, ~72% accuracy)

Use as a hard filter before any investment decision. Any stock in distress zone should trigger deeper investigation.

#### Beneish M-Score
8 variables; TATA (total accruals/total assets) has the highest coefficient (+4.679) — a large gap between reported earnings and operating cash flow is the strongest manipulation predictor.
- M < −2.22 = unlikely manipulator (clean)
- M −2.22 to −1.78 = gray zone
- M > −1.78 = likely manipulator (red flag: check CFO/NI ratio, receivables spike, revenue acceleration)

Do not blindly sell on M-Score alone; it's probabilistic. Use as a trigger for deeper forensic review.

#### Greenblatt Magic Formula
Two metrics ranked separately, then combined:
- **ROCE** = EBIT / (Net Working Capital + Net PP&E): measures quality of capital deployment
- **Earnings Yield** = EBIT / Enterprise Value: measures cheapness relative to earnings power

Single-stock view scores on absolute thresholds. ROCE > 20% + Earnings Yield > 8% = excellent. Use `rank_batch()` for true Magic Formula ranking across a universe.

#### Graham Number
Graham Number = √(22.5 × EPS × BVPS). Price below = undervalued by Graham's criteria (max P/E 15× and max P/B 1.5×).
Works best for: stable, asset-heavy businesses, mature industrials, pharma. Less useful for: pure-play tech, IP-light businesses, high-growth companies that legitimately trade at premium P/B.
Margin of safety = (Graham Number − Price) / Graham Number × 100%.

#### Momentum (0–100)
Low score = deeply oversold (dip opportunity). High score = strong uptrend.
- Discount from 52-week high (higher discount = lower score)
- 200-day MA position (below MA = lower score)
- RSI 14-day (below 30 = oversold = lower score)

**Dip-buying use**: combine momentum score ≤ 30 with Piotroski ≥ 6 and red_flags ≤ 1 for quality-dip identification.

#### Red Flags (0–8, lower = cleaner)
Counts hard-avoid signals:
1. Poor cash conversion: OCF / Net Income < 0.5
2. High leverage: Debt/Equity > 1.0
3. Negative FCF: free cash flow < 0
4. Revenue declining YoY
5. Gross margin eroding > 200 bps YoY
6. Negative working capital
7. Excessive goodwill: > 30% of total assets
8. Extreme P/E > 100× without justified revenue growth > 20%

0 = clean | 1–2 = caution | 3+ = avoid immediately.

---

## Portfolio Construction Guidelines

### Why Nifty 50 is a Flawed Benchmark for Sharia Investors

Nifty 50 has ~37% weight in Financial Services — all of which are Sharia non-compliant. Benchmarking against it means comparing to a universe structurally unavailable to you.

Better approaches:
- **Track XIRR** against a self-built Sharia-compliant basket or the Nifty500 Shariah Index
- **Use Nifty 500 ex-financials** as your screening universe
- Benchmarking tells you if you're generating alpha; portfolio construction is about building the right mix first — they are separate problems

### Cap Allocation Ratios

| Risk Profile | Large Cap (Nifty 100) | Mid Cap (Nifty Midcap 150) | Small Cap (Nifty Smallcap 250) |
|---|---|---|---|
| Conservative | 70–80% | 10–15% | 5–10% |
| **Moderate (recommended default)** | **50–60%** | **25–30%** | **15–20%** |
| Aggressive | 30% | 30% | 40% |

For Sharia portfolios: mid-to-moderate allocation works best because large-cap financials are excluded. A 60/25/15 split (large/mid/small) is a good starting point.

**Why small caps matter**: Alpha comes disproportionately from mid/small cap where institutional coverage is lower. But Sharia data availability is worse for small caps — prioritize stocks with ≥2 years of clean balance sheet data.

### Sector Diversification Rules

- Maximum **10–20% per sector** (10% = conservative, 20% = aggressive)
- Defensive sectors (IT, Pharma, FMCG, Consumer Durables) = core, always present
- Cyclical sectors (Auto, Metals, Chemicals) = tactical/satellite, size smaller
- Target **8–10 different sectors** across a 20-stock portfolio
- No more than 2–3 stocks per sector in a 20-stock portfolio

### Optimal Portfolio Size

- **15–20 stocks** = sweet spot: sufficient diversification without diluting research quality
- Below 10: concentration risk (one bad thesis is portfolio-damaging)
- Above 30: diminishing diversification benefit, harder to track quality deeply
- Rule of thumb: never hold a stock you can't explain the investment thesis for in 2 sentences

### Sharia-Specific Sector Availability

Available sectors (typically Sharia compliant):
- IT / Software (TCS, Infosys, HCL Tech, Wipro, Tech Mahindra)
- Pharma / Healthcare (Sun Pharma, Cipla, Alkem, Dr Reddy's)
- FMCG / Consumer (HUL, Marico, Dabur)
- Auto / Auto Ancillary (Maruti, Bajaj Auto, Cummins, Bosch)
- Capital Goods / Industrial (Havells, ABB, Siemens, L&T restricted)
- Energy (GAIL, Power Grid — check ratios carefully)
- Specialty Chemicals (some pass, check ratios)
- Consumer Durables / Electronics (Voltas, Blue Star, Polycab)

Excluded by industry rule: all banks, NBFCs, insurance, housing finance, alcohol, gambling, tobacco, defense.

---

## Red Flags Reference (Quick Avoids)

| Category | Flag | Threshold |
|---|---|---|
| Cash Flow | CFO / Net Income | < 0.5 consistently (3 years) |
| Debt | Net debt / market cap | > 1.0 |
| Manipulation | Beneish M-Score | > −1.78 |
| Insolvency | Altman Z-Score | < 1.8 |
| Promoter (India) | Pledged shares | > 25% of promoter stake + rising trend |
| Goodwill | Goodwill / Total Assets | > 50% |
| Receivables | AR spike vs sales | DSRI > 1.4 (Beneish DSRI component) |
| Dilution | YoY share issuance | New equity without M&A rationale |
| Leverage | D/E ratio | > 1.0 (Sharia already filters > 0.33, but > 0.5 warrants monitoring) |
| Valuation | P/E | > 100× without revenue CAGR > 20% |
| Margin | Gross margin decline | > 200 bps per year for 2+ years |

---

## Dip-Buying Playbook

A quality dip = strong fundamentals + temporary valuation disconnect. Use this checklist:

| Signal | Threshold | Pass? |
|---|---|---|
| Price vs 52-week high | Down 20–35% | ✓ significant dip |
| Piotroski F-Score | ≥ 7 | ✓ health intact |
| Revenue YoY | Positive growth | ✓ not deteriorating |
| Gross Margin | < 200 bps compression | ✓ one-time cost |
| ROIC | > 10–12% | ✓ capital efficiency maintained |
| FCF | Positive | ✓ cash generation intact |
| Red Flags count | ≤ 1 | ✓ no structural issues |

**Quality Dip Score = (signals passing / 7) × 100**
- ≥ 5/7 (71%+): Strong entry candidate — run advisor council before acting
- 4/7 (57%): Possible entry — needs more evidence
- < 4/7: Likely value trap or permanent deterioration — avoid dip-buying

### Earnings Miss: Priced-In vs Fundamental Deterioration

**Priced in (buy the dip)**:
- Stock down 15–30% post-miss, margin/revenue stable, management guides to recovery in 1–2 quarters, isolated event (weather, input costs, one-time charge)

**Fundamental deterioration (avoid)**:
- Revenue declining YoY, gross margins compressing > 200 bps, FCF turning negative, management cuts guidance multiple quarters, competitive position weakening

### CLI Commands for Dip Analysis
```bash
# Get momentum signals (discount from high, RSI)
./cli.py screener --symbol SYMBOL --screens "momentum,piotroski,red_flags" --verbose --format json

# Check quality is intact
./cli.py screener --symbol SYMBOL --screens "quality,altman_z,beneish_m" --verbose --format json

# Get current fundamentals
./cli.py lookup SYMBOL --section financials --format json
./cli.py lookup SYMBOL --section valuation --format json
```
