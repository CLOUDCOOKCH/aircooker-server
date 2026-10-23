import { useState } from 'react';
import { Plus, Search, Trash2 } from 'lucide-react';
import { useApp } from './model';
import { Empty, IconButton, PageHeader } from './components';
import { monday, pantryIncludedThisWeek, today, uuid } from './lib/domain';
export function Pantry({ back, setup }: { back?: () => void; setup?: () => void }) {
  const app = useApp(),
    { t } = app;
  const [name, setName] = useState(''),
    [query, setQuery] = useState(''),
    [error, setError] = useState(false);
  const day = today(app.household.timezone);
  const period = monday(day);
  const items = app
    .entities('pantry')
    .filter((row) => row.payload.name.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await app.save([
        { kind: 'pantry', id: uuid(), value: { name, available: true, include_this_week: false } },
      ]);
      setName('');
      setError(false);
    } catch {
      setError(true);
    }
  };
  return (
    <>
      <PageHeader title={t('pantry')} subtitle={t('pantryIntro')} back={back}>
        {setup && (
          <button className="secondary compact" onClick={setup}>
            {t('pantryChooseBasics')}
          </button>
        )}
      </PageHeader>
      <details className="pantry-help">
        <summary>{t('pantryHeading')}</summary>
        <p>{t('pantryBody')}</p>
      </details>
      <form className="add-staple" onSubmit={(e) => void add(e)}>
        <label className="sr-only" htmlFor="staple">
          {t('pantryName')}
        </label>
        <input
          id="staple"
          required
          maxLength={200}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t('pantryName')}
        />
        <button className="primary" disabled={!name.trim()}>
          <Plus size={18} />
          {t('add')}
        </button>
      </form>
      {error && (
        <p role="alert" className="error-note">
          {t('invalid')}
        </p>
      )}
      {app.entities('pantry').length > 4 && (
        <label className="search-field">
          <Search size={18} />
          <input
            type="search"
            placeholder={t('searchPantry')}
            aria-label={t('searchPantry')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
      )}
      {!app.entities('pantry').length ? (
        <Empty title={t('pantryEmpty')} body={t('pantryEmptyBody')} />
      ) : (
        <div className="pantry-list">
          {items.map((row) => (
            <div className="pantry-item" key={row.id}>
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={row.payload.available}
                  aria-label={`${t('available')} · ${row.payload.name}`}
                  onChange={(e) =>
                    void app
                      .save([
                        {
                          kind: 'pantry',
                          id: row.id,
                          value: { ...row.payload, available: e.target.checked },
                        },
                      ])
                      .catch(() => setError(true))
                  }
                />
                <strong>{row.payload.name}</strong>
              </label>
              <label className="check-row pantry-override">
                <input
                  type="checkbox"
                  checked={pantryIncludedThisWeek(row.payload, day)}
                  onChange={(e) =>
                    void app
                      .save([
                        {
                          kind: 'pantry',
                          id: row.id,
                          value: {
                            ...row.payload,
                            include_this_week: e.target.checked,
                            include_week_start: e.target.checked ? period : null,
                          },
                        },
                      ])
                      .catch(() => setError(true))
                  }
                />
                <span>{t('includeWeek')}</span>
              </label>
              <IconButton
                label={`${t('delete')} ${row.payload.name}`}
                onClick={() =>
                  void app
                    .save([{ kind: 'pantry', id: row.id, value: row.payload, deleted: true }])
                    .catch(() => setError(true))
                }
              >
                <Trash2 size={17} />
              </IconButton>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
