import { sentimentData } from '../../data/sentimentData';
import styles from './SentimentGauge.module.css';

/* ============================================================
   SVG constants
   ============================================================ */
const CX = 150;
const CY = 150;
const R = 110;
const STROKE_WIDTH = 22;
const NEEDLE_LENGTH = R - 10;
const NEEDLE_BASE_RADIUS = 7;

/**
 * Convert a 0-100 score to a radian angle on the semicircular arc.
 * Score 0   → π   (far left, 180°)
 * Score 100 → 0   (far right,  0°)
 * Score 50  → π/2 (straight up, 90°)
 */
function scoreToAngle(score) {
  return Math.PI - (score / 100) * Math.PI;
}

/**
 * Build an SVG arc path string for a single zone segment.
 * Angles are measured in radians from the positive x-axis.
 * Because SVG y-axis is flipped we negate the sin component.
 */
function buildArcPath(min, max) {
  // Add tiny inset gaps (0.5° in radians) so segments don't touch
  const GAP = 0.012;
  const startAngle = scoreToAngle(min) - GAP;
  const endAngle = scoreToAngle(max) + GAP;

  const x1 = CX + R * Math.cos(startAngle);
  const y1 = CY - R * Math.sin(startAngle);
  const x2 = CX + R * Math.cos(endAngle);
  const y2 = CY - R * Math.sin(endAngle);

  // large-arc-flag = 0 because each segment is exactly 36° (< 180°)
  return `M ${x1},${y1} A ${R},${R} 0 0,1 ${x2},${y2}`;
}

/**
 * Map a zone color key to the corresponding CSS variable string.
 */
function zoneColorVar(color) {
  if (color === 'positive') return 'var(--positive)';
  if (color === 'negative') return 'var(--negative)';
  return 'var(--text-muted)';
}

/* ============================================================
   Sub-components
   ============================================================ */

function GaugeArcs({ zones }) {
  return (
    <g aria-hidden="true">
      {zones.map((zone) => (
        <path
          key={zone.label}
          d={buildArcPath(zone.min, zone.max)}
          fill="none"
          stroke={zoneColorVar(zone.color)}
          strokeWidth={STROKE_WIDTH}
          strokeLinecap="round"
          opacity="0.85"
        />
      ))}
    </g>
  );
}

function GaugeNeedle({ score }) {
  const angle = scoreToAngle(score);
  const tipX = CX + NEEDLE_LENGTH * Math.cos(angle);
  const tipY = CY - NEEDLE_LENGTH * Math.sin(angle);

  return (
    <g aria-hidden="true">
      {/* Needle line */}
      <line
        x1={CX}
        y1={CY}
        x2={tipX}
        y2={tipY}
        stroke="var(--text-primary)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      {/* Pivot circle */}
      <circle
        cx={CX}
        cy={CY}
        r={NEEDLE_BASE_RADIUS}
        fill="var(--text-primary)"
      />
      {/* Inner dot for polish */}
      <circle
        cx={CX}
        cy={CY}
        r={NEEDLE_BASE_RADIUS - 3}
        fill="var(--bg-surface)"
      />
    </g>
  );
}

/**
 * Resolve which zone the current score falls into,
 * so the label color can match the arc segment colour.
 */
function resolveZoneColor(score, zones) {
  const zone = zones.find((z) => score >= z.min && score <= z.max);
  return zone ? zoneColorVar(zone.color) : 'var(--text-muted)';
}

/* ============================================================
   Main component
   ============================================================ */
export function SentimentGauge() {
  const { score, label, description, zones } = sentimentData;
  const labelColor = resolveZoneColor(score, zones);

  return (
    <section className={styles.section} aria-labelledby="sentiment-title">
      <h2 id="sentiment-title" className={styles.sectionTitle}>
        Market Sentiment
      </h2>

      <div className={styles.gaugeCard}>
        {/* SVG gauge */}
        <svg
          className={styles.svg}
          viewBox="0 0 300 165"
          role="img"
          aria-label={`Fear and greed gauge showing ${score} — ${label}`}
        >
          <GaugeArcs zones={zones} />
          <GaugeNeedle score={score} />
        </svg>

        {/* Numeric score */}
        <p className={styles.score} aria-live="polite">
          {score}
        </p>

        {/* Zone label — colour matches the arc segment */}
        <p className={styles.label} style={{ color: labelColor }}>
          {label}
        </p>

        {/* Description */}
        <p className={styles.description}>{description}</p>
      </div>
    </section>
  );
}
