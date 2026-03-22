# TOP 3 BEARISH WEEKLY STRATEGIES — Final Selection
## Run ID: run_20032026 | Date: 2026-03-20
## Expiry: March 24, 2026 (Tuesday) | India VIX: 22.09 (HIGH)
## Pipeline: Lead > ScoutLeaders > 4 Scouts > Orchestrator > Verifier > Final Synthesis
## Selection Criteria: Score >= 70/110, SEBI Compliant, IV Regime Aligned

---

## #1: Nifty Bearish Diagonal/Calendar Put [MERGED] — Score: 82/110

**Verdict:** STRONG PASS — Best weekly strategy in entire pipeline (bull + bear)

### Structure (2-Phase)
**Phase 1 — Calendar/Diagonal:**
- **Buy 1x** Nifty 22,900 PE — monthly Mar 31
- **Sell 1x** Nifty 22,900 PE — weekly Mar 24
- **Net Debit:** ~Rs 15,925 (245 pts x 65)

**Phase 2 — Post weekly expiry, sell Apr weekly to create diagonal:**
- Potential R:R improvement to 11.5:1

### Edge Thesis
**Triple edge:** Theta + Direction + IV Term Structure. The ONLY weekly strategy with NET LONG VEGA — profits from further VIX spikes, unlike every other short-vega structure. If Iran-Israel escalates, this position benefits. Phase 2 adds optionality via further premium collection.

### Greeks Profile
| Greek | Value | Assessment |
|-------|-------|------------|
| Delta | -0.35 | Moderate bearish |
| Gamma | Near neutral | Opposing expiries offset |
| Vega | +1.5 (NET LONG) | **UNIQUE** — profits from VIX spike |
| Theta | +Rs 455/day | Positive and growing |

### Key Risk
Rs 15,925 debit is substantial. Phase 2 contingent on Phase 1 success. IV term structure thesis assumed, not verified.

### Rubric Breakdown
| Dimension | Score |
|-----------|-------|
| Edge Clarity | 8 |
| Entry Precision | 7 |
| Exit Discipline | 7 |
| Risk-Reward | 8 |
| Liquidity Feasibility | 8 |
| Historical Evidence | 5 |
| IV Regime Alignment | 9 |
| Regulatory Compliance | 9 |
| Capital Efficiency | 6 |
| Failure Mode Resilience | 7 |
| Greeks Robustness | 8 |
| **Raw: 82** | **Deductions: 0** |

---

## #2: Nifty Put Ratio Backspread — Score: 78/110

**Verdict:** PASS — High-conviction crash hedge

### Structure
- **Sell 1x** Nifty 23,100 PE (ATM) — weekly Mar 24
- **Buy 2x** Nifty 22,700 PE (OTM) — weekly Mar 24
- **Net Credit:** ~Rs 1,950 (30 pts x 65)
- **Max Loss:** Rs 24,050 at 22,700 pin ("valley of death")
- **Max Profit:** Unlimited below 22,400

