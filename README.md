# PivotPoint

An options trading intelligence system for Indian derivatives markets. PivotPoint combines quantitative strategy engines, real-time market data pipelines, and multi-channel signal delivery to generate, evaluate, and distribute options trading signals across Nifty and Bank Nifty instruments.

## What It Does

PivotPoint scans live options chains, runs them through 14 proprietary multi-leg strategies, applies risk management filters, and delivers actionable signals to Discord, Telegram, and a web dashboard — all in real time.

The system is designed for the NSE derivatives market and understands the nuances of Indian options: weekly expiries, strike price conventions, VIX regime shifts, and Fyers API data structures.

## System Architecture

```
                    ┌─────────────────────┐
                    │     Fyers API        │
                    │  (Market Data Feed)  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  MarketDataProvider  │
                    │   (Protocol-based)   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  StrategyScanner     │
                    │  (async orchestrator)│
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                 │
    ┌─────────▼────────┐ ┌────▼──────┐ ┌───────▼────────┐
    │  6 Bullish        │ │ 8 Bearish │ │  Risk Manager  │
    │  Strategies       │ │ Strategies│ │  (pre-trade)   │
    └─────────┬────────┘ └────┬──────┘ └───────┬────────┘
              │                │                 │
              └────────────────┼─────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Signal Router     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                 │
    ┌─────────▼──────┐ ┌──────▼──────┐ ┌───────▼───────┐
    │    Discord      │ │  Telegram   │ │  Web Dashboard │
    │  (Embeds)       │ │ (MarkdownV2)│ │   (React SPA) │
    └────────────────┘ └─────────────┘ └───────────────┘
```

## Strategy Engine

The core of PivotPoint is its strategy library — 14 multi-leg options strategies that go beyond simple calls and puts:

**Bullish (6 strategies)**
- Supertrend Bull Call Spread — trend-following with defined risk
- Call Ratio Backspread — asymmetric payoff for strong moves
- Modified Butterfly — neutral-to-bullish with enhanced breakevens
- Broken Wing Call Butterfly — directional butterfly with credit
- Bullish Diagonal Calendar — time decay + directional bias
- Bullish Adjusted Iron Fly — volatility play with directional tilt

**Bearish (8 strategies)**
- Bear Call Credit Spread — income generation in downtrends
- Put Ratio Backspread — crash protection with leverage
- Skip-Strike Bearish Put Butterfly — wide-range profit zone
- Bear Put Condor — defined risk/reward in moderate declines
- Bearish Broken Wing Put Butterfly — credit-bearing directional put fly
- Bearish Diagonal Calendar Put — time decay with bearish bias
- Bearish Jade Lizard — premium collection with upside protection
- Bearish Put Ladder — multi-strike put combination

Each strategy implements four core methods: `evaluate` (screen opportunity), `build_position` (construct multi-leg trade), `check_exit` (manage live positions), and `validate_entry` (final pre-trade checks). Strategies are auto-discovered at runtime via the `StrategyRegistry`, which scans the bullish and bearish directories using `importlib`.

Strategies operate across **weekly**, **monthly**, and **quarterly** timeframes, targeting **Nifty** and **Bank Nifty** underlyings. Each carries a unique strategy ID (e.g., `BW1`, `BrM2`) for signal tracking and attribution.

## Data Layer

Market data flows through a **protocol-based** architecture (`typing.Protocol`, not ABC), with the primary implementation targeting the Fyers API. The data layer provides:

- Real-time options chain snapshots with full Greeks (delta, theta, gamma, vega, IV)
- Underlying price feeds for Nifty and Bank Nifty
- India VIX for volatility regime detection
- Historical candle data for technical analysis
- WebSocket streams for live tick data

All monetary values (strikes, premiums, P&L) use `Decimal` — never `float` — to avoid floating-point arithmetic errors in position sizing and risk calculations.

## Risk Management

Every signal passes through the `RiskManager` before delivery:

