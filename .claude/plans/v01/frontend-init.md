# PivotPoint Frontend — Init Plan

## Overview
Build a React + Vite quant dashboard at `outputs/website/quant/frontend/`. Static placeholder data (swappable for live API later). Dark/light theme driven by a single config file. No external UI libraries — vanilla CSS modules only.

## Design Decisions
| Decision | Choice |
|----------|--------|
| Location | `outputs/website/quant/frontend/` |
| Framework | React 18 + Vite |
| Styling | Vanilla CSS modules (no Tailwind, no MUI, no shadcn) |
| Fonts | JetBrains Mono (numerics), Inter (labels/headings) via Google Fonts |
| Theme | Config-driven dark/light via `src/config/theme.js` → CSS variables |
| Data | Static JS objects in `src/data/`, flagged `isPlaceholder: true` |
| Charts | SVG-only (no chart libraries) |
| Branding | `APP_NAME` constant matching Python backend identity |
| Deployment | Vercel SPA (`vercel.json` with rewrites) |

---

## Phase 0: Project Scaffold
**Goal:** Create Vite + React project with all config files.

### Files
- `outputs/website/quant/frontend/package.json` — React 18, Vite, dev deps only (no UI libs)
- `outputs/website/quant/frontend/vite.config.js` — Standard React config
- `outputs/website/quant/frontend/vercel.json` — SPA rewrites (`{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }`)
- `outputs/website/quant/frontend/index.html` — Entry with Google Fonts import, `<div id="root">`
- `outputs/website/quant/frontend/.gitignore` — node_modules, dist, .env

### Verification
- [ ] `npm install` succeeds
- [ ] `npm run dev` starts dev server
- [ ] Blank page renders at localhost

---

## Phase 1: Theme Config System
**Goal:** Single source of truth for all design tokens.

### `src/config/theme.js`
```js
export const theme = {
  dark: {
    bg: { primary: '#1a1d2e', secondary: '#252836', surface: '#2d3142' },
    text: { primary: '#e8e8e8', secondary: '#a0a4b8', muted: '#6b7084' },
    accent: { primary: '#c9a96e', secondary: '#5ec4c4' },  // muted gold, soft cyan
    positive: '#4a9d6e',   // toned green
    negative: '#c95454',   // toned red
    border: '#3a3d50',
  },
  light: {
    bg: { primary: '#f5f3ef', secondary: '#ffffff', surface: '#edeae4' },
    text: { primary: '#1a1d2e', secondary: '#4a4d5e', muted: '#8a8d9e' },
    accent: { primary: '#b8943d', secondary: '#3a9e9e' },
    positive: '#2d7a4f',
    negative: '#b83a3a',
    border: '#d4d1cb',
  },
  typography: {
    fontHeading: "'Inter', sans-serif",
    fontMono: "'JetBrains Mono', monospace",
    sizes: { xs: '0.75rem', sm: '0.875rem', md: '1rem', lg: '1.25rem', xl: '1.5rem', xxl: '2rem' },
    weights: { regular: 400, medium: 500, semibold: 600, bold: 700 },
  },
  spacing: { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px', xxl: '48px' },
  radius: { sm: '4px', md: '8px', lg: '12px', xl: '16px' },
  transitions: { fast: '150ms ease', normal: '250ms ease', slow: '400ms ease' },
}

export const APP_NAME = 'PivotPoint'
export const APP_VERSION = '0.1.0'
```

### `src/config/ThemeProvider.jsx`
- React context providing current theme (dark/light)
- On mount: read `localStorage.getItem('pivotpoint-theme')` or default to `'dark'`
- Injects all tokens as CSS variables on `document.documentElement`
- Exposes `toggleTheme()` and `currentTheme` via context

### `src/styles/global.css`
- CSS reset
- Google Fonts `@import`
- `body` styles using `var(--bg-primary)`, `var(--text-primary)`, etc.
- Utility classes for flash animation on value changes

### Verification
- [ ] Theme toggle switches all CSS variables
- [ ] `localStorage` persists choice across refresh
- [ ] Both themes fully styled (no unstyled elements)

---

## Phase 2: Layout Shell — Toolbar, App Container, Footer
**Goal:** Page skeleton with toolbar (logo + toggle) and footer.

### Components

#### `src/components/Toolbar/Toolbar.jsx` + `Toolbar.module.css`
- Compact height (~48px)
- Left: small `APP_NAME` text (not a heavy logo)
- Right: dark/light toggle (small sun/moon icon swap)
- Minimal visual weight: no heavy borders, no strong background contrast
- Uses config tokens for all colors

#### `src/components/Footer/Footer.jsx` + `Footer.module.css`
- Disclaimer: "Options trading involves substantial risk of loss..."
- Last updated timestamp (from data or `new Date()`)
- Placeholder nav links: About | Contact | Disclaimer
- Muted text, small font

