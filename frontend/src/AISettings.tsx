import { useEffect, useRef, useState } from 'react';
import { useApp } from './model';
import type { components } from './api-schema';

type Status = components['schemas']['AISettingsStatus'];
type Catalog = components['schemas']['AIProviderCatalog'];
const labels: Record<string, string> = {
  gemini: 'Google Gemini',
  openai: 'OpenAI',
  openrouter: 'OpenRouter',
  'openai-compatible': 'Custom OpenAI-compatible API',
  anthropic: 'Anthropic',
  ollama: 'Ollama',
  openwebui: 'OpenWebUI',
};

export function AISettings() {
  const app = useApp(),
    { t } = app;
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [profile, setProfile] = useState<Status | null>(null);
  const [key, setKey] = useState(''),
    [clear, setClear] = useState(false);
  const [enabled, setEnabled] = useState(false),
    [busy, setBusy] = useState(false);
  const [error, setError] = useState(false),
    [saved, setSaved] = useState(false);
  const guard = useRef(false);
  useEffect(() => {
    let alive = true;
    if (app.api && !app.demo)
      void app.api
        .request<Catalog>('/api/v1/admin/ai/providers')
        .then((value) => {
          if (!alive) return;
          setCatalog(value);
          const selected =
            value.profiles.find((p) => p.provider === value.default_provider) ?? value.profiles[0];
          setProfile(selected);
          setEnabled(value.enabled);
        })
        .catch(() => {
          if (alive) setError(true);
        });
    return () => {
      alive = false;
    };
  }, [app.api, app.demo]);
  if (app.demo) return null;
  const update = (value: Partial<Status>) => {
    if (profile) setProfile({ ...profile, ...value });
    setSaved(false);
  };
  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!app.api || !profile || guard.current) return;
    guard.current = true;
    setBusy(true);
    setError(false);
    setSaved(false);
    try {
      await app.api.request('/api/v1/admin/ai', {
        method: 'PUT',
        body: JSON.stringify({
          enabled,
          provider: profile.provider,
          base_url: profile.base_url,
          model: profile.model,
          api_key: clear ? '' : key || undefined,
          input_formats: profile.input_formats,
          requests_per_hour: profile.requests_per_hour,
          timeout: profile.timeout,
          max_content: profile.max_content,
          structured_output: profile.structured_output,
          allow_local_http: profile.allow_local_http,
        }),
      });
      const value = await app.api.request<Catalog>('/api/v1/admin/ai/providers');
      setCatalog(value);
      setProfile(value.profiles.find((p) => p.provider === profile.provider) ?? profile);
      setSaved(true);
    } catch {
      setError(true);
    } finally {
      setKey('');
      setClear(false);
      guard.current = false;
      setBusy(false);
    }
  };
  return (
    <section className="settings-group">
      <h2>{t('aiSettingsTitle')}</h2>
      <div className="settings-surface">
        <p className="settings-description">{t('aiSettingsHint')}</p>
        {catalog && (
          <p className="settings-description">
            {t('aiDefault')}: {labels[catalog.default_provider] ?? catalog.default_provider}
          </p>
        )}
        {!profile ? (
          <p role={error ? 'alert' : 'status'}>{t(error ? 'aiSettingsError' : 'processing')}</p>
        ) : (
          <form onSubmit={(event) => void save(event)} className="ai-settings-form">
            <fieldset disabled={busy || !app.online}>
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(event) => {
                    setEnabled(event.target.checked);
                    setSaved(false);
                  }}
                />
                {t('aiEnable')}
              </label>
              <label>
                {t('aiProvider')}
                <select
                  aria-label={t('aiProvider')}
                  value={profile.provider ?? 'gemini'}
                  onChange={(event) => {
                    const next = catalog?.profiles.find((p) => p.provider === event.target.value);
                    if (next) {
                      setProfile(next);
                      setKey('');
                      setClear(false);
                      setSaved(false);
                    }
                  }}
                >
                  {catalog?.profiles.map((p) => (
                    <option key={p.provider} value={p.provider ?? ''}>
                      {labels[p.provider ?? ''] ?? p.provider}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                {t('aiEndpoint')}
                <input
                  type="url"
                  required={enabled}
                  maxLength={2048}
                  value={profile.base_url ?? ''}
                  onChange={(event) => update({ base_url: event.target.value })}
                />
              </label>
              <label>
                {t('aiModel')}
                <input
                  required={enabled}
                  maxLength={200}
                  value={profile.model ?? ''}
                  onChange={(event) => update({ model: event.target.value })}
                />
              </label>
              <label>
                {t('aiKey')}
                <input
                  type="password"
                  autoComplete="off"
                  maxLength={8192}
                  value={key}
                  onChange={(event) => setKey(event.target.value)}
                />
              </label>
              <small>{t(profile.key_configured ? 'aiKeyStored' : 'aiKeyHint')}</small>
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={clear}
                  onChange={(event) => setClear(event.target.checked)}
                />
                {t('aiClearKey')}
              </label>
              <fieldset>
                <legend>{t('aiFormats')}</legend>
                <p>{t('aiFormatsHint')}</p>
                {(profile.available_formats ?? [])
                  .filter((format) => format !== 'text')
                  .map((format) => (
                    <label className="check-row" key={format}>
                      <input
                        type="checkbox"
                        checked={profile.input_formats?.includes(format) ?? false}
                        onChange={(event) =>
                          update({
                            input_formats: event.target.checked
                              ? [...(profile.input_formats ?? ['text']), format]
                              : profile.input_formats?.filter((f) => f !== format),
                          })
                        }
                      />
                      {t(
                        (
                          {
                            image: 'aiImages',
                            pdf: 'aiPDF',
                            video: 'aiVideo',
                            youtube: 'aiYouTube',
                          } as Record<string, 'aiImages' | 'aiPDF' | 'aiVideo' | 'aiYouTube'>
                        )[format],
                      )}
                    </label>
                  ))}
              </fieldset>
              <label>
                {t('aiHourlyLimit')}
                <input
                  type="number"
                  min={1}
                  max={1000}
                  required
                  value={profile.requests_per_hour ?? 20}
                  onChange={(event) => update({ requests_per_hour: Number(event.target.value) })}
                />
              </label>
              <label>
                {t('aiTimeout')}
                <input
                  type="number"
                  min={1}
                  max={120}
                  required
                  value={profile.timeout ?? 30}
                  onChange={(event) => update({ timeout: Number(event.target.value) })}
                />
              </label>
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={profile.structured_output ?? false}
                  onChange={(event) => update({ structured_output: event.target.checked })}
                />
                {t('aiStructured')}
              </label>
              {['openai-compatible', 'ollama', 'openwebui'].includes(profile.provider ?? '') && (
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={profile.allow_local_http ?? false}
                    onChange={(event) => update({ allow_local_http: event.target.checked })}
                  />
                  {t('aiLocalHTTP')}
                </label>
              )}
              <button className="primary" disabled={busy}>
                {t(busy ? 'processing' : 'aiSaveDefault')}
              </button>
            </fieldset>
          </form>
        )}
        {!app.online && <p role="status">{t('aiSettingsOffline')}</p>}
        {profile && error && (
          <p role="alert" className="error-note">
            {t('aiSettingsError')}
          </p>
        )}
        {saved && (
          <p role="status" className="success-note">
            {t('aiSettingsSaved')}
          </p>
        )}
      </div>
    </section>
  );
}
