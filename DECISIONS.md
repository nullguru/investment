# Project Decisions

A running log of architectural, design, and product decisions made during development.
Each entry captures the context, the decision, the reasoning, and what was ruled out.
Ordered newest-first.

## When to add an entry

Add an entry when a decision is made that:
- Changes how a major section works (not just a bug fix or style tweak)
- Involves a real tradeoff where the alternative was seriously considered
- Would be confusing to a future developer (or agent) who sees the result without the reasoning
- Involves a user-visible product direction change

Do **not** add entries for: routine bug fixes, dependency updates, UI polish, or anything already explained clearly by the code itself.

## When to read this file

Read before: proposing architectural changes, adding major new features, or answering "why does X work this way." It tells you what was already tried, what was rejected and why, and what the open questions were at each decision point — so you don't re-propose things that were already ruled out.

---

## [2026-06-16] ARCHITECTURE.md consolidated from LAYERS.md

**Context**
`LAYERS.md` at project root contained early-stage architecture docs (written before the build system, MF module, screener, and Recommendations page existed). It was stale and in the wrong location — agents loading context from `.agents/context/` would not find it.

**Decision**
- Created `.agents/context/ARCHITECTURE.md` as the single authoritative architecture document, covering: tech stack, frontend build system, dark theme palette, Alpine/FastAPI conventions, data model, module structure, page list, and pointers to key DECISIONS.md entries.
- `LAYERS.md` replaced with a one-line stub pointing to `ARCHITECTURE.md`.
- `README.md` context table updated to include `ARCHITECTURE.md`.
- Both thin wrapper files (`.claude/skills/investment.md`, `.codex/skills/investment/SKILL.md`) updated to remove the deleted `portfolio_holdings.md` reference and point to `db/settings.json` instead.

**Ruled out**
- Keeping `LAYERS.md` as the live doc: wrong location for agent context, already stale, no enforcement mechanism to keep it current.

---

## [2026-06-16] Agent context: single sources of truth

**Context**
The `.agents/context/` directory had three sources that drifted from each other:
1. `portfolio_holdings.md` — manually maintained holdings table, already missing ADBE
2. `portfolio_policy.md` — sector targets and numeric limits duplicated verbatim from `modules/portfolio/policy.py`
3. `investment.md` — had a full `## Personal Portfolio Policy` section duplicating `portfolio_policy.md`

Any change to a rule required updating up to three files. Drift had already occurred.

**Decision**
Each piece of information has exactly one authoritative source:

| What | Single source | Why there, not elsewhere |
|---|---|---|
| Current holdings & prices | `db/settings.json` → `personalIndexHoldingsText` | This is the live app state; manually maintained .md files will always lag |
| Market overrides (US stocks) | `db/settings.json` → `holdingMarkets` | Same — app writes and reads this directly |
| Numeric policy rules (cap %, sector %, concentration) | `modules/portfolio/policy.py` → `CAP_TARGETS`, `CONCENTRATION`, `SECTOR_TARGETS` | Backend computation uses these constants directly; having them elsewhere creates silent divergence |
| Why rules exist + behavioural rules | `.agents/context/portfolio_policy.md` | Context the code cannot carry — reasoning, growth rule, SIP behaviour, benchmarking rationale |
| Investor goals, risk tolerance, horizon | `.agents/context/investor_profile.md` | Personal context, not derivable from code |
| Architectural decisions | `DECISIONS.md` (this file) | Running log of decisions and rejected alternatives |

**What was removed**
- `portfolio_holdings.md` — deleted; agents should read `db/settings.json` directly
- Duplicate `## Personal Portfolio Policy` section in `investment.md` — replaced with a one-line pointer to `portfolio_policy.md`
- Duplicate numeric tables in `portfolio_policy.md` — replaced with pointers to `policy.py` and a prose section explaining the *why*

**Ruled out**
- Keeping `portfolio_holdings.md` with a sync script: still two sources, sync scripts get skipped
- Making `policy.py` read from `portfolio_policy.md` at runtime: fragile markdown parsing in a financial computation module
- A test asserting `.md` values match `policy.py`: catches drift but doesn't eliminate duplication

---

## [2026-06-16] Advisor Overview page — combined cross-asset view

**Context**
Portfolio tracking was split across two disconnected pages: Portfolio (Indian + US stocks) and MF Holdings (Tata Ethical mutual fund). There was no single view of total wealth, allocation mix, or cross-asset recommendations. The user wanted a combined "advisor" view.

