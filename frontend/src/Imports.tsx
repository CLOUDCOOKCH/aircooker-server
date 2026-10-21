import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Link, Plus } from 'lucide-react';
import { useApp } from './model';
import { PageHeader } from './components';
import { uuid } from './lib/domain';
import type { ImportTask } from './lib/store';
import { sourceKind } from './lib/imports';
import type { components } from './api-schema';
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
  const [file, setFile] = useState<File | null>(null);
  const [sourceID, setSourceID] = useState<string | null>(null);
  const [status, setStatus] = useState<components['schemas']['AISettingsStatus'] | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);
  useEffect(() => {
    let alive = true;
    if (app.api && !app.demo)
      void app.api
        .request<components['schemas']['AISettingsStatus']>('/api/v1/admin/ai')
        .then((value) => {
          if (alive) setStatus(value);
        })
        .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [app.api, app.demo]);
  useEffect(() => {
    if (
      !app.online ||
      !app.imports.some((task) => ['queued', 'processing', 'cancel_pending'].includes(task.state))
    )
      return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void app.sync();
    }, 2000);
    return () => window.clearInterval(timer);
  }, [app.online, app.imports, app.sync]);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setSaving(true);
    try {
      if (!url && !text.trim() && !file && !sourceID) throw new Error();
      if (file && (file.size > 8 * 1024 * 1024 || !sourceKind(file.type))) throw new Error();
      if (
        file &&
        status &&
        (!status.enabled || !status.input_formats?.includes(sourceKind(file.type)!))
      )
        throw new Error();
      const attachment = file ? uuid() : sourceID;
      await app.store.saveImport({
        id: uuid(),
        body: {
          source_url: url || null,
          text: text || null,
          use_ai: ai,
          consent_external_ai: ai && consent,
          ...(ai && status?.enabled && status.provider && status.base_url && status.model
            ? {
                ai_destination: [status.provider, status.base_url, status.model] as [
                  string,
                  string,
                  string,
                ],
              }
            : {}),
          ...(attachment ? { source_id: attachment } : {}),
        },
        ...(file ? { source: { blob: file, name: file.name } } : {}),
        state: 'queued',
      });
      setURL('');
      setText('');
      setFile(null);
      setSourceID(null);
      setConsent(false);
      if (fileInput.current) fileInput.current.value = '';
      setError(false);
      await app.changed();
    } catch {
      setError(true);
    } finally {
      submitting.current = false;
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
          <p className="muted">{t('importMetadataFirst')}</p>
          {app.demo ? (
            <div className="info-note">{t('demoUnavailable')}</div>
          ) : (
            <form onSubmit={(e) => void submit(e)}>
              <label>
                {t('importFile')}
                <input
                  ref={fileInput}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,application/pdf,video/mp4,video/webm"
                  onChange={(event) => {
                    const selected = event.target.files?.[0] ?? null;
                    setFile(selected);
                    setSourceID(null);
                    if (selected) {
                      setAI(true);
                      setConsent(false);
                    }
                  }}
                />
                <small>{t('importFileHint')}</small>
              </label>
              {(file || sourceID) && (
                <p className="info-note">{file?.name ?? t('importRetainedSource')}</p>
              )}
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
                  disabled={!!file || !!sourceID}
                  onChange={(e) => {
                    setAI(e.target.checked);
                    setConsent(false);
                  }}
                />
                {t('useAI')}
              </label>
              {ai && (
                <p className="muted">
                  {status?.enabled
                    ? `${t('aiDefault')}: ${status.provider} · ${status.model}`
                    : t('importAIUnavailable')}
                </p>
              )}
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
                  {t('importFileError')}
                </p>
              )}
              <button
                className="primary full"
                disabled={
                  saving || (!url && !text.trim() && !file && !sourceID) || (ai && !consent)
                }
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
                <strong>{task.recipe?.title || task.body.source_url || t('importRecipe')}</strong>
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
                    {task.error && (
                      <p role="status" className="error-note">
                        {t(
                          task.error === 'ai_input_format_unsupported'
                            ? 'importFormatUnsupported'
                            : task.error === 'ai_configuration_changed_review_consent'
                              ? 'importProviderChanged'
                              : task.error.includes('limit') || task.error.includes('large')
                                ? 'importLimit'
                                : task.error === 'ai_not_configured'
                                  ? 'importAIUnavailable'
                                  : 'importExtractionError',
                        )}
                      </p>
                    )}
                    <button
                      className="text-button"
                      onClick={() => {
                        setURL(task.body.source_url ?? '');
                        setText(task.body.text ?? '');
                        setSourceID(task.body.source_id ?? null);
                        setAI(!!task.body.use_ai);
                        setConsent(false);
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
