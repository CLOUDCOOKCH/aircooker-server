import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';
import type { components } from './api-schema';
import { useApp } from './model';
import { PageHeader, Photo } from './components';
import { payload, uuid } from './lib/domain';
import type { Recipe } from './lib/domain';
import { APIError } from './lib/api';
import { ideaError } from './lib/idea-errors';

type Status = components['schemas']['AISettingsStatus'];
type Job = components['schemas']['IdeaStatus'];
type Request = components['schemas']['IdeaRequest'];
type Draft = {
  mode: 'ingredients' | 'surprise';
  ingredients: string;
  request?: Request;
  job?: Job;
};
const CACHE = 'recipe-ideas:v1';
export function RecipeIdeas({
  back,
  review,
}: {
  back: () => void;
  review: (recipe: Recipe, draftID: string) => void;
}) {
  const app = useApp(),
    { t } = app;
  const [draft, setDraft] = useState<Draft>({ mode: 'ingredients', ingredients: '' });
  const [ready, setReady] = useState(false),
    [status, setStatus] = useState<Status | null>(null);
  const [consent, setConsent] = useState(false),
    [error, setError] = useState<string | null>(null),
    [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const cacheReadable = useRef(false);
  const configured =
    status?.enabled &&
    status.input_formats?.includes('text') &&
    status.provider &&
    status.base_url &&
    status.model;
  const pending =
    !!draft.request && (!draft.job || ['queued', 'running'].includes(draft.job.state));
  useEffect(() => {
    let alive = true;
    void app.store
      .setting<Draft>(CACHE, { mode: 'ingredients', ingredients: '' })
      .then((value) => {
        if (value.mode !== 'ingredients' && value.mode !== 'surprise') throw new Error('invalid');
        if (typeof value.ingredients !== 'string' || value.ingredients.length > 2000)
          throw new Error('invalid');
        value.job?.recipes?.forEach((recipe) => payload('recipe', recipe));
        if (alive) {
          cacheReadable.current = true;
          setDraft(value);
          setReady(true);
        }
      })
      .catch(() => {
        if (alive) {
          setReady(true);
          setError('local_storage_unavailable');
        }
      });
    return () => {
      alive = false;
    };
  }, [app.store]);
  useEffect(() => {
    if (ready && cacheReadable.current)
      void app.store.setSetting(CACHE, draft).catch(() => setError('local_storage_unavailable'));
  }, [ready, draft, app.store]);
  useEffect(() => {
    if (!app.api || !app.online || app.demo) return;
    let alive = true;
    void app.api
      .request<Status>('/api/v1/admin/ai')
      .then((value) => {
        if (alive) {
          setStatus(value);
          setConsent(false);
        }
      })
      .catch((e) => {
        if (alive) setError(e instanceof APIError ? e.code : 'connection_unavailable');
      });
    return () => {
      alive = false;
    };
  }, [app.api, app.online]);
  useEffect(() => {
    if (!ready || !pending || !app.api || !app.online || !draft.request) return;
    let alive = true,
      polling = false;
    const request = draft.request;
    const poll = async () => {
      if (polling || !alive) return;
      polling = true;
      try {
        let job: Job;
        try {
          job = await app.api!.request<Job>('/api/v1/recipe-ideas/' + request.request_id);
        } catch (e) {
          if (!(e instanceof APIError) || e.status !== 404) throw e;
          job = await app.api!.request<Job>('/api/v1/recipe-ideas', {
            method: 'POST',
            body: JSON.stringify(request),
          });
        }
        job.recipes?.forEach((recipe) => payload('recipe', recipe));
        if (alive) {
          setDraft((current) => ({ ...current, job }));
          setError(null);
        }
      } catch (e) {
        if (alive) {
          setError(e instanceof APIError ? e.code : 'connection_unavailable');
          if (e instanceof APIError && e.status >= 400 && e.status < 500) {
            setDraft((current) => ({
              ...current,
              job: { id: request.request_id, state: 'failed', recipes: [], error_code: e.code },
            }));
            setConsent(false);
            void app
              .api!.request<Status>('/api/v1/admin/ai')
              .then(setStatus)
              .catch(() => undefined);
          }
        }
      } finally {
        polling = false;
      }
    };
    void poll();
    const timer = setInterval(() => void poll(), 2500);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [ready, pending, app.api, app.online, draft.request?.request_id]);
  const generate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (lock.current || pending || !configured || !consent || !app.online || !app.api) return;
    lock.current = true;
    setBusy(true);
    setError(null);
    try {
      const request: Request = {
        request_id: uuid(),
        mode: draft.mode,
        ingredients: draft.mode === 'ingredients' ? draft.ingredients.trim() : '',
        language: app.language,
        consent_external_ai: true,
        ai_destination: [status!.provider!, status!.base_url!, status!.model!],
      };
      const next = { ...draft, request, job: undefined };
      await app.store.setSetting(CACHE, next);
      cacheReadable.current = true;
      setDraft(next);
    } catch {
      setError('local_storage_unavailable');
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const failed = draft.job?.state === 'failed' || draft.job?.state === 'expired';
  const failure = ideaError(
    error ?? draft.job?.error_code,
    !error && draft.job?.state === 'expired',
  );
  return (
    <>
      <PageHeader title={t('recipeIdeas')} subtitle={t('ideasIntro')} back={back} />
      <div className="ideas-layout">
        <form
          className="ideas-form"
          onSubmit={(event) => void generate(event)}
          aria-busy={pending || busy}
        >
          <fieldset disabled={pending || busy || !ready}>
            <legend>{t('ideasMode')}</legend>
            <div className="ideas-modes">
              {(['ingredients', 'surprise'] as const).map((mode) => (
                <label className="check-row" key={mode}>
                  <input
                    type="radio"
                    name="idea-mode"
                    checked={draft.mode === mode}
                    onChange={() => {
                      setDraft((current) => ({ ...current, mode }));
                      setConsent(false);
                    }}
                  />
                  {t(mode === 'ingredients' ? 'ideasUseMine' : 'ideasSurprise')}
                </label>
              ))}
            </div>
            {draft.mode === 'ingredients' && (
              <label>
                {t('ideasIngredients')}
                <textarea
                  rows={4}
                  maxLength={2000}
                  required
                  value={draft.ingredients}
                  placeholder={t('ideasPlaceholder')}
                  onChange={(event) => {
                    setDraft((current) => ({ ...current, ingredients: event.target.value }));
                    setConsent(false);
                  }}
                />
              </label>
            )}
            {draft.mode === 'surprise' && <p className="muted">{t('ideasSurpriseHint')}</p>}
            {configured ? (
              <>
                <p className="ideas-provider">
                  {status!.provider} · {status!.model}
                  <br />
                  <span className="muted">{status!.base_url}</span>
                </p>
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={consent}
                    onChange={(event) => setConsent(event.target.checked)}
                  />
                  {t('ideasConsent')}
                </label>
              </>
            ) : app.online || app.demo ? (
              <p className="info-note">
                {t(app.demo ? 'demoUnavailable' : status === null ? 'loading' : 'ideasConfigure')}
              </p>
            ) : null}
            <button
              className="primary full"
              disabled={
                !configured ||
                !consent ||
                !app.online ||
                pending ||
                busy ||
                (draft.mode === 'ingredients' && !draft.ingredients.trim())
              }
            >
              <Sparkles size={18} />
              {t(pending || busy ? 'ideasGenerating' : 'ideasGenerate')}
            </button>
          </fieldset>
          {!app.online && (
            <p className="info-note" role="status">
              {t('ideasOffline')}
            </p>
          )}
          {pending && (
            <p role="status" className="info-note">
              {t('ideasQueued')}
            </p>
          )}
          {(error || failed) && (
            <div className="error-note" role="alert">
              <p>{t(failure.message)}</p>
              {failure.code && (
                <p>
                  {t('ideasErrorCode')} <code>{failure.code}</code>
                </p>
              )}
              {failed && (
                <button
                  type="button"
                  className="text-button"
                  onClick={() => {
                    back();
                    app.setTab('settings');
                  }}
                >
                  {t('ideasOpenSettings')}
                </button>
              )}
              {error && !failed && (
                <button type="button" className="text-button" onClick={() => location.reload()}>
                  {t('retry')}
                </button>
              )}
            </div>
          )}
        </form>
        <section className="ideas-results" aria-label={t('recipeIdeas')} aria-live="polite">
          <p className="info-note">{t('ideasReviewHint')}</p>
          {draft.job?.state === 'ready'
            ? (draft.job.recipes ?? []).map((value, index) => {
                const recipe = payload('recipe', value);
                return (
                  <article className="idea-result" key={draft.job!.id + ':' + index}>
                    <Photo id={null} />
                    <div>
                      <h2>{recipe.title}</h2>
                      <p>{recipe.description}</p>
                      <details>
                        <summary>
                          {t('ingredients')} · {recipe.ingredients.length}
                        </summary>
                        <ul>
                          {recipe.ingredients.map((item) => (
                            <li key={item.id}>
                              {item.name}
                              {item.quantity ? ` · ${item.quantity} ${item.unit}` : ''}
                            </li>
                          ))}
                        </ul>
                      </details>
                      <button
                        className="text-button"
                        onClick={() => review(recipe, `recipe-idea:${draft.job!.id}:${index}`)}
                      >
                        {t('ideasReview')}
                        <ArrowRight size={17} />
                      </button>
                    </div>
                  </article>
                );
              })
            : !pending && (
                <div className="ideas-empty">
                  <Sparkles size={28} />
                  <h2>{t('ideasEmpty')}</h2>
                  <p className="muted">{t('ideasEmptyHint')}</p>
                </div>
              )}
        </section>
      </div>
    </>
  );
}
