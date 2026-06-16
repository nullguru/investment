---
name: investment
description: Investment analysis platform and decision framework — stock screening (Sharia compliance), market data, portfolio analysis, personal Sharia index rebalancing, buy/hold/sell evaluation, any-stock idea review, and multi-advisor investment suggestions for Indian/US stocks.
---

# Investment Platform Skill

This is a thin Claude wrapper.

Before doing substantive work, read:

- `.agents/skills/investment.md` — canonical skill: setup, CLI, workflows, schemas
- `.agents/context/investor_profile.md` — risk tolerance, horizon, behavioural notes
- `.agents/context/portfolio_policy.md` — cap allocation, sector limits, SIP rules
- `db/settings.json` — live holdings (`personalIndexHoldingsText`) and market overrides (`holdingMarkets`)

Treat `.agents/` as the single source of truth. Keep this wrapper lean.
Update `.agents/` files instead of duplicating instructions here.
