import { createContext, useState, useEffect, useCallback } from 'react';
import { theme } from './theme.js';

export const ThemeContext = createContext(null);

/**
 * Flattens the mode-specific portion of the theme object and injects all tokens
 * as CSS custom properties on document.documentElement.
 *
 * Mapping rules (mirrors the CSS var names components will use via var(--xxx)):
 *   bg.primary        → --bg-primary
 *   text.secondary    → --text-secondary
 *   accent.primary    → --accent-primary
 *   positive          → --positive
 *   negative          → --negative
 *   border            → --border
 *
 * Typography (shared, not mode-specific):
 *   fontHeading       → --font-heading
 *   fontMono          → --font-mono
 *   sizes.xs          → --size-xs
 *   weights.regular   → --weight-regular
 *
 * Spacing / radius / transitions (shared):
 *   spacing.md        → --spacing-md
 *   radius.sm         → --radius-sm
 *   transitions.fast  → --transition-fast
 */
function injectCssVars(modeName) {
  const root = document.documentElement;
  const modeTokens = theme[modeName];

  // --- mode-specific tokens ---
  // bg.*
  Object.entries(modeTokens.bg).forEach(([key, val]) => {
    root.style.setProperty(`--bg-${key}`, val);
  });
  // text.*
  Object.entries(modeTokens.text).forEach(([key, val]) => {
    root.style.setProperty(`--text-${key}`, val);
  });
  // accent.*
  Object.entries(modeTokens.accent).forEach(([key, val]) => {
    root.style.setProperty(`--accent-${key}`, val);
  });
  // flat scalars
  root.style.setProperty('--positive', modeTokens.positive);
  root.style.setProperty('--negative', modeTokens.negative);
  root.style.setProperty('--border', modeTokens.border);

  // --- shared tokens (same for both modes) ---
  const { typography, spacing, radius, transitions } = theme;

  root.style.setProperty('--font-heading', typography.fontHeading);
  root.style.setProperty('--font-mono', typography.fontMono);

  Object.entries(typography.sizes).forEach(([key, val]) => {
    root.style.setProperty(`--size-${key}`, val);
  });
  Object.entries(typography.weights).forEach(([key, val]) => {
    root.style.setProperty(`--weight-${key}`, val);
  });
  Object.entries(spacing).forEach(([key, val]) => {
    root.style.setProperty(`--spacing-${key}`, val);
  });
  Object.entries(radius).forEach(([key, val]) => {
    root.style.setProperty(`--radius-${key}`, val);
  });
  Object.entries(transitions).forEach(([key, val]) => {
    root.style.setProperty(`--transition-${key}`, val);
  });
}

const STORAGE_KEY = 'pivotpoint-theme';
const DEFAULT_THEME = 'dark';

export function ThemeProvider({ children }) {
  const [currentTheme, setCurrentTheme] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME;
  });

  // Inject CSS vars whenever the theme changes (and on first mount).
  useEffect(() => {
    injectCssVars(currentTheme);
    localStorage.setItem(STORAGE_KEY, currentTheme);
  }, [currentTheme]);

  const toggleTheme = useCallback(() => {
    setCurrentTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  return (
    <ThemeContext.Provider value={{ currentTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
