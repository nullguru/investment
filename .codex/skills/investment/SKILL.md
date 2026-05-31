---
name: investment
description: Use for investment-platform tasks in this repository: Sharia compliance checks, market and financial lookup, portfolio refreshes, personal Sharia index rebalancing, any-stock buy/hold/sell evaluation, advisor-council idea reviews, and multi-stock investment suggestions. This is a thin Codex wrapper around the canonical shared agent skill at `.agents/skills/investment.md`.
---

# Investment

This skill is intentionally thin. Do not duplicate the operational workflow here.

## Canonical Reference

Before doing substantive work, read:

- `.agents/skills/investment.md` — canonical skill: setup, CLI, workflows, schemas
- `.agents/context/investor_profile.md` — risk tolerance, horizon, behavioural notes
- `.agents/context/portfolio_policy.md` — cap allocation, sector limits, SIP rules
- `.agents/context/portfolio_holdings.md` — current holdings with buy prices

Treat `.agents/` as the single source of truth for all content.
Keep this wrapper lean; update `.agents/` files when anything changes.

## Codex-Specific Guidance

- Prefer the CLI as the primary interface and use `--format json` for structured output.
- Use the FastAPI endpoints when storing or retrieving research sections.
- Keep this wrapper lean; update the shared `.agents` skill when workflow instructions change.

## Repo Nuance

- Universe loading may be empty if NSE/BSE source data is unavailable in the current environment. If that happens, prefer cached Sharia data when possible or follow the import/web-fetch flow documented in `.agents/skills/investment.md`.
