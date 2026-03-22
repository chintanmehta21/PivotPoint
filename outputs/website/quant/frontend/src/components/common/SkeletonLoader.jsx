import styles from './SkeletonLoader.module.css';

/**
 * SkeletonLoader — animated placeholder blocks with a pulse effect.
 *
 * Props:
 *   width        — CSS width string (default: '100%')
 *   height       — CSS height string (default: '1rem')
 *   count        — number of skeleton lines to render (default: 1)
 *   borderRadius — CSS border-radius string (default: 'var(--radius-sm)')
 */
export function SkeletonLoader({
  width = '100%',
  height = '1rem',
  count = 1,
  borderRadius = 'var(--radius-sm)',
}) {
  const lines = Array.from({ length: count }, (_, i) => i);

  return (
    <div
      className={styles.wrapper}
      style={count > 1 ? { gap: 'var(--spacing-sm)' } : undefined}
      aria-busy="true"
      aria-label="Loading…"
    >
      {lines.map((i) => (
        <span
          key={i}
          className={styles.block}
          style={{ width, height, borderRadius }}
        />
      ))}
    </div>
  );
}
