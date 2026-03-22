# TOP 3 BEARISH MONTHLY STRATEGIES — Final Selection
## Run ID: run_20032026 | Date: 2026-03-20
## Expiry: March 31, 2026 (Tuesday) | India VIX: 22.09 (HIGH)
## Pipeline: Lead > ScoutLeaders > 4 Scouts > Orchestrator > Verifier > Final Synthesis
## Selection Criteria: Score >= 70/110, SEBI Compliant, IV Regime Aligned

---

## #1: Nifty Bearish Jade Lizard (Zero Upside Risk) — Score: 80/110

**Verdict:** STRONG PASS — Essential portfolio hedge | Unique zero-upside-risk property

### Structure
- **Sell 1x** Nifty 22,500 PE (OTM) — monthly Mar 31
- **Sell 1x** Nifty 23,800 CE (OTM) — monthly Mar 31
- **Buy 1x** Nifty 24,000 CE (wing) — monthly Mar 31
- **Net Credit:** Rs 7,930 (122 pts x 65)
- **Max Profit Upside:** Rs 1,430 (even at Nifty 24,000+) — ZERO RISK on rally
- **Max Profit Downside:** Rs 7,930 (full credit) if 22,500 < Nifty < 23,800
- **Max Loss:** Unlimited below 22,500 (naked put) — requires stop

### Edge Thesis
**The ONLY bearish strategy with ZERO upside risk.** In a geopolitical environment with ceasefire uncertainty, this is invaluable. Even if Iran-Israel resolves and market rallies 5%, this position STILL PROFITS Rs 1,430. The naked put risk is the only concern — manageable with stops.

### Greeks Profile
| Greek | Value | Assessment |
|-------|-------|------------|
| Delta | -0.17 | Mild bearish |
| Gamma | -0.015 | Mild |
| Vega | -2.8 | Benefits from VIX normalization |
| Theta | +Rs 780/day | Strong |

### Key Risk
Naked put at 22,500. In a market moving 500-750 pts/day, 22,500 is reachable. Stop at 22,700 limits loss to ~Rs 5,000. Gap below stop could be catastrophic.

### Rubric Breakdown
| Dimension | Score |
|-----------|-------|
| Edge Clarity | 9 |
| Entry Precision | 7 |
| Exit Discipline | 7 |
| Risk-Reward | 6 |
| Liquidity Feasibility | 7 |
| Historical Evidence | 5 |
| IV Regime Alignment | 8 |
| Regulatory Compliance | 10 |
| Capital Efficiency | 5 |
| Failure Mode Resilience | 9 |
| Greeks Robustness | 7 |
| **Raw: 80** | **Deductions: 0** |

---

## #2: Bank Nifty Bear Call Credit Spread — Score: 75/110

**Verdict:** PASS — Reliable income strategy | Best as portfolio component

### Structure
- **Sell 1x** Bank Nifty 55,000 CE (OTM) — monthly Mar 31
- **Buy 1x** Bank Nifty 55,500 CE (wing) — monthly Mar 31
- **Net Credit:** Rs 4,200 (140 pts x 30)
- **Max Loss:** Rs 10,800 (360 pts x 30)
- **Max Profit:** Rs 4,200 (full credit)
- **Probability of Profit:** >75%

### Edge Thesis
Simplest, most reliable structure. 2.9% buffer to short strike with 11 DTE. Oil-to-banking transmission channel: rising oil prices squeeze Bank margins, creating structural headwind. Theta-driven income with >75% POP. Defined risk.

### Greeks Profile
| Greek | Value | Assessment |
|-------|-------|------------|
| Delta | -0.12 | Mild bearish |
| Gamma | -0.003 | Very mild |
| Vega | -1.8 | Benefits from VIX normalization |
| Theta | +Rs 300/day | Strong and consistent |

### Key Risk
1:0.39 risk-reward requires 72%+ win rate to break even after costs. A single BankNifty 4%+ rally causes max loss (Rs 10,800), wiping 2.6 winning trades.

