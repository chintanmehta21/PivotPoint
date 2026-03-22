import { marketIndices } from '../../data/marketData';
import { PlaceholderBadge } from '../common/PlaceholderBadge';
import { ValueFlash } from '../common/ValueFlash';
import styles from './MarketOverview.module.css';

/**
 * Formats a numeric value using Indian number system (e.g. 23,150.35).
 * Returns the em dash "—" if value is null or undefined.
 */
function formatValue(value) {
  if (value == null) return '—';
  return value.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Formats the change percentage with a directional arrow prefix.
 * Positive → ▲, Negative → ▼, Zero → returns "0.00%".
 */
function formatChange(change) {
  if (change == null) return '—';
  const abs = Math.abs(change).toFixed(2);
  if (change > 0) return `▲ ${abs}%`;
  if (change < 0) return `▼ ${abs}%`;
  return `${abs}%`;
}

function IndexCard({ index }) {
  const { name, value, change } = index;
  const isPositive = change > 0;
  const isNegative = change < 0;

  const changeClass = isPositive
    ? styles.positive
    : isNegative
    ? styles.negative
    : styles.neutral;

  return (
    <article className={styles.card} aria-label={`${name} index`}>
      <h3 className={styles.cardName}>{name}</h3>
      <ValueFlash value={value}>
        <span className={styles.cardValue}>{formatValue(value)}</span>
      </ValueFlash>
      <span className={`${styles.cardChange} ${changeClass}`}>
        {formatChange(change)}
      </span>
    </article>
  );
}

export function MarketOverview() {
  const hasPlaceholder = marketIndices.some((idx) => idx.isPlaceholder);

  return (
    <section className={styles.section} aria-labelledby="market-overview-title">
      <h2 id="market-overview-title" className={styles.sectionTitle}>
        Market Overview
        <PlaceholderBadge isPlaceholder={hasPlaceholder} />
      </h2>
      <div className={styles.strip}>
        {marketIndices.map((index) => (
          <IndexCard key={index.name} index={index} />
        ))}
      </div>
    </section>
  );
}
