/**
 * App — root component. Wraps the full page shell in ThemeProvider so all
 * child components receive CSS variable overrides for the active theme.
 */
import { ThemeProvider } from './config/ThemeProvider.jsx';
import { Toolbar } from './components/Toolbar/Toolbar.jsx';
import { Footer } from './components/Footer/Footer.jsx';
import { MarketOverview } from './components/MarketOverview/MarketOverview.jsx';
import { SentimentGauge } from './components/SentimentGauge/SentimentGauge.jsx';
import { StrategySection } from './components/StrategySection/StrategySection.jsx';
import { bullishStrategies } from './data/bullishStrategies.js';
import { bearishStrategies } from './data/bearishStrategies.js';
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/react';
import styles from './App.module.css';

function AppContent() {
  return (
    <div className={styles.appShell}>
      <Toolbar />
      <main className={styles.main}>
        <MarketOverview />
        <SentimentGauge />
        <StrategySection
          title="Bullish Strategies"
          strategies={bullishStrategies}
          direction="bullish"
        />
        <StrategySection
          title="Bearish Strategies"
          strategies={bearishStrategies}
          direction="bearish"
        />
      </main>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
      <Analytics />
      <SpeedInsights />
    </ThemeProvider>
  );
}

export default App;