### Rubric Breakdown
| Dimension | Score |
|-----------|-------|
| Edge Clarity | 7 |
| Entry Precision | 7 |
| Exit Discipline | 7 |
| Risk-Reward | 4 |
| Liquidity Feasibility | 7 |
| Historical Evidence | 6 |
| IV Regime Alignment | 7 |
| Regulatory Compliance | 10 |
| Capital Efficiency | 6 |
| Failure Mode Resilience | 7 |
| Greeks Robustness | 7 |
| **Raw: 75** | **Deductions: 0** |

---

## #3: Nifty Bearish Put Ladder — Score: 71/110

**Verdict:** PASS — Good staircase play | Active management required

### Structure
- **Buy 1x** Nifty 23,100 PE (ATM) — monthly Mar 31
- **Sell 1x** Nifty 22,500 PE — monthly Mar 31
- **Sell 1x** Nifty 22,000 PE — monthly Mar 31
- **Net Debit:** ~Rs 11,180 (172 pts x 65)
- **Max Profit:** Rs 26,000 (400 pts x 65) at 22,000-22,500 zone
- **Max Loss Upside:** Rs 11,180 (debit) above 23,100
- **Danger Zone:** Below 21,415 — naked put exposure begins
- **R:R:** 2.2:1 on upside risk

### Edge Thesis
1,500-pt profit zone maps to the staircase support structure (23,100 → 22,500 → 22,000). Strong theta (+Rs 910/day) while waiting. Benefits from VIX normalization (short vega). Targets the "measured decline" thesis — orderly selling to support levels.

### Greeks Profile
| Greek | Value | Assessment |
|-------|-------|------------|
| Delta | -0.35 | Moderately strong bearish |
| Gamma | -0.015 | Mild from 2 sold options |
| Vega | -2.8 | Benefits from IV contraction |
| Theta | +Rs 910/day | Strong |

### Key Risk
Naked 22,000 put below 21,415 creates unlimited loss. In the current crash environment (3.26% daily moves), a continued 7.3% decline is extreme but NOT impossible over 11 DTE. Mandatory adjustment protocol if Nifty approaches 22,200.

### Rubric Breakdown
| Dimension | Score |
|-----------|-------|
| Edge Clarity | 7 |
| Entry Precision | 6 |
| Exit Discipline | 6 |
| Risk-Reward | 7 |
| Liquidity Feasibility | 7 |
| Historical Evidence | 5 |
| IV Regime Alignment | 7 |
| Regulatory Compliance | 10 |
| Capital Efficiency | 5 |
| Failure Mode Resilience | 5 |
| Greeks Robustness | 6 |
| **Raw: 71** | **Deductions: 0** |

---

## Portfolio Correlation Check
- **M-4 (Jade Lizard)** vs **M-1 (Bear Call):** LOW correlation. Different underlyings (Nifty vs BankNifty), different structures. M-4's zero-upside-risk complements M-1's pure credit collection.
- **M-4 (Jade Lizard)** vs **M-5 (Put Ladder):** MODERATE correlation. Both bearish on Nifty. But M-4 profits on rally (unique), M-5 loses on rally. Natural diversification on rally scenario.
- **M-1 (Bear Call)** vs **M-5 (Put Ladder):** LOW correlation. Different underlyings, different structures. Independent risk profiles.
- **All 3 together:** Excellent diversification — Nifty + BankNifty exposure, 3 different structures, mixed upside scenarios.

## IV Regime Suitability
All 3 strategies are SHORT VEGA — all benefit from VIX normalization from 22.09 toward 15-18. Consensus position: VIX contraction is the base case for the next 11 days.

## Key Monthly Insight
**Zero-upside-risk (M-4 Jade Lizard) is the standout innovation in the bearish monthly portfolio.** In a geopolitical environment where ceasefire news could cause sudden rallies, having a bearish strategy that still profits on rallies is uniquely valuable. This should be the ANCHOR of any bearish monthly portfolio.
