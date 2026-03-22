/**
 * StrategyCard — collapsible card displaying a single options strategy with
 * entry/target/stop-loss stock table and an expandable Greeks + rationale panel.
 */
import { useState } from 'react';
import { PlaceholderBadge } from '../common/PlaceholderBadge';
import styles from './StrategyCard.module.css';

// ── Formatters ──────────────────────────────────────────────────────────────

function fmtPrice(val) {
  if (val == null) return 'N/A';
  return Number(val).toLocaleString('en-IN');
}

function fmtPct(val) {
  if (val == null) return 'N/A';
  return `${Number(val).toFixed(1)}%`;
}

function fmtGreek(val) {
  if (val == null) return 'N/A';
  return Number(val).toFixed(2);
}

// ── Sub-components ───────────────────────────────────────────────────────────

function StockTable({ stocks }) {
  if (!stocks || stocks.length === 0) {
    return <p className={styles.emptyMsg}>No stock data available.</p>;
  }

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.th}>Stock</th>
            <th className={styles.th}>Entry</th>
            <th className={styles.th}>Target</th>
            <th className={styles.th}>Stop-Loss</th>
            <th className={styles.th}>% Gain</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock, idx) => (
            <tr key={stock.name ?? idx} className={idx % 2 === 0 ? styles.rowEven : styles.rowOdd}>
              <td className={styles.td}>{stock.name ?? 'N/A'}</td>
              <td className={`${styles.td} ${styles.mono}`}>{fmtPrice(stock.entry)}</td>
              <td className={`${styles.td} ${styles.mono}`}>{fmtPrice(stock.target)}</td>
              <td className={`${styles.td} ${styles.mono}`}>{fmtPrice(stock.stopLoss)}</td>
              <td className={`${styles.td} ${styles.mono} ${stock.pctGain >= 0 ? styles.positive : styles.negative}`}>
                {fmtPct(stock.pctGain)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GreeksTable({ stocks }) {
  if (!stocks || stocks.length === 0) {
    return <p className={styles.emptyMsg}>No Greeks data available.</p>;
  }

  return (
    <div className={styles.tableWrapper}>
      <table className={`${styles.table} ${styles.greeksTable}`}>
        <thead>
          <tr>
            <th className={styles.th}>Stock</th>
            <th className={styles.th}>Delta</th>
            <th className={styles.th}>Theta</th>
            <th className={styles.th}>Gamma</th>
            <th className={styles.th}>IV %</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock, idx) => {
            const g = stock.greeks ?? {};
            return (
              <tr key={stock.name ?? idx} className={idx % 2 === 0 ? styles.rowEven : styles.rowOdd}>
                <td className={styles.td}>{stock.name ?? 'N/A'}</td>
                <td className={`${styles.td} ${styles.mono}`}>{fmtGreek(g.delta)}</td>
                <td className={`${styles.td} ${styles.mono}`}>{fmtGreek(g.theta)}</td>
                <td className={`${styles.td} ${styles.mono}`}>{fmtGreek(g.gamma)}</td>
                <td className={`${styles.td} ${styles.mono}`}>{fmtGreek(g.iv)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export function StrategyCard({ strategy, direction }) {
  const [expanded, setExpanded] = useState(false);

  if (!strategy) return null;

  const isBullish = direction === 'bullish';
  const accentClass = isBullish ? styles.accentBullish : styles.accentBearish;

  return (
    <article className={`${styles.card} ${accentClass}`}>
      {/* ── Header ── */}
      <button
        className={styles.header}
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        aria-label={`${expanded ? 'Collapse' : 'Expand'} ${strategy.name}`}
      >
        <div className={styles.headerLeft}>
          <h3 className={styles.strategyName}>
            {strategy.name ?? 'Unnamed Strategy'}
            <PlaceholderBadge isPlaceholder={strategy.isPlaceholder} />
          </h3>
          {strategy.riskReward && (
            <span className={`${styles.badge} ${isBullish ? styles.badgeBullish : styles.badgeBearish}`}>
              {strategy.riskReward}
            </span>
          )}
        </div>
        <span className={`${styles.chevron} ${expanded ? styles.chevronUp : ''}`} aria-hidden="true">
          ▼
        </span>
      </button>

      {/* ── Always visible: description + stock table ── */}
      <div className={styles.body}>
        {strategy.description && (
          <p className={styles.description}>{strategy.description}</p>
        )}

        <StockTable stocks={strategy.stocks} />
      </div>

      {/* ── Progressive disclosure: rationale + greeks ── */}
      {expanded && (
        <div className={styles.expanded}>
          {strategy.technicalRationale && (
            <div className={styles.rationaleBlock}>
              <h4 className={styles.subHeading}>Technical Rationale</h4>
              <p className={styles.rationaleText}>{strategy.technicalRationale}</p>
            </div>
          )}

          <div className={styles.greeksBlock}>
            <h4 className={styles.subHeading}>Option Greeks</h4>
            <GreeksTable stocks={strategy.stocks} />
          </div>
        </div>
      )}
    </article>
  );
}
