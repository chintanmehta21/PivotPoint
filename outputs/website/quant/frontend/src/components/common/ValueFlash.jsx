import { useEffect, useRef } from 'react';
import styles from './ValueFlash.module.css';

/**
 * ValueFlash — wraps a numeric display and briefly applies a gold highlight
 * animation whenever the `value` prop changes.
 *
 * Props:
 *   value    — the numeric (or any) value being displayed; change detection
 *              is keyed on this prop via a ref comparison.
 *   children — the rendered content to wrap (typically formatted number text).
 */
export function ValueFlash({ value, children }) {
  const spanRef = useRef(null);
  const prevValueRef = useRef(value);

  useEffect(() => {
    // Skip the initial mount — only flash on subsequent changes.
    if (prevValueRef.current === value) return;
    prevValueRef.current = value;

    const el = spanRef.current;
    if (!el) return;

    // Remove then re-add to restart the animation if value changes rapidly.
    el.classList.remove(styles.flash);
    // Force reflow so the browser resets the animation state.
    void el.offsetWidth;
    el.classList.add(styles.flash);

    const timer = setTimeout(() => {
      el.classList.remove(styles.flash);
    }, 600);

    return () => clearTimeout(timer);
  }, [value]);

  return (
    <span ref={spanRef} className={styles.wrapper}>
      {children}
    </span>
  );
}
