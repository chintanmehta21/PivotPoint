export const theme = {
  dark: {
    bg: { primary: '#1a1d2e', secondary: '#252836', surface: '#2d3142' },
    text: { primary: '#e8e8e8', secondary: '#a0a4b8', muted: '#6b7084' },
    accent: { primary: '#c9a96e', secondary: '#5ec4c4' },
    positive: '#4a9d6e',
    negative: '#c95454',
    border: '#3a3d50',
    shadow: { hover: '0 4px 12px rgba(0, 0, 0, 0.3)' },
  },
  light: {
    bg: { primary: '#f5f3ef', secondary: '#ffffff', surface: '#edeae4' },
    text: { primary: '#1a1d2e', secondary: '#4a4d5e', muted: '#8a8d9e' },
    accent: { primary: '#b8943d', secondary: '#3a9e9e' },
    positive: '#2d7a4f',
    negative: '#b83a3a',
    border: '#d4d1cb',
    shadow: { hover: '0 4px 12px rgba(0, 0, 0, 0.1)' },
  },
  typography: {
    fontHeading: "'Inter', sans-serif",
    fontMono: "'JetBrains Mono', monospace",
    sizes: { xs: '0.75rem', sm: '0.875rem', md: '1rem', lg: '1.25rem', xl: '1.5rem', xxl: '2rem' },
    weights: { regular: 400, medium: 500, semibold: 600, bold: 700 },
  },
  spacing: { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px', xxl: '48px' },
  radius: { sm: '4px', md: '8px', lg: '12px', xl: '16px' },
  transitions: { fast: '150ms ease', normal: '250ms ease', slow: '400ms ease' },
}

export const APP_NAME = 'PivotPoint'
export const APP_VERSION = '0.1.0'
