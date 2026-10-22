import { createRoot } from 'react-dom/client';
import App from './App';
import { ErrorBoundary } from './ErrorBoundary';
import './styles.css';
import './task-layout.css';

// Safari emits gesture events even where touch-action alone is insufficient.
// Do not cancel single-finger touch events: scrolling and text handles need them.
for (const type of ['gesturestart', 'gesturechange', 'gestureend']) {
  document.addEventListener(type, (event) => event.preventDefault(), { passive: false });
}
// Trackpad pinch is exposed as Ctrl+wheel in Chromium. Normal wheel scrolling
// and browser/OS keyboard accessibility commands remain available.
document.addEventListener(
  'wheel',
  (event) => {
    if (event.ctrlKey) event.preventDefault();
  },
  { passive: false },
);

createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>,
);
