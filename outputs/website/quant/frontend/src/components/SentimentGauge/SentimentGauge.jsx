import { sentimentData } from '../../data/sentimentData';
import { PlaceholderBadge } from '../common/PlaceholderBadge';
import styles from './SentimentGauge.module.css';

/**
 * Map a zone color key to the corresponding CSS variable string.
 */
function zoneColorVar(color) {
  if (color === 'positive') return 'var(--positive)';
  if (color === 'negative') return 'var(--negative)';
  return 'var(--text-muted)';
}

/**
 * Resolve which zone the current score falls into,
 * so the label color can match the bar segment colour.
 */
function resolveZoneColor(score, zones) {
  const zone = zones.find((z) => score >= z.min && score <= z.max);
  return zone ? zoneColorVar(zone.color) : 'var(--text-muted)';
}

/* ============================================================
   Main component — compact horizontal bar
   ============================================================ */
export function SentimentGauge() {
  const { score, label, description, zones, isPlaceholder } = sentimentData;
  const labelColor = resolveZoneColor(score, zones);

  return (
    <section className={styles.section} aria-labelledby="sentiment-title">
      <h2 id="sentiment-title" className={styles.sectionTitle}>
        Market Sentiment
        <PlaceholderBadge isPlaceholder={isPlaceholder} />
      </h2>

      <div className={styles.gaugeCard}>
        {/* Score + label row */}
        <div className={styles.scoreRow}>
          <span className={styles.score}>{score}</span>
          <span className={styles.label} style={{ color: labelColor }}>
            {label}
          </span>
        </div>

        {/* Horizontal bar */}
        <div
          className={styles.barTrack}
          role="img"
          aria-label={`Fear and greed bar showing ${score} — ${label}`}
        >
          {zones.map((zone) => (
            <div
              key={zone.label}
              className={styles.barSegment}
              style={{
                width: `${zone.max - zone.min}%`,
                backgroundColor: zoneColorVar(zone.color),
                opacity: 0.85,
              }}
            />
          ))}
          {/* Needle indicator */}
          <div
            className={styles.barNeedle}
            style={{ left: `${score}%` }}
            aria-hidden="true"
          />
        </div>

        {/* Description */}
        <p className={styles.description}>{description}</p>
      </div>
    </section>
  );
}
