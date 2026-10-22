import { useEffect, useRef, useState } from 'react';
import { useApp } from './model';
import type { components } from './api-schema';
import { APIError } from './lib/api';

type Status = components['schemas']['ChatGPTStatus'];
type Pairing = components['schemas']['ChatGPTPairing'];
type Catalog = components['schemas']['ChatGPTModelCatalog'];
const endpoint = '/api/v1/integrations/chatgpt';

export function ChatGPTSettings() {
  const app = useApp(),
    { t } = app;
  const [status, setStatus] = useState<Status | null>(null);
  const [pairing, setPairing] = useState<(Pairing & { before: string | null }) | null>(null);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [model, setModel] = useState('');
  const [personal, setPersonal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [notice, setNotice] = useState<
    'chatgptCopied' | 'chatgptPairExpired' | 'chatgptRevocationUnknown' | null
  >(null);
  const guard = useRef(false);
  const code = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let alive = true;
    if (app.api && !app.demo)
      void app.api
        .request<Status>(endpoint)
        .then((value) => {
          if (alive) {
            setStatus(value);
            setModel(value.model ?? '');
          }
        })
        .catch(() => {
          if (alive) setError(true);
        });
    return () => {
      alive = false;
    };
  }, [app.api, app.demo]);

  useEffect(() => {
    if (!pairing || !app.api) return;
    let alive = true;
    const timer = window.setInterval(() => {
      if (pairing.expires_at * 1000 <= Date.now()) {
        setPairing(null);
        setNotice('chatgptPairExpired');
        return;
      }
      if (!navigator.onLine || document.visibilityState !== 'visible') return;
      void app
        .api!.request<Status>(endpoint)
        .then((value) => {
          if (!alive) return;
          setStatus(value);
          if (value.state === 'connected' && value.connection_id !== pairing.before) {
            setPairing(null);
            setCatalog(null);
            setModel(value.model ?? '');
          }
        })
        .catch(() => undefined);
    }, 2500);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [pairing, app.api]);

  const act = async (work: () => Promise<void>) => {
    if (guard.current || !app.api || !app.online) return;
    guard.current = true;
    setBusy(true);
    setError(false);
    setNotice(null);
    try {
      await work();
    } catch (error) {
      setError(true);
      if (error instanceof APIError && error.code === 'chatgpt_reconnect_required')
        setStatus((value) => (value ? { ...value, state: 'reconnect_required' } : value));
    } finally {
      guard.current = false;
      setBusy(false);
    }
  };
  if (app.demo) return null;
  return (
    <section className="settings-group chatgpt-settings">
      <h2>{t('chatgptTitle')}</h2>
      <div className="settings-surface settings-copy">
        <p>{t('chatgptHint')}</p>
        {!status ? (
          <p role={error ? 'alert' : 'status'}>{t(error ? 'chatgptError' : 'loading')}</p>
        ) : (
          <>
            <p className="chatgpt-connection-state" role="status">
              <strong>
                {t(
                  status.state === 'connected'
                    ? 'chatgptConnected'
                    : status.state === 'reconnect_required'
                      ? 'chatgptReconnect'
                      : 'notConnected',
                )}
              </strong>
              {status.account_label && <span>{status.account_label}</span>}
            </p>
            {status.state === 'connected' && (
              <div className="chatgpt-model">
                {catalog ? (
                  <form
                    onSubmit={(event) => {
                      event.preventDefault();
                      void act(async () => {
                        const next = await app.api!.request<Status>(endpoint, {
                          method: 'PUT',
                          body: JSON.stringify({ connection_id: status.connection_id, model }),
                        });
                        setStatus(next);
                        setCatalog(null);
                      });
                    }}
                  >
                    <label>
                      {t('chatgptModel')}
                      <select
                        aria-label={t('chatgptModel')}
                        value={model}
                        required
                        disabled={busy || !app.online}
                        onChange={(event) => setModel(event.target.value)}
                      >
                        <option value="">{t('chatgptChooseModel')}</option>
                        {catalog.models.map((value) => (
                          <option key={value.slug} value={value.slug}>
                            {value.display_name}
                          </option>
                        ))}
                      </select>
                    </label>
                    {catalog.models.length === 0 && <p role="status">{t('chatgptNoModels')}</p>}
                    <button className="primary" disabled={busy || !app.online || !model}>
                      {t('save')}
                    </button>
                  </form>
                ) : (
                  <>
                    <p>
                      {status.model
                        ? `${t('chatgptModel')}: ${status.model}`
                        : t('chatgptChooseModel')}
                    </p>
                    <button
                      className="secondary"
                      disabled={busy || !app.online}
                      onClick={() =>
                        void act(async () =>
                          setCatalog(await app.api!.request<Catalog>(endpoint + '/models')),
                        )
                      }
                    >
                      {t('chatgptLoadModels')}
                    </button>
                  </>
                )}
              </div>
            )}
            {pairing ? (
              <div className="chatgpt-pairing">
                <ol>
                  <li>
                    <a href={endpoint + '/helper'} download="mealf-connect-chatgpt.py">
                      {t('chatgptDownload')}
                    </a>{' '}
                    {t('chatgptPython')}
                  </li>
                  <li>
                    {t('chatgptRunHelper')}
                    <code className="chatgpt-command">
                      py -3 mealf-connect-chatgpt.py --server {location.origin}
                    </code>
                  </li>
                  <li>{t('chatgptPasteCode')}</li>
                </ol>
                <label>
                  {t('chatgptPairCode')}
                  <input
                    ref={code}
                    readOnly
                    value={pairing.code}
                    spellCheck={false}
                    autoComplete="off"
                    onFocus={(event) => event.target.select()}
                  />
                </label>
                <small>{t('chatgptPairPrivacy')}</small>
                <div className="form-actions">
                  <button
                    className="secondary"
                    onClick={() => {
                      if (!navigator.clipboard) {
                        code.current?.focus();
                        code.current?.select();
                        return;
                      }
                      void navigator.clipboard
                        .writeText(pairing.code)
                        .then(() => setNotice('chatgptCopied'))
                        .catch(() => {
                          code.current?.focus();
                          code.current?.select();
                        });
                    }}
                  >
                    {t('chatgptCopy')}
                  </button>
                  <button
                    className="text-button"
                    disabled={busy || !app.online}
                    onClick={() =>
                      void act(async () => {
                        await app.api!.request(endpoint + '/pairing', { method: 'DELETE' });
                        setPairing(null);
                      })
                    }
                  >
                    {t('cancel')}
                  </button>
                </div>
                <p role="status">{t('chatgptWaiting')}</p>
              </div>
            ) : (
              <>
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={personal}
                    disabled={busy || !app.online}
                    onChange={(event) => setPersonal(event.target.checked)}
                  />
                  {t('chatgptPersonalConsent')}
                </label>
                <button
                  className="secondary"
                  disabled={busy || !app.online || !personal}
                  onClick={() =>
                    void act(async () => {
                      const next = await app.api!.request<Pairing>(endpoint + '/pairing', {
                        method: 'POST',
                        body: JSON.stringify({ personal_use_confirmed: true }),
                      });
                      setPairing({ ...next, before: status.connection_id ?? null });
                      setPersonal(false);
                    })
                  }
                >
                  {t(
                    status.state === 'connected' || status.state === 'reconnect_required'
                      ? 'chatgptReconnectAction'
                      : 'chatgptConnect',
                  )}
                </button>
              </>
            )}
            {(status.state !== 'disconnected' || status.account_label) && (
              <button
                className="text-button danger"
                disabled={busy || !app.online}
                onClick={() =>
                  void act(async () => {
                    const result = await app.api!.request<
                      components['schemas']['ChatGPTDisconnect']
                    >(endpoint, { method: 'DELETE' });
                    setPairing(null);
                    setCatalog(null);
                    setStatus(await app.api!.request<Status>(endpoint));
                    if (!result.remote_revocation_confirmed) setNotice('chatgptRevocationUnknown');
                  })
                }
              >
                {t('chatgptDisconnect')}
              </button>
            )}
          </>
        )}
        <p className="muted">
          {t('chatgptLimits')}{' '}
          <a href="https://chatgpt.com/#settings/Usage" target="_blank" rel="noreferrer">
            {t('chatgptUsage')}
          </a>
        </p>
        {!app.online && <p role="status">{t('aiSettingsOffline')}</p>}
        {status && error && (
          <p role="alert" className="error-note">
            {t('chatgptError')}
          </p>
        )}
        {notice && <p role="status">{t(notice)}</p>}
        {busy && <p role="status">{t('processing')}</p>}
      </div>
    </section>
  );
}
