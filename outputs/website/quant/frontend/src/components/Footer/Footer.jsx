/**
 * Footer — short disclaimer with author link and last-updated timestamp.
 */
import styles from './Footer.module.css';

const CM_URL = import.meta.env.VITE_CM_URL || '#';

export function Footer() {
  const lastUpdated = new Date().toLocaleDateString();

  return (
    <footer className={styles.footer} role="contentinfo">
      <div className={styles.disclaimer}>
        <span className={styles.notAdvice}>NOT Financial advice</span>
        <span className={styles.madeBy}>
          Made by{' '}
          <a
            href={CM_URL}
            className={styles.cmLink}
            target="_blank"
            rel="noopener noreferrer"
          >
            CM
          </a>
        </span>
      </div>

      <span className={styles.timestamp}>
        Last updated: {lastUpdated}
      </span>
    </footer>
  );
}
