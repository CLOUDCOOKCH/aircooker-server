import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Check, Search } from 'lucide-react';
import { useApp } from './model';
import { PageHeader } from './components';
import { PANTRY_FOODS, pantryKey } from './lib/food';
import { uuid } from './lib/domain';
import { foodEmoji } from './lib/ingredient-options';
import type { Edit } from './lib/store';

const DRAFT = 'food:pantry-draft:v1';
export function PantrySetup({ back }: { back: () => void }) {
  const app = useApp(),
    { t } = app;
  const [selected, setSelected] = useState<string[]>([]),
    [query, setQuery] = useState(''),
    [ready, setReady] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(false);
  const lock = useRef(false);
  useEffect(() => {
    let alive = true;
    void (async () => {
      const draft = await app.store.setting<string[] | null>(DRAFT, null);
      if (
        draft &&
        (!Array.isArray(draft) || draft.some((id) => !PANTRY_FOODS.some((food) => food.id === id)))
      )
        throw Error('invalid');
      const existing = PANTRY_FOODS.filter((food) =>
        app
          .entities('pantry')
          .some(
            (row) => row.payload.available && pantryKey(row.payload.name) === 'catalog:' + food.id,
          ),
      ).map((food) => food.id);
      if (alive) {
        setSelected(draft ?? existing);
        setReady(true);
      }
    })().catch(() => {
      if (alive) setError(true);
    });
    return () => {
      alive = false;
    };
  }, [app.store]);
  const toggle = async (id: string) => {
    const next = selected.includes(id)
      ? selected.filter((value) => value !== id)
      : [...selected, id];
    setSelected(next);
    try {
      await app.store.setSetting(DRAFT, next);
      setError(false);
    } catch {
      setError(true);
    }
  };
  const finish = async (skip = false) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(false);
    try {
      const edits: Edit[] = [];
      if (!skip) {
        // Read current durable records, including edits made by another tab.
        const current = (await app.store.all()).filter(
          (row) => row.kind === 'pantry' && !row.deleted,
        );
        for (const food of PANTRY_FOODS) {
          const matches = current.filter(
            (row) => pantryKey((row.payload as { name: string }).name) === 'catalog:' + food.id,
          );
          const available = selected.includes(food.id);
          if (!matches.length && available)
            edits.push({
              kind: 'pantry',
              id: uuid(),
              value: { name: food.name[app.language], available: true, include_this_week: false },
            });
          for (const row of matches) {
            const value = row.payload as {
              name: string;
              available: boolean;
              include_this_week: boolean;
              include_week_start?: string | null;
            };
            if (value.available !== available)
              edits.push({ kind: 'pantry', id: row.id, value: { ...value, available } });
          }
        }
      }
      await app.save(edits, { food: { pantry_setup_done: true } });
      if (!skip) await app.store.setSetting(DRAFT, null);
      back();
    } catch {
      setError(true);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const items = PANTRY_FOODS.filter((food) =>
    food.name[app.language]
      .toLocaleLowerCase(app.language)
      .includes(query.trim().toLocaleLowerCase(app.language)),
  );
  return (
    <div className="pantry-onboarding">
      <PageHeader title={t('pantrySetupTitle')} subtitle={t('pantrySetupHint')} back={back} />
      <label className="search-field">
        <Search size={18} aria-hidden="true" />
        <input
          type="search"
          aria-label={t('searchPantry')}
          placeholder={t('searchPantry')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={busy}
        />
      </label>
      <fieldset disabled={busy || !ready} className="staple-picker">
        <legend className="sr-only">{t('pantrySetupTitle')}</legend>
        {(['seasoning', 'cupboard', 'fridge'] as const).map((group) => {
          const foods = items.filter((food) => food.pantry_group === group);
          return (
            foods.length > 0 && (
              <section
                className="staple-group"
                key={group}
                aria-label={t(
                  group === 'seasoning'
                    ? 'pantrySeasoning'
                    : group === 'cupboard'
                      ? 'pantryCupboard'
                      : 'pantryFridge',
                )}
              >
                <h2>
                  {t(
                    group === 'seasoning'
                      ? 'pantrySeasoning'
                      : group === 'cupboard'
                        ? 'pantryCupboard'
                        : 'pantryFridge',
                  )}
                </h2>
                <div className="staple-options">
                  {foods.map((food) => (
                    <label
                      className={'staple-option' + (selected.includes(food.id) ? ' selected' : '')}
                      key={food.id}
                    >
                      <input
                        type="checkbox"
                        checked={selected.includes(food.id)}
                        onChange={() => void toggle(food.id)}
                      />
                      <span className="pantry-emoji" aria-hidden="true">
                        {foodEmoji(food.name[app.language])}
                      </span>
                      <span>{food.name[app.language]}</span>
                      <Check size={16} aria-hidden="true" />
                    </label>
                  ))}
                </div>
              </section>
            )
          );
        })}
        {!items.length && <p className="muted">{t('pantryNoMatches')}</p>}
      </fieldset>
      <div className="onboarding-finish">
        <p className="muted">
          {selected.length} {t('pantrySelected')}
        </p>
        <button
          type="button"
          className="primary"
          disabled={busy || !ready}
          onClick={() => void finish()}
        >
          {t('pantrySaveBasics')}
          <ArrowRight size={18} />
        </button>
        <button
          type="button"
          className="text-button"
          disabled={busy}
          onClick={() => void finish(true)}
        >
          {t('setupNotNow')}
        </button>
      </div>
      {error && (
        <p className="error-note" role="alert">
          {t('foodSaveError')}
        </p>
      )}
    </div>
  );
}
