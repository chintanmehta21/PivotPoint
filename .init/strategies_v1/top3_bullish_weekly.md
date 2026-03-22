# TOP 3 BULLISH WEEKLY STRATEGIES — Final Selection
## Run ID: run_20032026 | Date: 2026-03-20
## Expiry: March 24, 2026 (Tuesday) | India VIX: 22.09 (HIGH)
## Pipeline: Lead > ScoutLeaders > 4 Scouts > Orchestrator > Verifier > Final Synthesis
## Selection Criteria: Score >= 70/110, SEBI Compliant, IV Regime Aligned

---

> **[INSUFFICIENT_STRATEGIES — 2 of 3 available]**
> Only 2 strategies passed the 70/110 threshold. 5 of 7 weekly bullish strategies failed — 4 due to SEBI weekly expiry rationalization (BankNifty/Midcap weekly availability uncertain), 1 due to IV mismatch. Do NOT pad with unvalidated strategies.

---

## #1: Nifty Call Ratio Backspread 1:2 — Score: 72/110

**Verdict:** PASS — Moderate-High Confidence

### Structure
- **Sell 1x** Nifty 23,100 CE (ATM) — weekly Mar 24
- **Buy 2x** Nifty 23,300 CE (OTM) — weekly Mar 24
- **Net Credit:** ~Rs 7,800 (120 pts x 65)
- **Max Loss:** Rs 11,700 at 23,300 (Max Pain pin)
- **Max Profit:** Unlimited above 23,500; Rs 7,800 below 23,100

### Edge Thesis
Net credit entry in HIGH VIX creates asymmetric payoff: profits in 2 of 3 scenarios (rally = unlimited upside, decline = credit retained). Only loses at exact Max Pain pin at 23,300 — low probability but highest-risk zone.

### Greeks Profile
| Greek | Value | Assessment |
|-------|-------|------------|
| Delta | +0.30 to +0.50 | Accelerates on rally |
| Gamma | HIGH at 23,300 | Risk at max-loss zone, benefit above |
| Vega | Net long (de minimis at 2 DTE) | LOW impact |
| Theta | +Rs 300-500/day (credit) | Favorable |

### Key Risk
Max Pain at 23,300 = max loss zone. Market makers may pin near this level on expiry day.

### Rubric Breakdown
| Dimension | Score |
|-----------|-------|
| Edge Clarity | 8 |
| Entry Precision | 7 |
| Exit Discipline | 7 |
| Risk-Reward | 8 |
| Liquidity Feasibility | 9 |
| Historical Evidence | 5 |
| IV Regime Alignment | 9 |
| Regulatory Compliance | 10 |
| Capital Efficiency | 7 |
| Failure Mode Resilience | 5 |
| Greeks Robustness | 7 |
| **Raw: 82** | **Deductions: -10** |

---

## #2: Nifty Supertrend Bull Call Spread — Score: 70/110

**Verdict:** PASS — Moderate Confidence

### Structure
- **Buy 1x** Nifty ATM CE — weekly Mar 24
- **Sell 1x** Nifty ATM+300 CE — weekly Mar 24
- **Net Debit:** ~Rs 5,850 (90 pts x 65)
- **Max Loss:** Rs 5,850 (defined)
- **Max Profit:** Rs 13,650 (210 pts x 65)
- **R:R:** 2.33:1

### Edge Thesis
Supertrend indicator (10,3) on 15-min chart provides mechanical entry/exit signals. Bull call spread neutralizes IV exposure — ideal for high-VIX entry. Signal-driven removes emotional bias.

### Greeks Profile
| Greek | Value | Assessment |
|-------|-------|------------|
| Delta | +0.25 to +0.35 | Moderate bullish |
| Gamma | Small positive | Benefits from sharp upmove |
| Vega | Near neutral (spread) | Excellent for HIGH VIX |
| Theta | Small negative | Manageable |

### Key Risk
Supertrend win rate (55-62%) is unverified community data. In news-driven volatile markets (VIX > 20), false signals increase. Discount win rate to 45-50%.

### Rubric Breakdown
| Dimension | Score |
|-----------|-------|
| Edge Clarity | 6 |
| Entry Precision | 7 |
| Exit Discipline | 8 |
| Risk-Reward | 8 |
| Liquidity Feasibility | 9 |
| Historical Evidence | 4 |
| IV Regime Alignment | 7 |
| Regulatory Compliance | 10 |
| Capital Efficiency | 8 |
| Failure Mode Resilience | 6 |
| Greeks Robustness | 7 |
| **Raw: 80** | **Deductions: -10** |

---

## Portfolio Correlation Check
- **W1 (Ratio Backspread)** and **W6 (Bull Call Spread)** are LOW CORRELATION — different structures, different profit mechanisms (credit vs debit, unlimited vs capped). Can be held simultaneously.

## IV Regime Suitability
Both strategies are well-suited for HIGH VIX:
- W1: Net credit enabled by inflated premiums
- W6: Spread structure neutralizes vega

## Key Weekly Insight
**SEBI weekly expiry rationalization is the dominant filter.** Only Nifty weekly strategies are executable with confidence. BankNifty, Midcap Nifty, and FinNifty weekly options may not exist post-SEBI circular. All future weekly strategy research should focus on Nifty (NSE) and Sensex (BSE) only.