**Decision**
New top-level nav page `advisor` (second in nav, after Home) — a Phase 1 client-side-only aggregation:
- Computes total wealth in INR: Indian stocks + US stocks × USD/INR + MF current value
- Allocation bar and bucket cards: Indian equity / US equity / MF
- Geographic exposure: India % vs US % with 20% FX-risk threshold
- Priority actions: one card per bucket, pulled from existing computed signals (policyAnalysis gaps, mfDiagnosis, nonShariaHoldings)
- Sharia compliance summary across all three buckets (US stocks flagged as unscreened)
- No new backend API calls — all derived from state already loaded by Portfolio and MF pages

Return shown is simple P&L %, not XIRR. Labelled explicitly in the UI. True combined XIRR requires per-date cash flows from the trade ledger — deferred to Phase 2.

**Naming**
The page is named **⬡ Recommendations** (page id `recommendations`, URL hash `#recommendations`). It was briefly called "Advisor" but renamed to avoid confusion with the **Advisor Council** — the multi-viewpoint AI chat workflow defined in `.agents/skills/investment.md`. These are structurally different: Recommendations is a live UI dashboard; Advisor Council is a prompt-driven analysis mode. Keeping distinct names keeps them unambiguous in both conversation and code.

**Ruled out**
- Option A — combined card on Portfolio page: page already dense; MF data is structurally different (no Sharia screen, no per-stock breakdown)
- Option C — merge MF into Portfolio table: incompatible data models (MF is a NAV snapshot, not a stock price row)
- Phase 1 with backend XIRR aggregation: no per-date MF cash flows in the current import; computing a fake XIRR would be misleading

**Open questions for Phase 2**
- Expose per-instalment MF SIP dates via a richer import format (CAMS/Karvy statement)
- Compute true combined XIRR via a new `/api/portfolio/combined-xirr` endpoint
- US stocks Sharia screen: surface a warning to verify via Musaffa

---

## [2026-06-16] MF Fund Diagnosis section

**Context**
The MF Holdings page showed raw numbers (invested, current, XIRR) but no interpretation. The user asked for a recommendation section similar to the Portfolio Diagnosis pattern — should they continue SIP, add a lumpsum, hold, or exit?

**Decision**
Added a `mfDiagnosis()` computed function and a "Fund Diagnosis" section below the holdings table. Fully client-side — no new API. Signals derived from data already in `mfHoldings`:

- **XIRR vs 6% inflation** — primary health signal
- **NAV vs avg cost** (`current_value/units` vs `invested_value/units`) — detects rupee cost averaging opportunity when NAV is below avg buy price
- **Drawdown depth** — absolute return from cost basis
- **Sharia scarcity note** — detected by `/ethical|sharia/i` match on scheme name; exit bar is high given <10 Sharia equity funds in India
- **Thematic concentration warning** — detected from `sub_category`

Verdict thresholds: XIRR ≥ 6% → Continue; NAV below cost + XIRR ≥ −15% → Continue + Consider Lumpsum; XIRR ≥ −10% → Monitor; XIRR ≥ −20% → Hold; else → Pause & Review.

Includes a collapsible "Why these signals?" section explaining all six MF principles inline, so the user can build intuition without needing an external source.

**Ruled out**
- Backend API with NAV history: NAV history is not in the current Groww XLSX export; adding it requires a different data source (MFI API or CAMS statement)
- Per-folio verdict: both folios are the same scheme; a grouped view is more meaningful

---

## [2026-06-16] Recommendation system overhaul — scope & approach

**Context**
The "If I Deploy New Money — What Should I Buy?" section was built around a single logic:
find which Nifty 50 Sharia-compliant stocks you are most underweight relative to their
benchmark weight, and surface those as buy candidates. The only technical signal was
vs200DMA used as a dip flag.

**Problems identified**
1. Universe is artificially capped at ~50 large-cap stocks. Mid/small caps are invisible.
2. The gap analysis conflates two different problems: sector underexposure and
   single-stock underexposure. These have different solutions.
3. Non-compliant and unknown-compliance candidates are completely hidden, making it
   impossible to know whether a Sharia-compliant option even exists for a given gap.
4. "Before vs Recommended" (diagnosis) and "Deploy New Money" (prescription) use
   different gap calculations, so they can point in different directions. The three
   portfolio sub-sections (Theory → Diagnosis → Prescription) are logically adjacent
   but not functionally connected.