#### `src/App.jsx`
- `<ThemeProvider>` wrapping everything
- `<Toolbar />`
- `<main>` container for sections (flex column, centered, max-width ~1200px)
- `<Footer />`

### Verification
- [ ] Toolbar renders with toggle
- [ ] Toggle works and persists
- [ ] Footer shows disclaimer
- [ ] Layout is responsive (mobile/tablet/desktop)

---

## Phase 3: Market Overview Bar
**Goal:** 6 index cards in a responsive horizontal strip.

### `src/data/marketData.js`
```js
export const marketIndices = [
  { name: 'Nifty 50', value: 23150.35, change: -1.24, isPlaceholder: true },
  { name: 'Bank Nifty', value: 53420.80, change: 0.87, isPlaceholder: true },
  { name: 'Nifty Midcap', value: 12850.60, change: -0.45, isPlaceholder: true },
  { name: 'India VIX', value: 22.09, change: 12.5, isPlaceholder: true },
  { name: 'SGX Nifty', value: 23180.00, change: -0.92, isPlaceholder: true },
  { name: 'Sensex', value: 76540.25, change: -1.18, isPlaceholder: true },
]
```

### `src/components/MarketOverview/MarketOverview.jsx` + `.module.css`
- Horizontal scrollable strip (CSS grid, wrap on desktop, scroll on mobile)
- Each card: name, value (mono font), % change with directional arrow
- Green/red color coding from theme (toned, not neon)
- Edge cases: null value → "—", negative VIX → show as-is, long name → truncate with ellipsis
- Subtle flash animation on value change (CSS `@keyframes`)

### `src/components/common/ValueFlash.jsx`
- Wraps any numeric display
- On value prop change, applies a brief highlight animation (gold/cyan flash from theme)

### Verification
- [ ] 6 cards render with correct data
- [ ] Green/red colors match theme config
- [ ] Null values show "—" gracefully
- [ ] Responsive: scrolls horizontally on mobile, wraps on desktop

---

## Phase 4: Market Sentiment Gauge
**Goal:** Fear & Greed SVG arc gauge.

### `src/data/sentimentData.js`
```js
export const sentimentData = {
  score: 32,
  label: 'Fear',
  description: 'Market participants showing elevated caution amid geopolitical uncertainty.',
  isPlaceholder: true,
  zones: [
    { min: 0, max: 20, label: 'Extreme Fear', color: 'negative' },
    { min: 20, max: 40, label: 'Fear', color: 'negative' },
    { min: 40, max: 60, label: 'Neutral', color: 'muted' },
    { min: 60, max: 80, label: 'Greed', color: 'positive' },
    { min: 80, max: 100, label: 'Extreme Greed', color: 'positive' },
  ],
}
```

### `src/components/SentimentGauge/SentimentGauge.jsx` + `.module.css`
- SVG semicircular arc (180°)
- Colored zones rendered as arc segments
- Needle/indicator at current score position
- Score number displayed large (mono font, centered)
- Label below ("Fear")
- Brief descriptor text
- Works in both themes (SVG fills reference CSS variables)

### Verification
- [ ] Gauge renders with correct score position
- [ ] Zone colors match theme
- [ ] Readable in both dark and light mode
- [ ] Score 0 and 100 edge cases render correctly

---

## Phase 5: Strategy Sections (Bullish + Bearish)
**Goal:** Reusable strategy section with progressive disclosure cards.

### `src/data/bullishStrategies.js`
```js
export const bullishStrategies = [
  {
    name: 'Bull Call Spread',
    description: 'Buy lower strike call, sell higher strike call. Limited risk, limited reward.',
    riskReward: 'Moderate Risk / Moderate Reward',
    technicalRationale: 'Best when IV is moderate and expecting steady upward move in underlying.',
    stocks: [
      { name: 'RELIANCE', entry: 2850, target: 2950, stopLoss: 2800, pctGain: 3.5,
        greeks: { delta: 0.45, theta: -12.5, gamma: 0.03, iv: 24.2 } },
      // ... 4 more
    ],
    isPlaceholder: true,
  },
  // 2 more strategies
]
```

### `src/data/bearishStrategies.js`
- Mirror structure, 3 bearish strategies (Bear Put Spread, Long Put, Protective Put)
- Same stock table structure with realistic NSE tickers

### `src/components/StrategySection/StrategySection.jsx` + `.module.css`
- Props: `title` ("Bullish Strategies" / "Bearish Strategies"), `strategies` (array), `direction` ("bullish"/"bearish")
- Renders a section header + grid of `StrategyCard` components
- Section header color-coded: subtle green tint for bullish, red for bearish

