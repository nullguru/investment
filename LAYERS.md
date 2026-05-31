# Architecture

The platform has four interfaces sharing the same domain logic:

```
Shared Agent Skill (.agents/skills/investment.md)
  ↑ thin wrappers in .claude/skills/investment.md and .codex/skills/investment/SKILL.md
  ↓ calls CLI via Bash
CLI (cli.py)  ←→  FastAPI (backend/main.py)  ←→  Web UI (frontend/)
  ↓                    ↓
modules/ (domain logic)
  ↓
core/ (config, cache, output)
```

## Layers

### `core/` — Domain-agnostic infrastructure
- `config.py` — Project paths, env overrides (`FIN_CACHE_PATH`, `FIN_DB_PATH`, etc.)
- `cache.py` — Parquet I/O, `cache/meta.json` staleness tracking
- `output.py` — CLI output formatting (JSON, table, CSV)

### `modules/` — Domain modules
Each module is self-contained with its own data, computation, and service logic.

- **`modules/sharia/`** — Sharia compliance screening
  - `filter.py` — Fetches yfinance data, computes 4 ratios, thresholds, industry exclusion
  - `service.py` — Batch computation wrapper with parallel fetching
  - `data.py` — Sharia cache, column definitions, enrichment, portfolio helpers
- **`modules/universe/`** — Ticker management
  - `indian.py` — NSE (nsetools) + BSE (CSV) combined universe
  - Future: `us.py` for US market
- **`modules/market/`** — Market data providers
  - `yf.py` — Yahoo Finance sections (overview, market, financials, valuation)
- **`modules/portfolio/`** — Portfolio analysis (placeholder for expansion)

### `backend/` — FastAPI REST API
- `main.py` — All `/api/*` endpoints, serves SPA from `frontend/`
- Imports from `modules/` and `core/`

### `frontend/` — Web UI
- `index.html` — Tailwind CSS + Alpine.js SPA with hash routing

### `cli.py` — CLI entry point
- Single file with argparse subcommands
- Commands: `universe`, `sharia`, `compute`, `lookup`, `compare`, `cache`, `import`, `serve`
- `--format json|table|csv` for all commands

### `.agents/skills/investment.md` — Shared agent skill
- Canonical workflow shared by agent runtimes
- Documents CLI usage, web fetch protocol, and research workflow

### `.claude/skills/investment.md` / `.codex/skills/investment/SKILL.md` — Thin wrappers
- Platform-specific entrypoints that refer to the shared `.agents` skill

## Dependency flow

```
CLI / FastAPI
  → modules/sharia (filter, service, data)
  → modules/universe (indian tickers)
  → modules/market (yfinance)
  → core/config (paths)
  → core/cache (parquet, meta.json)
```

## File layout

```
cli.py                            # CLI entry point
core/config.py                    # Paths, env vars
core/cache.py                     # Parquet I/O, meta.json
core/output.py                    # JSON/table/CSV formatting
modules/sharia/                   # Sharia compliance screening
modules/universe/                 # Ticker management (Indian, future US)
modules/market/                   # Market data providers (Yahoo Finance)
modules/portfolio/                # Portfolio analysis (placeholder)
backend/main.py                   # FastAPI REST API
frontend/index.html               # Tailwind + Alpine.js SPA
.agents/skills/investment.md      # Shared agent skill definition
.claude/skills/investment.md      # Claude wrapper
.codex/skills/investment/SKILL.md # Codex wrapper
```
