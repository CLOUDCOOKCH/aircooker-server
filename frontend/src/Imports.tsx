import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Camera, ImagePlus, Link, Plus, X } from 'lucide-react';
import { useApp } from './model';
import { PageHeader, Photo } from './components';
import { uuid } from './lib/domain';
import type { ImportTask, Photo as StoredPhoto } from './lib/store';
import { prepareImportImage } from './lib/image-import';

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
  ai_not_configured: 'imageAINotConfigured',
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
  const [url, setURL] = useState(''),
    [text, setText] = useState(''),
    [imageText, setImageText] = useState(''),
    [imageTextOpen, setImageTextOpen] = useState(false),
    [selected, setSelected] = useState<StoredPhoto>(),
    [ai, setAI] = useState(false),
    [consent, setConsent] = useState(false),
    [error, setError] = useState<'invalid' | 'saveError' | 'imageInputError' | null>(null),
    [saving, setSaving] = useState(false),
    [choosing, setChoosing] = useState(false);
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
    setSaving(true);
    try {
      if (mode === 'image' ? !selected : !url && !text.trim()) {
        setError('invalid');
        return;
      }
      const importID = uuid();
      await app.store.saveImport(
        {
          id: importID,
          body: {
            source_url: mode === 'link' ? url || null : null,
            text: (mode === 'image' ? imageText : text) || null,
            image_id: mode === 'image' ? selected!.id : null,
            use_ai: ai,
            consent_external_ai: ai && consent,
          },
          state: 'queued',
        },
        mode === 'image' ? selected : undefined,
      );
      setURL('');
      setText('');
      setImageText('');
      setImageTextOpen(false);
      setSelected(undefined);
      setError(null);
      setQueuedFocus(importID);
      await app.changed();
    } catch {
      setError('saveError');
    } finally {
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
      setImageText(task.recognizedText ?? task.body.text ?? '');
      setImageTextOpen(Boolean(task.body.image_id));
      setSelected(task.body.image_id ? await app.store.photo(task.body.image_id) : undefined);
      setAI(Boolean(task.body.use_ai));
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
      <PageHeader title={t('importRecipe')} back={back} />
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
                {mode === 'image' ? (
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
                    <p className="intro-copy">{t('importHint')}</p>
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
                  </>
                )}
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
                    {t(mode === 'image' ? 'imageAIConsent' : 'aiConsent')}
                  </label>
                )}
                {error && (
                  <p role="alert" className="error-note">
                    {t(error)}
                  </p>
                )}
                <button
                  className="primary full"
                  disabled={
                    saving ||
                    choosing ||
                    (mode === 'image' ? !selected : !url && !text.trim()) ||
                    (ai && !consent)
                  }
                >
                  {t('queueImport')}
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