### Edge Thesis
THE crash hedge for the current environment. Net credit entry = PAID to hold downside insurance. Positive gamma means profits accelerate on big moves (exactly what's happening — 3.26% daily crashes). If Iran-Israel escalates overnight, massive profits. Only loses at the exact 22,700 pin.

### Greeks Profile
| Greek | Value | Assessment |
|-------|-------|------------|
| Delta | -0.10 | Mild bearish, accelerates on crash |
| Gamma | +0.06 (POSITIVE) | **Key advantage** — accelerates profits |
| Vega | +2.5 | Benefits from VIX spike |
| Theta | -Rs 455/day | NEGATIVE — time works against |

### Key Risk
"Valley of death" around 22,400-23,000 produces losses. This 600-pt zone includes first support level. A moderate 1-2% decline (most probable outcome) hits the worst zone.

### Rubric Breakdown
| Dimension | Score |
|-----------|-------|
| Edge Clarity | 8 |
| Entry Precision | 7 |
| Exit Discipline | 6 |
| Risk-Reward | 7 |
| Liquidity Feasibility | 9 |
| Historical Evidence | 5 |
| IV Regime Alignment | 8 |
| Regulatory Compliance | 10 |
| Capital Efficiency | 6 |
| Failure Mode Resilience | 5 |
| Greeks Robustness | 7 |
| **Raw: 78** | **Deductions: 0** |

---

## #3: Nifty Bearish Broken-Wing Put Butterfly — Score: 73/110

**Verdict:** CONDITIONAL PASS — Suitable for consolidation expectation only

### Structure
- **Buy 1x** Nifty 23,000 PE — weekly Mar 24
- **Sell 2x** Nifty 22,700 PE — weekly Mar 24
- **Buy 1x** Nifty 22,200 PE — weekly Mar 24
- **Net Debit:** ~Rs 1,625 (25 pts x 65)
- **Max Profit:** Rs 17,875 (275 pts x 65) at 22,700 pin
- **Max Loss:** Rs 14,625 below 22,200 | Rs 1,625 above 23,000
- **R:R:** 2.8:1 on debit

### Edge Thesis
Skew harvest + theta crush in high VIX. Zero-cost-like entry (Rs 1,625 debit). Broken wing caps catastrophic downside. Targets 22,700 support zone for a market that just crashed 3.26%.

### Greeks Profile
| Greek | Value | Assessment |
|-------|-------|------------|
| Delta | -0.17 | Mild bearish |
| Gamma | -0.030 (strongly negative) | **CRITICAL** at 1 DTE |
| Vega | -0.8 | Irrelevant at 1 DTE |
| Theta | +Rs 260/day | Favorable |

### Key Risk
**This is a PIN strategy in a CRASH market.** Profit zone is only 550 pts wide in a market moving 500-750 pts/day. Extreme negative gamma at 1 DTE means rapid P&L swings near sold strikes.

### Rubric Breakdown
| Dimension | Score |
|-----------|-------|
| Edge Clarity | 7 |
| Entry Precision | 6 |
| Exit Discipline | 7 |
| Risk-Reward | 7 |
| Liquidity Feasibility | 9 |
| Historical Evidence | 4 |
| IV Regime Alignment | 5 |
| Regulatory Compliance | 10 |
| Capital Efficiency | 8 |
| Failure Mode Resilience | 5 |
| Greeks Robustness | 5 |
| **Raw: 73** | **Deductions: 0** |

---

## Portfolio Correlation Check
- **W-6 (Diagonal)** vs **W-2 (Backspread):** LOW correlation. Different profit mechanisms (theta vs gamma), different vega profiles (long vs long). Complementary.
- **W-6 (Diagonal)** vs **W-1 (BWB):** LOW correlation. Different structures entirely. W-6 is cross-expiry, W-1 is single-expiry pin.
- **W-2 (Backspread)** vs **W-1 (BWB):** MODERATE correlation. Both single-expiry bearish on Nifty. But opposite gamma profiles (+0.06 vs -0.030). Natural hedge.
- **All 3 together:** Well-diversified portfolio covering crash (W-2), moderate decline (W-6), and consolidation (W-1).

## IV Regime Suitability
| Strategy | Vega | VIX Spike | VIX Crush |
|----------|------|-----------|-----------|
| W-6 Diagonal | LONG | Benefits | Hurts |
| W-2 Backspread | LONG | Benefits | Hurts |
| W-1 BWB | Neutral | Irrelevant | Irrelevant |

## Key Weekly Insight
**Bearish weekly has 3 viable strategies vs only 2 bullish — the market's bearish bias from geopolitical crisis creates more actionable bearish opportunities.** The highest-scoring weekly strategy (W-6 at 82) is bearish, and its long vega property is uniquely valuable as crisis insurance.