- **Max loss limits** per trade and portfolio-wide
- **VIX regime filters** — different strategy selection in high vs. low volatility
- **Position sizing** based on account risk parameters
- **Pre-trade validation** with configurable limits via `pydantic-settings`

## Signal Delivery

Signals are routed through three independent channels, each with its own formatter:

| Channel | Format | Use Case |
|---------|--------|----------|
| **Discord** | Rich embeds with color-coded fields | Team alerts, real-time monitoring |
| **Telegram** | MarkdownV2 with structured layouts | Mobile-first notifications |
| **Web Dashboard** | React SPA with interactive UI | Analysis, strategy comparison, portfolio overview |

## Web Dashboard

A standalone React + Vite single-page application that presents the trading intelligence visually:

- **Market Overview** — 6 Indian market indices (Nifty 50, Bank Nifty, Sensex, India VIX, and more) in a responsive card grid with real-time value formatting
- **Sentiment Gauge** — SVG semicircular arc visualizing market fear/greed with color-coded zones
- **Strategy Cards** — Progressive disclosure cards for all strategies: stock tables with entry/target/stop-loss, expandable Greeks panels (delta, theta, gamma, IV), and risk/reward badges
- **Theme System** — Config-driven dark/light mode with a single `theme.js` controlling all design tokens (colors, typography, spacing, radius, transitions) via CSS custom properties
- **Vercel Analytics** — Web Analytics + Speed Insights for traffic and Core Web Vitals monitoring

Built with vanilla CSS modules — no UI framework dependencies. Every color, font, and spacing value flows from the theme config, making the entire visual system modifiable from one file.

**Live:** [pivotpoint-one.vercel.app](https://pivotpoint-one.vercel.app)

## Data Science Layer

A protocol-based ML/AI layer (in development) designed to augment the quantitative engine:

- **Feature Pipelines** — Greeks-based and IV-based feature extractors for model training
- **Sentiment Analysis** — News sentiment scoring for market regime detection
- **Model Framework** — Base model abstractions for strategy enhancement

The data science layer communicates with the quant engine through well-defined protocols, keeping ML concerns decoupled from trading logic.

## Technical Foundation

| Aspect | Choice |
|--------|--------|
| **Language** | Python 3.11+ (engine), TypeScript/React (dashboard) |
| **Type System** | Pydantic models everywhere, mypy strict mode |
| **Configuration** | `pydantic-settings` with env var overrides |
| **Logging** | `structlog` with JSON (production) / console (development) |
| **Testing** | pytest with 82+ unit tests, custom fixtures, markers for slow/integration |
| **Linting** | Ruff (E, W, F, I, B, C4, UP, SIM rules, 120-char lines) |
| **Data Source** | Fyers API (options chains, Greeks, tick data) |
| **Deployment** | Vercel (dashboard), auto-deploy on push |

## Project Structure

```
PivotPoint/
├── src/
│   ├── quant/              # Core trading engine
│   │   ├── config/         # Settings, identity, environment
│   │   ├── data/           # Market data providers (Fyers API)
│   │   ├── execution/      # Scanner, signal router, position sizing
│   │   ├── models/         # Pydantic models (signals, contracts, market)
│   │   ├── risk/           # Risk limits, position tracking
│   │   ├── strategies/     # 14 strategy implementations
│   │   └── utils/          # Types, exceptions, helpers
│   │
│   └── data_science/       # ML/AI layer
│       ├── ai/             # Sentiment analysis
│       └── ml/             # Feature pipelines, model framework
│
├── outputs/                # Signal delivery channels
│   ├── discord/            # Discord bot + embed formatter
│   ├── telegram/           # Telegram bot + MarkdownV2 formatter
│   └── website/
│       ├── quant/frontend/ # React dashboard (Vite SPA)
│       └── dashboard/      # Backend data provider
│
├── tests/                  # 82+ unit tests
└── docs/                   # Architecture docs, strategy guides
```
