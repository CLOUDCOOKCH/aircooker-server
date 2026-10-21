import { useEffect, useState } from 'react';
import { useApp } from './model';

type Theme = 'flo' | 'after-dark' | 'sunday';
declare global {
  interface Window {
    mealfAppearance: { get(): Theme; set(theme: Theme): boolean };
  }
}
const themes = [
  { id: 'flo', name: 'Flo', description: 'themeFlo', mode: 'themeDevice' },
  { id: 'after-dark', name: 'After Dark', description: 'themeDark', mode: 'themeAlwaysDark' },
  { id: 'sunday', name: 'Sunday', description: 'themeLight', mode: 'themeAlwaysLight' },
] as const;

export function ThemeLibrary() {
  const { t } = useApp();
  const [selected, setSelected] = useState(window.mealfAppearance.get);
  const [unsaved, setUnsaved] = useState(false);
  useEffect(() => {
    const update = () => setSelected(window.mealfAppearance.get());
    window.addEventListener('mealf:appearance', update);
    return () => window.removeEventListener('mealf:appearance', update);
  }, []);
  return (
    <fieldset className="settings-group theme-library" aria-describedby="theme-hint">
      <legend>{t('themes')}</legend>
      <p id="theme-hint" className="settings-description">
        {t('themeHint')}
      </p>
      <div className="theme-options">
        {themes.map((theme) => (
          <label className="theme-option" key={theme.id}>
            <span className="theme-preview" data-theme-preview={theme.id} aria-hidden="true">
              <span className="theme-preview-heading" />
              <span className="theme-preview-meal">
                <span />
                <span />
              </span>
              <span className="theme-preview-nav">
                <span />
                <span />
                <span />
              </span>
            </span>
            <span className="theme-copy">
              <strong>{theme.name}</strong>
              <small id={`theme-description-${theme.id}`}>{t(theme.description)}</small>
              <span className="theme-mode" id={`theme-mode-${theme.id}`}>
                {t(theme.mode)}
              </span>
            </span>
            <input
              type="radio"
              name="appearance"
              value={theme.id}
              checked={selected === theme.id}
              aria-label={theme.name}
              aria-describedby={`theme-description-${theme.id} theme-mode-${theme.id}`}
              onChange={() => setUnsaved(!window.mealfAppearance.set(theme.id))}
            />
          </label>
        ))}
      </div>
      <p className="theme-status" role="status">
        {unsaved ? t('themeNotSaved') : ''}
      </p>
    </fieldset>
  );
}
