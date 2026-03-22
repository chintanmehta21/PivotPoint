import { ThemeProvider } from './config/ThemeProvider.jsx';
import { APP_NAME } from './config/theme.js';

function AppContent() {
  return (
    <div style={{ padding: 'var(--spacing-xl)' }}>
      <h1 style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>
        {APP_NAME}
      </h1>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
