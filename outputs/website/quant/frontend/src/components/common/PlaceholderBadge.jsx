import styles from './PlaceholderBadge.module.css';

/**
 * PlaceholderBadge — small inline pill shown when data is sample/placeholder.
 *
 * Props:
 *   isPlaceholder — boolean; when false (or absent) renders nothing at all
 *
 * Usage: place next to a section title or card header:
 *   <h2>Market Overview <PlaceholderBadge isPlaceholder={hasPlaceholder} /></h2>
 */
export function PlaceholderBadge({ isPlaceholder }) {
  if (!isPlaceholder) return null;

  return (
    <span className={styles.badge} aria-label="Sample data">
      Sample Data
    </span>
  );
}
