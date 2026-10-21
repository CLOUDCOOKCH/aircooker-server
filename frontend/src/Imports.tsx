import { useState } from 'react';
import { ArrowRight, Link, Plus } from 'lucide-react';
import { useApp } from './model';
import { PageHeader } from './components';
import { uuid } from './lib/domain';
import type { ImportTask } from './lib/store';
export function Imports({
  back,
  review,
  manual,
}: {
  back: () => void;
  review: (task: ImportTask) => void;
  manual: (task?: ImportTask) => void;
}) {
  const app = useApp(),
    { t } = app;
  const [url, setURL] = useState(''),
    [text, setText] = useState(''),
    [ai, setAI] = useState(false),
    [consent, setConsent] = useState(false),
    [error, setError] = useState(false),
    [saving, setSaving] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (!url && !text.trim()) throw new Error();
      await app.store.saveImport({
        id: uuid(),
        body: {
          source_url: url || null,
          text: text || null,
          use_ai: ai,
          consent_external_ai: ai && consent,
        },
        state: 'queued',
      });
      setURL('');
      setText('');
      setError(false);
      await app.changed();
    } catch {
      setError(true);
    } finally {
      setSaving(false);
    }
  };
  const cancel = async (task: ImportTask) => {
    try {
      await app.store.saveImport({
        ...task,
        state: 'cancel_pending',
      });
      await app.changed();
    } catch {
      setError(true);
    }
  };
  return (
    <>
      <PageHeader title={t('importRecipe')} back={back} />
      <div className="import-layout">
        <section>
          <p className="intro-copy">{t('importHint')}</p>
          {app.demo ? (
            <div className="info-note">{t('demoUnavailable')}</div>
          ) : (
            <form onSubmit={(e) => void submit(e)}>
              <label>
                {t('importURL')}
                <span className="input-icon">
                  <Link size={18} />
                  <input
                    type="url"
                    maxLength={2048}
                    placeholder="https://"
                    value={url}
                    onChange={(e) => setURL(e.target.value)}
                  />
                </span>
              </label>
              <label>
                {t('importText')}
                <textarea
                  rows={7}
                  maxLength={100000}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                />
              </label>
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={ai}
                  onChange={(e) => {
                    setAI(e.target.checked);
                    setConsent(false);
                  }}
                />
                {t('useAI')}
              </label>
              {ai && (
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={consent}
                    required
                    onChange={(e) => setConsent(e.target.checked)}
                  />
                  {t('aiConsent')}
                </label>
              )}
              {error && (
                <p role="alert" className="error-note">
                  {t('invalid')}
                </p>
              )}
              <button
                className="primary full"
                disabled={saving || (!url && !text.trim()) || (ai && !consent)}
              >
                {t('queueImport')}
                <ArrowRight size={18} />
              </button>
            </form>
          )}
          <button className="text-button" onClick={() => manual()}>
            <Plus size={17} />
            {t('create')}
          </button>
        </section>
        <section>
          <h2>{t('importing')}</h2>
          {app.imports
            .filter((task) => task.state !== 'cancelled')
            .map((task) => (
              <article className="import-job" key={task.id}>
                <strong>{task.recipe?.title ?? task.body.source_url ?? t('importText')}</strong>
                <p className="muted">
                  {t(
                    task.state === 'saving' || task.state === 'cancel_pending'
                      ? 'processing'
                      : task.state,
                  )}
                </p>
                {task.state === 'needs_input' && (
                  <>
                    <p>{t('importFallback')}</p>
                    <button
                      className="text-button"
                      onClick={() => {
                        setURL(task.body.source_url ?? '');
                        setText(task.body.text ?? '');
                      }}
                    >
                      {t('edit')}
                    </button>
                    <button className="text-button" onClick={() => manual(task)}>
                      {t('create')}
                    </button>
                  </>
                )}
                {task.state === 'preview' && (
                  <button className="secondary" onClick={() => review(task)}>
                    {t('review')}
                  </button>
                )}
                {!['saving', 'confirmed', 'cancel_pending'].includes(task.state) && (
                  <button className="text-button danger" onClick={() => void cancel(task)}>
                    {t('cancelImport')}
                  </button>
                )}
              </article>
            ))}
        </section>
      </div>
    </>
  );
}
