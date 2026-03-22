import styles from './ErrorState.module.css';

/**
 * ErrorState — calm, non-alarming error card.
 *
 * Props:
 *   message  — error text to display (string, required)
 *   onRetry  — optional callback; when provided a "Try again" button is shown
 */
export function ErrorState({ message, onRetry }) {
  return (
    <div className={styles.card} role="alert" aria-live="polite">
      {/* Warning icon — inline SVG triangle with exclamation mark */}
      <svg
        className={styles.icon}
        viewBox="0 0 24 24"
        aria-hidden="true"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <line
          x1="12"
          y1="9"
          x2="12"
          y2="13"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
        />
        <circle cx="12" cy="17" r="0.75" fill="currentColor" />
      </svg>

      <p className={styles.message}>{message}</p>

      {onRetry && (
        <button className={styles.retryButton} onClick={onRetry} type="button">
          Try again
        </button>
      )}
    </div>
  );
}
