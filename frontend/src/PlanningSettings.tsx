import { useEffect, useRef, useState } from 'react';
import { useApp } from './model';
import { categories, uuid } from './lib/domain';
import { PLANNING_PATH, parsePreferences, parsePreferenceDraft } from './lib/preferences';
import type { PlanningPreferences, PreferenceDraft } from './lib/preferences';
import type { components } from './api-schema';
const DRAFT = 'planning:preferences-draft';
type Draft = PreferenceDraft;
export function PlanningSettings() {
  const app = useApp(),
    { t } = app;
  const saving = useRef(false);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [preferences, setPreferences] = useState<PlanningPreferences>(app.planning.preferences);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(false),
    [saved, setSaved] = useState(false);
  useEffect(() => {
    let alive = true;
    void app.store
      .setting<Draft | null>(DRAFT, null)
      .then((stored) => {
        const value = parsePreferenceDraft(stored);
        if (alive && !saving.current) {
          setDraft(value);
          setPreferences(value?.preferences ?? app.planning.preferences);
        }
      })
      .catch(() => {
        if (alive) setError(true);
      });
    return () => {
      alive = false;
    };
  }, [app.store, app.planning]);
  const update = (value: PlanningPreferences) => {
    const next = {
      request_id: uuid(),
      base_revision: draft?.base_revision ?? app.planning.revision,
      preferences: value,
    };
    setPreferences(value);
    setDraft(next);
    setSaved(false);
    setError(false);
    void app.store.setSetting(DRAFT, next).catch(() => setError(true));
  };
  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    saving.current = true;
    setBusy(true);
    setError(false);
    setSaved(false);
    try {
      const value = parsePreferences(preferences);
      if (app.demo) {
        await app.store.setSetting('planning:context', {
          ...app.planning,
          revision: app.planning.revision + 1,
          preferences: value,
        });
      } else {
        if (!app.api) throw Error('not_connected');
        const body = {
          request_id: draft?.request_id ?? uuid(),
          base_revision: draft?.base_revision ?? app.planning.revision,
          preferences: value,
        };
        const receipt = await app.api.request<components['schemas']['PreferenceReceipt']>(
          PLANNING_PATH,
          { method: 'PUT', body: JSON.stringify(body) },
        );
        if (receipt.request_id !== body.request_id) throw Error('invalid_receipt');
      }
      const current = await app.refreshPlanning();
      await app.store.setSetting(DRAFT, null);
      setDraft(null);
      setPreferences(current.preferences);
      setSaved(true);
    } catch {
      setError(true);
    } finally {
      saving.current = false;
      setBusy(false);
    }
  };
  return (
    <section className="settings-group">
      <h2>{t('planningPreferences')}</h2>
      <div className="settings-surface">
        <p className="settings-description">{t(app.demo ? 'planningDemo' : 'planningShared')}</p>
        <form className="reminder-form" onSubmit={(event) => void save(event)}>
          <fieldset disabled={busy}>
            <legend>{t('planningCategories')}</legend>
            {categories.map((category) => (
              <label className="check-row" key={category}>
                <input
                  type="checkbox"
                  checked={preferences.categories.includes(category)}
                  onChange={(event) =>
                    update({
                      ...preferences,
                      categories: categories.filter((value) =>
                        value === category
                          ? event.target.checked
                          : preferences.categories.includes(value),
                      ),
                    })
                  }
                />
                {t(category)}
              </label>
            ))}
            <label className="check-row">
              <input
                type="checkbox"
                checked={preferences.allow_repeats}
                onChange={(event) =>
                  update({ ...preferences, allow_repeats: event.target.checked })
                }
              />
              {t('planningRepeats')}
            </label>
            <label className="check-row">
              <input
                type="checkbox"
                checked={preferences.use_leftovers}
                onChange={(event) =>
                  update({ ...preferences, use_leftovers: event.target.checked })
                }
              />
              {t('planningLeftovers')}
            </label>
            <label className="check-row">
              <input
                type="checkbox"
                checked={preferences.servings !== null}
                onChange={(event) =>
                  update({ ...preferences, servings: event.target.checked ? '2' : null })
                }
              />
              {t('planningFixedServings')}
            </label>
            {preferences.servings !== null && (
              <label>
                {t('servings')}
                <input
                  inputMode="decimal"
                  required
                  value={preferences.servings}
                  onChange={(event) =>
                    update({ ...preferences, servings: event.target.value.replace(',', '.') })
                  }
                />
              </label>
            )}
            {!preferences.categories.length && (
              <p className="muted">{t('planningChooseCategory')}</p>
            )}
            <p className="muted">{t('planningSaveHint')}</p>
            <button
              className="secondary full"
              disabled={(!app.online && !app.demo) || !preferences.categories.length}
            >
              {t('planningSave')}
            </button>
          </fieldset>
        </form>
        {saved && (
          <p role="status" className="settings-description">
            {t('planningSaved')}
          </p>
        )}
        {error && (
          <p role="alert" className="settings-description">
            {t('planningError')}
          </p>
        )}
      </div>
    </section>
  );
}
