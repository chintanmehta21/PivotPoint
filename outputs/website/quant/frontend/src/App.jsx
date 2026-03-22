import { ThemeProvider } from './config/ThemeProvider.jsx';
import { Toolbar } from './components/Toolbar/Toolbar.jsx';
import { Footer } from './components/Footer/Footer.jsx';
import styles from './App.module.css';

function AppContent() {
  return (
    <div className={styles.appShell}>
      <Toolbar />
      <main className={styles.main}>
        {/* Phase 3+ content will be mounted here */}
      </main>
      <Footer />
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
