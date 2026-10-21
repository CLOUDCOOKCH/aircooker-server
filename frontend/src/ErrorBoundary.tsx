import { Component } from 'react';
import type { ReactNode } from 'react';
import { translate } from './i18n';
export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (!this.state.failed) return this.props.children;
    const language = document.documentElement.lang.startsWith('de') ? 'de' : 'en';
    return (
      <main className="welcome-content">
        <h1>{translate(language, 'error')}</h1>
        <p className="welcome-description" role="alert">
          {translate(language, 'crash')}
        </p>
        <button className="primary" onClick={() => location.reload()}>
          {translate(language, 'applyUpdate')}
        </button>
      </main>
    );
  }
}
