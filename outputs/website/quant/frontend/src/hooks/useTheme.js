import { useContext } from 'react';
import { ThemeContext } from '../config/ThemeProvider.jsx';

/**
 * Consume the theme context set up by ThemeProvider.
 * Returns { currentTheme, toggleTheme }.
 * Throws if called outside of a ThemeProvider tree.
 */
export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (ctx === null) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return ctx;
}
