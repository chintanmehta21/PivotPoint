/**
 * StrategySection — themed wrapper that renders a titled, color-accented section
 * (bullish or bearish) containing a vertical list of collapsible StrategyCards.
 */
import { StrategyCard } from '../StrategyCard/StrategyCard.jsx';
import styles from './StrategySection.module.css';

export function StrategySection({ title, strategies, direction }) {
  const isBullish = direction === 'bullish';
  const headerAccentClass = isBullish ? styles.headerBullish : styles.headerBearish;

  return (
    <section className={styles.section}>
      {/* ── Section header ── */}
      <div className={`${styles.sectionHeader} ${headerAccentClass}`}>
        <h2 className={styles.sectionTitle}>{title}</h2>
        <span className={styles.sectionCount}>
          {strategies && strategies.length > 0
            ? `${strategies.length} ${strategies.length === 1 ? 'strategy' : 'strategies'}`
            : null}
        </span>
      </div>

      {/* ── Card grid or empty state ── */}
      {!strategies || strategies.length === 0 ? (
        <p className={styles.emptyState}>No strategies available.</p>
      ) : (
        <div className={styles.grid}>
          {strategies.map((strategy, idx) => (
            <StrategyCard
              key={strategy.name ?? idx}
              strategy={strategy}
              direction={direction}
            />
          ))}
        </div>
      )}
    </section>
  );
}
