import { useEffect, useState } from 'react';
import { Bell } from 'lucide-react';
import { useApp } from './model';
import { categories, uuid } from './lib/domain';
import { APIError } from './lib/api';
import type { Key } from './i18n';
import { pushKey, subscriptionFingerprint, subscriptionServerKey } from './lib/notifications';
import type { PushPreferences, PushStatus } from './lib/notifications';

const PATH = '/api/v1/notifications/push';
const DRAFT = 'push:preferences-draft';
const DEFAULTS: PushPreferences = {
  enabled: false,
  breakfast: '07:30',
  lunch: '12:00',
  dinner: '18:00',
};
export function ReminderSettings() {
  const app = useApp(),
    { t } = app;
  const [status, setStatus] = useState<PushStatus | null>(null);
  const [preferences, setPreferences] = useState<PushPreferences>(DEFAULTS);
  const [registration, setRegistration] = useState<ServiceWorkerRegistration | null>(null);
  const [fingerprint, setFingerprint] = useState<string | null>(null);
  const [boundKey, setBoundKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<Key | null>(null),
    [notice, setNotice] = useState<'saved' | 'queued' | null>(null);
  const [keyChanged, setKeyChanged] = useState(false);
  const supported =
    isSecureContext &&
    'Notification' in window &&
    'PushManager' in window &&
    'serviceWorker' in navigator;
  const [permission, setPermission] = useState<NotificationPermission>(
    supported ? Notification.permission : 'default',
  );
  const ios =
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const standalone =
    matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true;
  const needsInstall = ios && !standalone;
  const connected =
    status?.subscribed &&
    permission === 'granted' &&
    fingerprint === status.subscription_fingerprint &&
    boundKey === status.public_key;
  const dirty = JSON.stringify(preferences) !== JSON.stringify(status?.preferences);
  useEffect(() => {
    let alive = true;
    void (async () => {
      const cached = await app.store.setting<PushStatus | null>('push:status', null);
      const draft = await app.store.setting<PushPreferences | null>(DRAFT, null);
      if (alive) {
        setStatus(cached);
        setPreferences(draft ?? cached?.preferences ?? DEFAULTS);
      }
      if (app.demo || !app.api) return;
      if (app.online) {
        try {
          const current = await app.api.request<PushStatus>(PATH);
          await app.store.setSetting('push:status', current);
          if (alive) {
            setStatus(current);
            setPreferences(draft ?? current.preferences);
          }
        } catch {
          if (alive) setError('pushError');
        }
      }
      if (supported && !needsInstall) {
        const worker = await Promise.race([
          navigator.serviceWorker.ready,
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('worker_not_ready')), 10000),
          ),
        ]);
        const permission = Notification.permission;
        if (alive) {
          setRegistration(worker);
          setPermission(permission);
        }
        // A fresh Settings visit must not touch the platform push service before
        // permission is granted. In particular, native WebKit subscription discovery
        // may depend on an unavailable OS service. Connect performs it after consent.
        if (permission !== 'granted') return;
        const subscription = await worker.pushManager.getSubscription();
        const value = subscription ? await subscriptionFingerprint(subscription) : null;
        if (alive) {
          setFingerprint(value);
          setBoundKey(subscription ? subscriptionServerKey(subscription) : null);
          setPermission(Notification.permission);
        }
      }
    })().catch(() => {
      if (alive) setError('pushError');
    });
    return () => {
      alive = false;
    };
  }, [app.store, app.online]);
  useEffect(() => {
    const refresh = () => {
      if (supported) setPermission(Notification.permission);
      if (app.api && navigator.onLine && document.visibilityState === 'visible')
        void app.api
          .request<PushStatus>(PATH)
          .then(setStatus)
          .catch(() => setError('pushError'));
    };
    const timer = setInterval(refresh, 30000);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      clearInterval(timer);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, [app.api]);
  const update = (value: PushPreferences) => {
    setPreferences(value);
    setNotice(null);
    setError(null);
    void app.store.setSetting(DRAFT, value).catch(() => setError('pushError'));
  };
  const remember = async (value: PushStatus) => {
    await app.store.setSetting('push:status', value);
    await app.store.setSetting(DRAFT, null);
    setStatus(value);
    setPreferences(value.preferences);
  };
  const connect = async () => {
    if (!app.api || !registration || !status) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    setKeyChanged(false);
    try {
      // This is the first awaited operation after the user's click, preserving activation.
      const granted = await Notification.requestPermission();
      setPermission(granted);
      if (granted !== 'granted') return;
      const existing = await registration.pushManager.getSubscription();
      const expected = new Uint8Array(pushKey(status.public_key));
      const bound = existing?.options.applicationServerKey;
      if (
        existing &&
        (!bound ||
          new Uint8Array(bound).some((value, index) => value !== expected[index]) ||
          bound.byteLength !== expected.byteLength)
      ) {
        setKeyChanged(true);
        return;
      }
      const subscription =
        existing ??
        (await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: expected,
        }));
      const value = subscription.toJSON();
      if (!value.endpoint || !value.keys?.p256dh || !value.keys?.auth)
        throw new Error('invalid_subscription');
      const current = await app.api.request<PushStatus>(PATH + '/subscription', {
        method: 'PUT',
        body: JSON.stringify({
          endpoint: value.endpoint,
          keys: value.keys,
          preferences,
          language: app.language,
        }),
      });
      await remember(current);
      setFingerprint(await subscriptionFingerprint(subscription));
      setBoundKey(status.public_key);
    } catch (failure) {
      setError(
        failure instanceof APIError && failure.code === 'push_endpoint_unsupported'
          ? 'pushVendorUnsupported'
          : 'pushError',
      );
    } finally {
      setBusy(false);
    }
  };
  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!app.api) return;
    setBusy(true);
    setError(null);
    try {
      await remember(
        await app.api.request<PushStatus>(PATH + '/preferences', {
          method: 'PUT',
          body: JSON.stringify({ preferences, language: app.language }),
        }),
      );
      setNotice('saved');
    } catch {
      setError('pushError');
    } finally {
      setBusy(false);
    }
  };
  const disconnect = async () => {
    if (!app.api || !registration) return;
    setBusy(true);
    setError(null);
    try {
      await app.api.request(PATH + '/subscription', { method: 'DELETE' });
      await remember(await app.api.request<PushStatus>(PATH));
      setFingerprint(null);
      setBoundKey(null);
      await (await registration.pushManager.getSubscription())?.unsubscribe();
      setKeyChanged(false);
    } catch {
      setError('pushError');
    } finally {
      setBusy(false);
    }
  };
  const queue = async (kind: 'test' | 'retry') => {
    if (!app.api) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await app.api.request(PATH + '/' + kind, {
        method: 'POST',
        body: kind === 'test' ? JSON.stringify({ request_id: uuid() }) : undefined,
      });
      setStatus(await app.api.request<PushStatus>(PATH));
      setNotice('queued');
    } catch {
      setError('pushError');
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="settings-group">
      <h2>{t('pushReminders')}</h2>
      <div className="settings-surface">
        <div className="settings-row">
          <div>
            <strong>{t('pushHeading')}</strong>
            <small>{app.household.timezone}</small>
          </div>
          <Bell size={22} />
        </div>
        <p className="settings-description">{t('pushBody')}</p>
        {app.demo ? (
          <p className="settings-description">{t('demoUnavailable')}</p>
        ) : needsInstall ? (
          <p className="settings-description">{t('pushInstall')}</p>
        ) : !supported ? (
          <p className="settings-description">{t('pushUnsupported')}</p>
        ) : (
          <>
            {permission === 'denied' && <p className="settings-description">{t('pushDenied')}</p>}
            {status && !status.available && (
              <p className="settings-description">{t('pushHttps')}</p>
            )}
            {!app.online && <p className="settings-description">{t('pushOffline')}</p>}
            {!connected && (
              <button
                className="settings-row"
                disabled={
                  busy ||
                  !app.online ||
                  !registration ||
                  !status?.available ||
                  permission === 'denied'
                }
                onClick={() => void connect()}
              >
                {t('pushConnect')}
              </button>
            )}
            {connected && (
              <form className="reminder-form" onSubmit={(event) => void save(event)}>
                <fieldset disabled={busy}>
                  <legend className="sr-only">{t('pushReminders')}</legend>
                  <label className="check-row">
                    <input
                      type="checkbox"
                      checked={preferences.enabled ?? false}
                      onChange={(event) =>
                        update({ ...preferences, enabled: event.target.checked })
                      }
                    />
                    {t('pushEnabled')}
                  </label>
                  {categories.map((category) => (
                    <div className="reminder-time" key={category}>
                      <label className="check-row">
                        <input
                          type="checkbox"
                          checked={preferences[category] != null}
                          onChange={(event) =>
                            update({
                              ...preferences,
                              [category]: event.target.checked ? DEFAULTS[category] : null,
                            })
                          }
                        />
                        {t(category)}
                      </label>
                      <label>
                        <span className="sr-only">
                          {t('pushTime')} · {t(category)}
                        </span>
                        <input
                          type="time"
                          required={preferences[category] != null}
                          disabled={preferences[category] == null}
                          value={preferences[category] ?? ''}
                          onChange={(event) =>
                            update({ ...preferences, [category]: event.target.value })
                          }
                        />
                      </label>
                    </div>
                  ))}
                  <p className="muted">{t('pushSaveHint')}</p>
                  <button className="secondary full" disabled={!app.online}>
                    {t('pushSave')}
                  </button>
                </fieldset>
              </form>
            )}
            {connected && (
              <>
                <button
                  className="settings-row"
                  disabled={busy || !app.online || dirty || !status?.preferences.enabled}
                  onClick={() => void queue('test')}
                >
                  {t('pushTest')}
                </button>
                {!!status?.failed_jobs && (
                  <button
                    className="settings-row"
                    disabled={busy || !app.online}
                    onClick={() => void queue('retry')}
                  >
                    {t('pushRetry')} · {status.failed_jobs}
                  </button>
                )}
              </>
            )}
            {fingerprint && (
              <button
                className="settings-row"
                disabled={busy || !app.online}
                onClick={() => void disconnect()}
              >
                {t('pushDisconnect')}
              </button>
            )}
            {(keyChanged || (!!fingerprint && !!status && boundKey !== status.public_key)) && (
              <p className="settings-description" role="alert">
                {t('pushKeyChanged')}
              </p>
            )}
            {!!status?.pending_jobs && (
              <p className="settings-description" role="status">
                {status.pending_jobs} {t('pushPending')}
              </p>
            )}
            {status?.last_success && (
              <p className="settings-description">
                {t('pushLastAccepted')}{' '}
                {new Date(status.last_success * 1000).toLocaleString(app.language)}
              </p>
            )}
            {status?.error_code && (
              <p className="settings-description" role="alert">
                {t(
                  status.error_code === 'push_subscription_expired' ||
                    status.error_code === 'push_session_expired'
                    ? 'pushExpired'
                    : 'pushDeliveryError',
                )}
              </p>
            )}
          </>
        )}
        {notice && (
          <p className="settings-description" role="status">
            {t(notice === 'saved' ? 'pushSaved' : 'pushQueued')}
          </p>
        )}
        {error && (
          <p className="settings-description" role="alert">
            {t(error)}
          </p>
        )}
        <p className="settings-description">{t('pushPrivacy')}</p>
      </div>
    </section>
  );
}
