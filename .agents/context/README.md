# Agent Context

Persistent investor context that any agent harness should load alongside the skill file.

| File | Purpose | Load when |
|---|---|---|
| `investor_profile.md` | Risk tolerance, horizon, goals, behavioural notes | Always |
| `portfolio_policy.md` | **Why** the rules exist + behavioural rules (growth rule, benchmarking, SIP). Numeric constants live in `modules/portfolio/policy.py` — that is the single authoritative source the UI and backend compute from. | Any investment recommendation |
| `ARCHITECTURE.md` | Tech stack, build system, frontend conventions, backend patterns, data model, page list | Before implementing features, adding pages, or changing data flow |
| `../../../db/settings.json` | **Live source of truth** for current holdings (`personalIndexHoldingsText`: `SYMBOL units [avg_price]` per line), market overrides (`holdingMarkets`), and app settings | Portfolio analysis, rebalancing, gap checks — read this, not any .md file |
| `../../../DECISIONS.md` | Architectural and product decisions with reasoning and rejected alternatives | Before proposing structural changes, adding new sections, or when the user asks "why does X work this way" |

## For Agent Wrapper Authors

Add this to your harness-specific skill wrapper:

```
Before doing substantive work, read:
- .agents/skills/investment.md   (skill workflows and CLI reference)
- .agents/context/               (investor profile, portfolio policy, current holdings)
```

The context files are version-controlled in the repo and are the single source of truth.
Do not duplicate their content in harness-specific wrappers.
