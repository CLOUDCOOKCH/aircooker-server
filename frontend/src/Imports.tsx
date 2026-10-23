import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Camera, ImagePlus, Link, Plus, X } from 'lucide-react';
import { useApp } from './model';
import { PageHeader, Photo } from './components';
import { uuid } from './lib/domain';
import type { ImportTask, Photo as StoredPhoto } from './lib/store';
import { prepareImportImage } from './lib/image-import';
import { sourceKind } from './lib/imports';
import type { components } from './api-schema';

const errorKeys = {
  image_ocr_unavailable: 'imageOCRUnavailable',
  image_ocr_failed: 'imageOCRFailed',
  image_ocr_timeout: 'imageOCRFailed',
  image_no_readable_text: 'imageNoText',
  image_recipe_layout_unclear: 'imageLayoutUnclear',
  image_text_too_large: 'imageOCRFailed',
  image_not_found: 'imageImportMissing',
  image_not_available_locally: 'imageImportMissing',
  media_storage_limit: 'imageStorageFull',
  storage_unavailable: 'serverStorageError',
  ai_not_configured: 'imageAINotConfigured',
  ai_input_format_unsupported: 'importFormatUnsupported',
  ai_configuration_changed_review_consent: 'importProviderChanged',
  import_source_expired: 'importExtractionError',
  chatgpt_connection_changed: 'chatgptConnectionError',
  chatgpt_configuration_changed: 'chatgptConnectionError',
  chatgpt_reconnect_required: 'chatgptConnectionError',
  chatgpt_session_ended: 'chatgptConnectionError',
  chatgpt_plan_permission_required: 'chatgptConnectionError',
  chatgpt_usage_limit: 'chatgptAllowanceError',
  chatgpt_usage_unavailable: 'chatgptAllowanceError',
  chatgpt_not_eligible: 'chatgptConnectionError',
} as const;
function BlobPreview({ blob, alt }: { blob: Blob; alt: string }) {
  const [url, setURL] = useState<string>();
  useEffect(() => {
    const next = URL.createObjectURL(blob);
    setURL(next);
    return () => URL.revokeObjectURL(next);
  }, [blob]);
  return url ? <img className="import-image-preview" src={url} alt={alt} /> : null;
}

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
  const [mode, setMode] = useState<'link' | 'image'>('link');
  const [file, setFile] = useState<File | null>(null);
  const [sourceID, setSourceID] = useState<string | null>(null);
  const [status, setStatus] = useState<components['schemas']['AISettingsStatus'] | null>(null);
  const [chatgpt, setChatGPT] = useState<components['schemas']['ChatGPTStatus'] | null>(null);
  const [account, setAccount] = useState<'household' | 'chatgpt'>('household');
  const fileInput = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);
  useEffect(() => {
    let alive = true;
    if (app.api && !app.demo)
      void app.api
        .request<components['schemas']['AISettingsStatus']>('/api/v1/ai/status')
        .then(async (value) => {
          if (
            alive &&
            value &&
            typeof value.enabled === 'boolean' &&
            typeof value.provider === 'string' &&
            typeof value.base_url === 'string' &&
            typeof value.model === 'string' &&
            Array.isArray(value.input_formats) &&
            value.input_formats.every((format) => typeof format === 'string')
          )
            setStatus(value);
          await app.store.setSetting('imports:ai-profile', value);
        })
        .catch(() => undefined);
    if (app.api && !app.demo)
      void app.api
        .request<components['schemas']['ChatGPTStatus']>('/api/v1/integrations/chatgpt')
        .then((value) => {
          if (alive) setChatGPT(value);
        })
        .catch(() => undefined);
    if (!app.online && !app.demo)
      void app.store
        .setting<components['schemas']['AISettingsStatus'] | null>('imports:ai-profile', null)
        .then((value) => {
          if (
            alive &&
            value &&
            typeof value.enabled === 'boolean' &&
            typeof value.provider === 'string' &&
            typeof value.base_url === 'string' &&
            typeof value.model === 'string' &&
            Array.isArray(value.input_formats) &&
            value.input_formats.every((format) => typeof format === 'string')
          )
            setStatus(value);
        })
        .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [app.api, app.demo, app.online]);
  const [url, setURL] = useState(''),
    [text, setText] = useState(''),
    [imageText, setImageText] = useState(''),
    [imageTextOpen, setImageTextOpen] = useState(false),
    [selected, setSelected] = useState<StoredPhoto>(),
    [consent, setConsent] = useState(false),
    [error, setError] = useState<
      'invalid' | 'saveError' | 'imageInputError' | 'importFileError' | null
    >(null),
    [saving, setSaving] = useState(false),
    [choosing, setChoosing] = useState(false);
  const ai =
    account === 'household' &&
    Boolean(
      status?.enabled &&
      status.provider &&
      status.base_url &&
      status.model &&
      status.input_formats?.includes('text'),
    );
  const [queuedFocus, setQueuedFocus] = useState<string>();
  useEffect(() => {
    if (!queuedFocus) return;
    const target = document.getElementById('import-job-' + queuedFocus);
    if (target) {
      target.focus({ preventScroll: true });
      target.scrollIntoView({ block: 'center', behavior: 'instant' });
      setQueuedFocus(undefined);
    }
  }, [queuedFocus, app.imports]);
  const activeImports = app.imports.some((task) =>
    ['queued', 'processing', 'cancel_pending'].includes(task.state),
  );
  useEffect(() => {
    if (!activeImports || !app.api) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible' && navigator.onLine) void app.sync();
    }, 2500);
    return () => window.clearInterval(timer);
  }, [activeImports, app.store]);
  const camera = useRef<HTMLInputElement>(null),
    gallery = useRef<HTMLInputElement>(null);
  const choose = async (file?: File) => {
    if (!file) return;
    setChoosing(true);
    try {
      const blob = await prepareImportImage(file);
      setSelected({ id: uuid(), blob, pending: true });
      setImageText('');
      setImageTextOpen(false);
      setError(null);
    } catch {
      setError('imageInputError');
    } finally {
      setChoosing(false);
    }
  };
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setSaving(true);
    try {
      if (account === 'chatgpt') {
        if (!text.trim() || !consent || !chatgpt?.model || chatgpt.state !== 'connected') {
          setError('invalid');
          return;
        }
        const importID = uuid();
        await app.store.saveImport({
          id: importID,
          state: 'queued',
          body: {
            text,
            use_ai: true,
            consent_external_ai: true,
            consent_chatgpt_background: true,
            ai_account: 'chatgpt',
            chatgpt_connection_id: chatgpt.connection_id,
            ai_destination: ['chatgpt', 'https://api.openai.com/v1', chatgpt.model],
          },
        });
        setText('');
        setConsent(false);
        setError(null);
        setQueuedFocus(importID);
        await app.changed();
        return;
      }
      if (mode === 'image' ? !selected : !url && !text.trim() && !file && !sourceID) {
        setError('invalid');
        return;
      }
      if (
        mode === 'link' &&
        file &&
        (file.size > 8 * 1024 * 1024 ||
          !sourceKind(file.type) ||
          (status && (!status.enabled || !status.input_formats?.includes(sourceKind(file.type)!))))
      ) {
        setError('importFileError');
        return;
      }
      const attachment = mode === 'link' ? (file ? uuid() : sourceID) : null;
      const importID = uuid();
      await app.store.saveImport(
        {
          id: importID,
          body: {
            source_url: mode === 'link' ? url || null : null,
            text: (mode === 'image' ? imageText : text) || null,
            image_id: mode === 'image' ? selected!.id : null,
            use_ai: ai,
            consent_external_ai: ai,
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
          ...(mode === 'link' && file ? { source: { blob: file, name: file.name } } : {}),
          state: 'queued',
        },
        mode === 'image' ? selected : undefined,
      );
      setURL('');
      setText('');
      setImageText('');
      setImageTextOpen(false);
      setSelected(undefined);
      setFile(null);
      setSourceID(null);
      setConsent(false);
      if (fileInput.current) fileInput.current.value = '';
      setError(null);
      setQueuedFocus(importID);
      await app.changed();
    } catch {
      setError('saveError');
    } finally {
      submitting.current = false;
      setSaving(false);
    }
  };
  const cancel = async (task: ImportTask) => {
    try {
      await app.store.saveImport({ ...task, state: 'cancel_pending' });
      await app.changed();
    } catch {
      setError('saveError');
    }
  };
  const editSource = async (task: ImportTask) => {
    try {
      setMode(task.body.image_id ? 'image' : 'link');
      setURL(task.body.source_url ?? '');
      setText(task.body.text ?? '');
      setFile(null);
      setSourceID(task.body.source_id ?? null);
      setImageText(task.recognizedText ?? task.body.text ?? '');
      setImageTextOpen(Boolean(task.body.image_id));
      setSelected(task.body.image_id ? await app.store.photo(task.body.image_id) : undefined);
      setAccount(task.body.ai_account === 'chatgpt' ? 'chatgpt' : 'household');
      setConsent(false);
      setError(null);
      document
        .querySelector('.import-methods')
        ?.scrollIntoView({ block: 'start', behavior: 'instant' });
    } catch {
      setError('saveError');
    }
  };
  return (
    <>
      <PageHeader title={t('importRecipe')} subtitle={t('importIntro')} back={back} />
      <div className="import-layout">
        <section
          onPaste={(event) => {
            if (mode !== 'image' || choosing || saving || app.demo) return;
            const file = [...event.clipboardData.files].find((item) =>
              item.type.startsWith('image/'),
            );
            if (file) {
              event.preventDefault();
              void choose(file);
            }
          }}
        >
          {app.demo ? (
            <div className="info-note">{t('demoUnavailable')}</div>
          ) : (
            <>
              <div className="import-methods" role="group" aria-label={t('importMethod')}>
                {(['link', 'image'] as const).map((method) => (
                  <button
                    type="button"
                    key={method}
                    aria-pressed={mode === method}
                    onClick={() => {
                      setMode(method);
                      setAccount('household');
                      setConsent(false);
                      setError(null);
                    }}
                  >
                    {method === 'image' ? <ImagePlus size={19} /> : <Link size={19} />}
                    {t(method === 'image' ? 'photoOrScreenshot' : 'linkOrText')}
                  </button>
                ))}
              </div>
              <form onSubmit={(e) => void submit(e)}>
                {mode === 'link' &&
                  ((chatgpt?.state === 'connected' && chatgpt.model) || account === 'chatgpt') && (
                    <label>
                      {t('chatgptImportAccount')}
                      <select
                        aria-label={t('chatgptImportAccount')}
                        value={account}
                        onChange={(event) => {
                          setAccount(event.target.value as 'household' | 'chatgpt');
                          setConsent(false);
                        }}
                      >
                        <option value="household">{t('chatgptHousehold')}</option>
                        <option value="chatgpt">{t('chatgptPersonal')}</option>
                      </select>
                    </label>
                  )}
                {account === 'chatgpt' ? (
                  <>
                    <p className="intro-copy">{t('chatgptTextOnly')}</p>
                    <p className="muted">
                      {chatgpt?.account_label} · {chatgpt?.model} · https://api.openai.com/v1
                    </p>
                    <label>
                      {t('importText')}
                      <textarea
                        rows={9}
                        maxLength={50000}
                        value={text}
                        onChange={(event) => setText(event.target.value)}
                      />
                    </label>
                  </>
                ) : mode === 'image' ? (
                  <>
                    <p className="intro-copy">{t('imageImportHint')}</p>
                    <div className="image-source-actions">
                      <button
                        className="secondary"
                        type="button"
                        disabled={choosing || saving}
                        onClick={() => camera.current?.click()}
                      >
                        <Camera size={19} />
                        {t('takePhoto')}
                      </button>
                      <button
                        className="secondary"
                        type="button"
                        disabled={choosing || saving}
                        onClick={() => gallery.current?.click()}
                      >
                        <ImagePlus size={19} />
                        {t('chooseImage')}
                      </button>
                    </div>
                    <input
                      hidden
                      ref={camera}
                      type="file"
                      accept="image/*"
                      capture="environment"
                      aria-label={t('takePhoto')}
                      onChange={(e) => {
                        void choose(e.target.files?.[0]);
                        e.target.value = '';
                      }}
                    />
                    <input
                      hidden
                      ref={gallery}
                      type="file"
                      accept="image/*"
                      aria-label={t('chooseImage')}
                      onChange={(e) => {
                        void choose(e.target.files?.[0]);
                        e.target.value = '';
                      }}
                    />
                    {choosing && (
                      <p role="status" className="muted">
                        {t('preparingImage')}
                      </p>
                    )}
                    {selected && (
                      <figure className="import-selected-image">
                        <BlobPreview blob={selected.blob} alt={t('selectedRecipeImage')} />
                        <figcaption>
                          <span>{t('imageSelected')}</span>
                          <button
                            type="button"
                            className="text-button"
                            onClick={() => {
                              setSelected(undefined);
                              setImageText('');
                              setImageTextOpen(false);
                            }}
                          >
                            <X size={16} />
                            {t('remove')}
                          </button>
                        </figcaption>
                      </figure>
                    )}
                    <p className="image-import-privacy">{t('imageImportPrivacy')}</p>
                    {imageTextOpen && (
                      <label>
                        {t('correctRecognizedText')}
                        <textarea
                          rows={9}
                          maxLength={100000}
                          value={imageText}
                          onChange={(e) => setImageText(e.target.value)}
                        />
                      </label>
                    )}
                  </>
                ) : (
                  <>
                    <details className="import-help">
                      <summary>{t('importHelp')}</summary>
                      <p className="intro-copy">{t('importHint')}</p>
                      <p className="muted">{t('importMetadataFirst')}</p>
                    </details>
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
                    <details
                      className="import-alternative"
                      open={Boolean(text || file || sourceID) || undefined}
                    >
                      <summary>{t('importAlternative')}</summary>{' '}
                      <label>
                        {t('importText')}
                        <textarea
                          rows={7}
                          maxLength={100000}
                          value={text}
                          onChange={(e) => setText(e.target.value)}
                        />
                      </label>
                      <label>
                        {t('importFile')}
                        <input
                          ref={fileInput}
                          type="file"
                          accept="image/jpeg,image/png,image/webp,application/pdf,video/mp4,video/webm"
                          onChange={(event) => {
                            const next = event.target.files?.[0] ?? null;
                            setFile(next);
                            setSourceID(null);
                            if (next) {
                              setConsent(false);
                            }
                          }}
                        />
                        <small>{t('importFileHint')}</small>
                      </label>
                      {(file || sourceID) && (
                        <p className="info-note">{file?.name ?? t('importRetainedSource')}</p>
                      )}
                    </details>
                  </>
                )}
                {ai && account === 'household' && (
                  <p className="muted import-ai-notice" id="import-ai-notice">
                    {t('importAIAutomatic')}
                  </p>
                )}
                {account === 'chatgpt' && (
                  <label className="check-row">
                    <input
                      type="checkbox"
                      checked={consent}
                      required
                      onChange={(e) => setConsent(e.target.checked)}
                    />
                    {t(
                      account === 'chatgpt'
                        ? 'chatgptImportConsent'
                        : mode === 'image'
                          ? 'imageAIConsent'
                          : 'aiConsent',
                    )}
                  </label>
                )}
                {error && (
                  <p role="alert" className="error-note">
                    {t(error)}
                  </p>
                )}
                <button
                  className="primary full"
                  aria-describedby={ai ? 'import-ai-notice' : undefined}
                  disabled={
                    saving ||
                    choosing ||
                    (account === 'chatgpt'
                      ? !text.trim() || !consent || !chatgpt?.model || chatgpt.state !== 'connected'
                      : mode === 'image'
                        ? !selected
                        : !url && !text.trim() && !file && !sourceID)
                  }
                >
                  {t(ai ? 'queueImportAI' : 'queueImport')}
                  <ArrowRight size={18} />
                </button>
              </form>
            </>
          )}
          <button className="text-button" onClick={() => manual()}>
            <Plus size={17} />
            {t('create')}
          </button>
        </section>
        <section aria-label={t('importing')}>
          <h2>{t('importing')}</h2>
          {!app.imports.some((task) => task.state !== 'cancelled') && (
            <p className="muted import-empty">{t('importEmpty')}</p>
          )}
          {app.imports
            .filter((task) => task.state !== 'cancelled')
            .map((task) => (
              <article
                className="import-job"
                key={task.id}
                id={'import-job-' + task.id}
                tabIndex={-1}
              >
                <div className="import-job-heading">
                  {task.body.image_id && (
                    <Photo
                      id={task.body.image_id}
                      className="import-job-photo"
                      alt={t('selectedRecipeImage')}
                    />
                  )}
                  <div>
                    <strong>
                      {task.recipe?.title ??
                        task.body.source_url ??
                        t(task.body.image_id ? 'recipePhoto' : 'importText')}
                    </strong>
                    <p className="muted">
                      {t(
                        task.state === 'saving' || task.state === 'cancel_pending'
                          ? 'processing'
                          : task.state,
                      )}
                    </p>
                  </div>
                </div>
                {task.error && (
                  <p className="import-job-error">
                    {t(errorKeys[task.error as keyof typeof errorKeys] ?? 'importFallback')}
                  </p>
                )}
                {task.state === 'needs_input' && (
                  <>
                    {!task.error && <p>{t('importFallback')}</p>}
                    <button className="text-button" onClick={() => void editSource(task)}>
                      {t(task.body.image_id ? 'correctRecognizedText' : 'edit')}
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
