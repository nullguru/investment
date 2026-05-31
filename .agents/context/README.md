# Agent Context

Persistent investor context that any agent harness should load alongside the skill file.

| File | Purpose | Load when |
|---|---|---|
| `investor_profile.md` | Risk tolerance, horizon, goals, behavioural notes | Always |
| `portfolio_policy.md` | Cap allocation, sector limits, SIP rules | Any investment recommendation |
| `portfolio_holdings.md` | Current holdings with buy prices | Portfolio analysis, rebalancing, gap checks |

## For Agent Wrapper Authors

Add this to your harness-specific skill wrapper:

```
Before doing substantive work, read:
- .agents/skills/investment.md   (skill workflows and CLI reference)
- .agents/context/               (investor profile, portfolio policy, current holdings)
```

The context files are version-controlled in the repo and are the single source of truth.
Do not duplicate their content in harness-specific wrappers.