**Decision**
Rebuild the recommendation engine in two layers:

*Layer 1 — Gap diagnosis (structural)*
- Identify sector gaps: current portfolio sector weights vs a reference (Nifty 500
  sector weights, not Nifty 50 — less distorted by IT concentration)
- Identify cap tier gaps: current large/mid/small mix vs a user-configurable target
  (default 60/25/15). These two axes are independent.

*Layer 2 — Candidates per gap (universe-wide)*
- Pull all stocks from the Sharia cache (full universe, not just benchmark members)
- Classify by cap tier using market cap thresholds (large > ₹20K Cr, mid ₹5K–20K Cr,
  small < ₹5K Cr — Indian market convention)
- For each identified gap, surface top candidates tagged by Sharia status:
  - Green = Compliant
  - Red = Non-Compliant
  - Amber = Unknown (often missing data, not necessarily a red flag — shown with a note)
- Within compliant candidates, use technical factors (vs200DMA, momentum, RSI distance)
  as entry-timing tiebreakers only — not as the primary ranking signal
- Show multiple candidates per gap (not just one)

*UI structure*
- Gap Diagnosis panel: sector mix chart + cap tier mix chart, highlights top 2–3 gaps
- Candidates by Gap: expandable per-gap candidate lists with Sharia tags + technicals
- Keep the existing Nifty 50 underweight view as a separate tab for users who want
  pure index-replication behaviour

**Ruled out**
- Ranking candidates primarily by technical factors: large-cap Indian stocks, short-term
  technicals are weak predictors; would mislead users into buying the "technically nicer"
  stock that doesn't address the actual portfolio gap
- Removing the Nifty 50 benchmark view: still valid for strict index replication intent,
  just shouldn't be the only view

**Open questions before implementation**
- Sector reference weights: Nifty 500 sector composition, or user-defined targets?
- Cap tier target allocation: hardcoded default (60/25/15) or a settings field?
- How noisy will "unknown" tags be for small caps? May need a minimum data-quality
  threshold before surfacing a candidate at all.

---

## [2026-06-16] MF Holdings section added

**Context**
Portfolio tracking only covered equity trades from the Zerodha/Groww order history XLSX.
Mutual fund holdings (also via Groww) were a separate export with a different format:
a snapshot of units, invested value, current value, XIRR per folio — not a trade log.

**Decision**
Treat MF holdings as a separate snapshot entity (not merged into the trade ledger).
- New module: `modules/trades/mf_importer.py` — parses the Groww MF XLSX and stores
  to `db/mf_holdings.json`
- Three new API endpoints: GET /api/mf/holdings, POST /api/mf/import, POST /api/mf/upload
- New "MF Holdings" nav page with summary cards (invested, current, P&L, XIRR) and
  a per-folio holdings table
- Re-import and file-upload buttons for keeping the snapshot current

**Ruled out**
- Merging MF folios into the trade ledger: the data model is incompatible (no
  per-trade history in the export, only current snapshot state)

---

## [2026-06-15] Broker order history importer

**Context**
Trades were entered manually. A Zerodha/Groww equity order history XLSX export existed
with full executed order history.

**Decision**
- Importer reads from `raw_data/Stocks_Order_History_*.xlsx`, skipping 4 header rows
- Deduplication via `exchange_order_id` stored in `_import_meta` on each trade
- Always uses `.NS` suffix regardless of whether the execution was on NSE or BSE —
  yfinance canonical ticker must be consistent for AVCO position tracking
- Preview endpoint returns rows without writing, allowing UI review before committing

**Ruled out**
- Separate NSE/BSE ticker tracking: creates split positions for the same security

---

## [2026-05-xx] Portfolio page three-section structure

**Context**
The portfolio page needed to serve multiple purposes: education, diagnosis, prescription.

**Decision**
Three sequential sub-sections on one page:
1. Portfolio Theory — static educational content (MPT, diversification rules)
2. Your Portfolio — Before vs Recommended — diagnostic, reads live holdings
3. If I Deploy New Money — What Should I Buy? — prescriptive, uses benchmark gaps

**Known limitation recorded at time of decision**
Sections 2 and 3 are logically adjacent but not functionally connected — they use
different gap calculations. Accepted as a first-version tradeoff. Flagged for fixing
in the recommendation system overhaul (see 2026-06-16 entry above).
