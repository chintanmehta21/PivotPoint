# PivotPoint Strategy Guide

## Strategy Inventory

14 strategies across 6 categories (bullish/bearish × weekly/monthly/quarterly).
All strategies target Indian equity indices (Nifty 50, Bank Nifty) options on NSE.

### Bullish Strategies (6)

| ID | Name | Timeframe | Score | Legs | Key Feature |
|----|------|-----------|-------|------|-------------|
| BW1 | Call Ratio Backspread 1:2 | Weekly | 72/110 | 3 | Net credit, unlimited upside |
| BW2 | Supertrend Bull Call Spread | Weekly | 70/110 | 2 | Signal-driven, vega-neutral |
| BM1 | Modified Butterfly | Monthly | 78/110 | 4 | 4:1 R:R, short vega |
| BM2 | Bullish Diagonal Calendar | Monthly | 71/110 | 2+rolls | Triple-positive Greeks |
| BQ1 | Bullish-Adjusted Iron Fly | Quarterly | 76/110 | 6 (2-phase) | Neutral→bullish adjustment |
| BQ2 | Broken Wing Call Butterfly | Quarterly | 74/110 | 4 | Asymmetric payoff, cheap wing |

### Bearish Strategies (8)

| ID | Name | Timeframe | Score | Legs | Key Feature |
|----|------|-----------|-------|------|-------------|
| BrW1 | Bearish Diagonal/Calendar Put | Weekly | 82/110 | 2+rolls | Long vega, crisis hedge |
| BrW2 | Put Ratio Backspread | Weekly | 78/110 | 3 | Crash hedge, net credit |
| BrW3 | Bearish Broken-Wing Put Butterfly | Weekly | 73/110 | 4 | Skew harvest, pin strategy |
| BrM1 | Bearish Jade Lizard | Monthly | 80/110 | 3 | Zero upside risk |
| BrM2 | Bank Nifty Bear Call Credit Spread | Monthly | 75/110 | 2 | >75% POP, defined risk |
| BrM3 | Bearish Put Ladder | Monthly | 71/110 | 3 | Staircase support targets |
| BrQ1 | Skip-Strike Bearish Put Butterfly | Quarterly | 92/110 | 4 | No downside loss, guaranteed floor |
| BrQ2 | Bear Put Condor — Adaptive Bear | Quarterly | 87/110 | 4 | Absolute loss cap both sides |

## Top Performers

1. **BrQ1 (92/110)** — Skip-Strike Bearish Put Butterfly: Mathematically superior, no loss on any downside scenario
2. **BrQ2 (87/110)** — Bear Put Condor: Safest strategy, absolute loss cap in ALL scenarios
3. **BrW1 (82/110)** — Bearish Diagonal Calendar Put: Only weekly strategy with long vega (crisis hedge)
4. **BrM1 (80/110)** — Bearish Jade Lizard: Zero upside risk — profits even on rally

## IV Regime Suitability

| Strategy | Vega | VIX Spike | VIX Crush | Best Regime |
|----------|------|-----------|-----------|-------------|
| BW1 | Net long | Benefits | Hurts | HIGH VIX entry |
| BM1 | Net short | Hurts | Benefits | HIGH→LOW transition |
| BrW1 | Net long | Benefits | Hurts | Crisis/escalation |
| BrQ1 | Mild short | Minor | Minor | Any (structural edge) |

## Scoring Rubric (110 points)

| Dimension | Max Points |
|-----------|-----------|
| Edge Clarity | 10 |
| Entry Precision | 10 |
| Exit Discipline | 10 |
| Risk-Reward | 10 |
| Liquidity Feasibility | 10 |
| Historical Evidence | 10 |
| IV Regime Alignment | 10 |
| Regulatory Compliance | 10 |
| Capital Efficiency | 10 |
| Failure Mode Resilience | 10 |
| Greeks Robustness | 10 |

## Adding New Strategies

See `docs/v0/architecture.md` for the step-by-step process.

## Source Research

Original strategy research files are preserved in `.init/strategies_v1/` for reference.