### `src/components/StrategyCard/StrategyCard.jsx` + `.module.css`
- Card layout:
  - **Header:** Strategy name + chevron icon (▼/▲) for expand/collapse
  - **Body (always visible):** Description, risk/reward badge, stock table
  - **Stock table columns:** Stock Name | Entry | Target | Stop-Loss | % Gain
  - **Expanded section (hidden by default):** Technical rationale text + Greeks table (Delta, Theta, Gamma, IV per stock)
- `useState` for expand/collapse toggle
- Table uses mono font for numbers
- % Gain column color-coded (green/red from theme)
- Edge cases: missing stock data → show "N/A", empty strategies array → "No strategies available"

### Verification
- [ ] 3 bullish + 3 bearish cards render
- [ ] Expand/collapse toggle works per card
- [ ] Greeks hidden by default, visible on expand
- [ ] Tables use mono font for numbers
- [ ] Responsive: cards stack on mobile, grid on desktop
- [ ] Edge cases handled (null values, empty arrays)

---

## Phase 6: Common Components & Error Handling
**Goal:** Shared components for error states, loading, and edge cases.

### `src/components/common/ErrorState.jsx` + `.module.css`
- Styled error card: icon + message + optional retry button
- Uses theme colors (muted, not alarming)

### `src/components/common/SkeletonLoader.jsx` + `.module.css`
- Animated placeholder blocks (pulse animation)
- Accepts `width`, `height`, `count` props

### `src/components/common/PlaceholderBadge.jsx`
- Small badge/tag that says "Sample Data" when `isPlaceholder: true`
- Rendered on any card using placeholder data

### Verification
- [ ] Error state renders with message
- [ ] Skeleton loader animates correctly in both themes
- [ ] Placeholder badge appears on all placeholder data cards

---

## Phase 7: Final Polish & Verification
**Goal:** Responsive testing, edge cases, code quality.

### Tasks
7.1. **Responsive audit:** Test all sections at 375px (mobile), 768px (tablet), 1200px+ (desktop)
7.2. **Theme audit:** Toggle dark↔light, verify no unstyled elements, no white-on-white or dark-on-dark
7.3. **Edge case audit:** Pass null/undefined/extreme values to all components
7.4. **Code comments:** Verify every component has a purpose comment at top
7.5. **Config audit:** `grep` for any hardcoded hex color, font, or spacing value in components — should be zero
7.6. **Data audit:** Verify all placeholder values are realistic Indian market data (correct index ranges, valid NSE tickers, realistic premiums)
7.7. **localStorage audit:** Clear storage, verify default theme loads, toggle persists across refresh

### Verification
- [ ] `npm run build` succeeds with no warnings
- [ ] All components have purpose comments
- [ ] Zero hardcoded design tokens in components
- [ ] All placeholder data flagged with `isPlaceholder: true`
- [ ] Responsive at all breakpoints
- [ ] Both themes fully styled

---

## File Manifest

```
outputs/website/quant/frontend/
├── index.html
├── package.json
├── vite.config.js
├── vercel.json
├── .gitignore
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── App.module.css
    ├── config/
    │   ├── theme.js
    │   └── ThemeProvider.jsx
    ├── hooks/
    │   └── useTheme.js
    ├── data/
    │   ├── marketData.js
    │   ├── sentimentData.js
    │   ├── bullishStrategies.js
    │   └── bearishStrategies.js
    ├── components/
    │   ├── Toolbar/
    │   │   ├── Toolbar.jsx
    │   │   └── Toolbar.module.css
    │   ├── MarketOverview/
    │   │   ├── MarketOverview.jsx
    │   │   └── MarketOverview.module.css
    │   ├── SentimentGauge/
    │   │   ├── SentimentGauge.jsx
    │   │   └── SentimentGauge.module.css
    │   ├── StrategySection/
    │   │   ├── StrategySection.jsx
    │   │   └── StrategySection.module.css
    │   ├── StrategyCard/
    │   │   ├── StrategyCard.jsx
    │   │   └── StrategyCard.module.css
    │   ├── Footer/
    │   │   ├── Footer.jsx
    │   │   └── Footer.module.css
    │   └── common/
    │       ├── ValueFlash.jsx
    │       ├── ValueFlash.module.css
    │       ├── ErrorState.jsx
    │       ├── ErrorState.module.css
    │       ├── SkeletonLoader.jsx
    │       ├── SkeletonLoader.module.css
    │       └── PlaceholderBadge.jsx
    └── styles/
        └── global.css
```

**Total: ~35 files**

---

## Execution Notes

- **Phase dependencies:** 0 → 1 → 2 → 3,4 (parallel) → 5 → 6 → 7
- **Parallelizable:** Phase 3 (Market Overview) and Phase 4 (Sentiment Gauge) are independent
- **No npm in subagents:** Subagents should create files, not run `npm install`
- **All design tokens from `theme.js`** — zero hardcoded values in components
- **Placeholder data is realistic** — real NSE tickers, correct index ranges
- **Progressive disclosure everywhere** — clean by default, details on demand
