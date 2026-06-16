# System Architecture

Authoritative technical reference. Read before implementing features, adding pages, or changing data flow. Supersedes `LAYERS.md` (which now points here).

---

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (`backend/main.py`) — all `/api/*` endpoints, serves the SPA |
| Frontend | Alpine.js SPA, Tailwind CSS (CDN), hash routing (`#page-id`) |
| Frontend build | `frontend/build.py` assembles `index.html` from fragments (see below) |
| Data store | JSON files in `db/` — no database |
| Market data | yfinance via `modules/market/yf.py` |
| CLI | `cli.py` — argparse, `--format json|table|csv`, all module commands |

---

## Frontend build system

`frontend/index.html` is **compiled output** — never edit it directly. The real sources are:

```
frontend/
  shell.html          — <head>, navbar, sidebar, main wrapper skeleton
  pages/*.html        — one file per page (includes the outer x-show div)
  js/app.js           — full Alpine app() function: all state + methods
  build.py            — assembles shell + pages + app.js → index.html
```

**To add a page:**
1. Create `frontend/pages/mypage.html` with `<div x-show="page === 'mypage'" ...>`
2. Add `'mypage'` to `PAGES` list in `build.py`
3. Add `mypage: 'Label'` to `navCards` in `js/app.js`
4. Run `python frontend/build.py`

**Never edit `index.html` directly** — changes are overwritten on the next build.

---

## Frontend conventions

### Page structure
Every page is an `x-show` div. Pattern:
```html
<div x-show="page === 'mypage'" x-cloak class="space-y-6">
  ...
</div>
```

### Dark theme palette (use these, not light-mode equivalents)
| Purpose | Class |
|---|---|
| Card background | `bg-slate-800/40` |
| Card border | `border border-slate-700` |
| Section heading | `text-slate-100` |
| Body text | `text-slate-300` |
| Secondary / label | `text-slate-400` |
| Muted / hint | `text-slate-500` |
| Progress bar track | `bg-slate-700` |
| Amber signal bg | `bg-amber-900/20 border-amber-700/30` |
| Emerald signal bg | `bg-emerald-900/20 border-emerald-700/30` |
| Rose signal bg | `bg-rose-900/20 border-rose-700/30` |
| Blue signal bg | `bg-blue-900/20 border-blue-700/30` |
| Amber signal text | `text-amber-300` |
| Emerald signal text | `text-emerald-300` |
| Rose signal text | `text-rose-300` |

### Alpine state
All app state is declared at the top of `app.js` in the `Alpine.data('app', () => ({ ... }))` block. Add new state fields there. To add a computed function, place it near related functions (e.g. `advisorData()` lives after `mfGroupedHoldings()`).

### Data fetching pattern
```js
async fetchX() {
  this.xLoading = true; this.xError = '';
  try {
    const d = await fetch(API + '/x').then(r => r.json());
    this.xData = d.result || [];
  } catch(e) { this.xError = e.message; }
  finally { this.xLoading = false; }
},
```

### onPageChange
Add a branch for each page that needs data fetched on entry:
```js
else if (this.page === 'mypage') {
  if (!this.myData.length) this.fetchMyData();
}
```

---

## Backend conventions

### Settings persistence
`db/settings.json` is read/written via `_load_settings()` / `_save_settings()` in `backend/main.py`. The pattern requires two places to stay in sync:

```python
DEFAULT_SETTINGS = {
  "myField": defaultValue,   # ← add here
  ...
}

class SettingsBody(BaseModel):
  myField: type = defaultValue  # ← and here
```

**If you add a setting and only update one of these, `saveSettings()` from the frontend will silently drop the field.** This was the root cause of `holdingMarkets` not persisting (fixed June 2026).

### API response format
All endpoints return snake_case JSON. Alpine templates that consume these must not assume camelCase.

---

## Data model (`db/`)

| File | Contents | Written by |
|---|---|---|
| `settings.json` | App settings + **live holdings** (`personalIndexHoldingsText`: `SYMBOL units [avg_price]` per line), `holdingMarkets` (US overrides) | Frontend via `PUT /api/settings` |
| `trades.json` | Full trade ledger (buy/sell history) | Order history importer + manual entry |
| `mf_holdings.json` | MF snapshot (units, NAV, XIRR per folio) | Groww XLSX import via `POST /api/mf/upload` |
| `sharia_cache/` | Per-symbol Sharia compliance results (Parquet) | `modules/sharia/service.py` |
| `benchmarks/` | Nifty 50, Sensex 30 constituent lists | Static, maintained manually |
| `research/` | Per-symbol research JSON (8 sections) | Agent research workflow via `PUT /api/symbol/.../research/...` |
| `field_gaps.json` | Symbols with missing yfinance fields | Populated during Sharia compute |

---

## Module structure (`modules/`)

```
modules/
  sharia/         — Sharia compliance: filter.py (ratios), service.py (batch), data.py (cache/enrichment)
  universe/       — Ticker lists: indian.py (NSE+BSE), cap_tier.py (large/mid/small classification)
  market/         — Market data: yf.py (Yahoo Finance sections: overview, market, financials, valuation)
  portfolio/      — Portfolio analysis:
                      policy.py       (gap analysis vs sector/cap targets — authoritative policy constants)
                      scenarios.py    (deployment scenario engine: replace non-Sharia, fill gaps, top up)
  trades/         — Trade data:
                      importer.py     (Zerodha/Groww order history XLSX → trades.json, dedup by exchange_order_id)
                      mf_importer.py  (Groww MF XLSX → mf_holdings.json)
  lenses/         — Lens library (composite, thematic, ideas, custom)
  quality.py      — Legacy quality scoring
  research.py     — Per-symbol research section storage/retrieval
  screener/       — Modular screener: piotroski, altman_z, beneish_m, magic_formula, graham_number, momentum, red_flags
```

---

## Pages (current)

| Page id | File | What it does |
|---|---|---|
| `home` | `pages/home.html` | Dashboard, cache status, quick links |
| `recommendations` | `pages/recommendations.html` | Combined wealth view — IN/US/MF allocation, Stocks vs MF and IN vs US advice, priority actions |
| `all_stocks` | `pages/all_stocks.html` | Full universe table with Sharia + quality filters |
| `per_stock` | `pages/per_stock.html` | Single-stock deep dive — 8-section research, screener scores, Sharia detail |
| `comparison` | `pages/comparison.html` | Side-by-side multi-stock comparison |
| `portfolio` | `pages/portfolio.html` | Personal Sharia Index — holdings, benchmark gap diagnosis, deployment scenarios |
| `trades` | `pages/trades.html` | Trade journal — ledger, positions, P&L |
| `mf` | `pages/mf.html` | MF Holdings — snapshot, Fund Diagnosis (SIP/lumpsum/hold recommendation) |
| `lenses` | `pages/lenses.html` | Lens Library — composite/thematic/ideas/custom screens |
| `watchlist` | `pages/watchlist.html` | Watchlist with live Sharia enrichment |

---

## Key architectural decisions

See `DECISIONS.md` for the full log. High-signal entries:
- **MF as separate snapshot entity** (not merged into trade ledger) — June 2026
- **Recommendations page as Phase 1 client-side aggregation** — June 2026
- **`holdingMarkets` as source of truth for US/IN classification** — June 2026
- **`policy.py` constants as single source for portfolio rules** — June 2026
- **`db/settings.json` as live source for current holdings** — June 2026
