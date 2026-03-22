/**
 * Footer — disclaimer text, nav links, and last-updated timestamp.
 * Renders as a <footer> landmark at the bottom of the page shell.
 */
import styles from './Footer.module.css';

const DISCLAIMER =
  'Options trading involves substantial risk of loss. Past performance is not indicative of future results. ' +
  'The strategies and data presented are for informational purposes only.';

const NAV_LINKS = ['About', 'Contact', 'Disclaimer'];

export function Footer() {
  const lastUpdated = new Date().toLocaleDateString();

  return (
    <footer className={styles.footer} role="contentinfo">
      <p className={styles.disclaimer}>{DISCLAIMER}</p>

      <div className={styles.meta}>
        <nav className={styles.nav} aria-label="Footer navigation">
          {NAV_LINKS.map((label, index) => (
            <span key={label}>
              <span className={styles.navLink} role="link" tabIndex={0}>
                {label}
              </span>
              {index < NAV_LINKS.length - 1 && (
                <span className={styles.separator} aria-hidden="true">|</span>
              )}
            </span>
          ))}
        </nav>

        <span className={styles.timestamp}>
          Last updated: {lastUpdated}
        </span>
      </div>
    </footer>
  );
}
