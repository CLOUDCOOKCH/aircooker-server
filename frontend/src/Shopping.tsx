import { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, RefreshCw, ShoppingBag } from 'lucide-react';
import { useApp } from './model';
import { Empty, PageHeader } from './components';
import { addDays, displayDate } from './lib/domain';
import { parseShopping, SHOPPING_CACHE } from './lib/shopping';
import type { ShoppingSnapshot } from './lib/shopping';
import type { Key } from './i18n';

const itemLabels: Record<string, Key> = {
  not_sent: 'shoppingNotSent',
  pending: 'shoppingPending',
  synced: 'shoppingSynced',
  purchased: 'shoppingPurchased',
  removed_by_user: 'shoppingRemoved',
  manual: 'shoppingManual',
};
export function Shopping() {
  const app = useApp(),
    { t } = app;
  const [data, setData] = useState<ShoppingSnapshot | null>(null);
  const [stale, setStale] = useState(true),
    [error, setError] = useState<Key | null>(null);
  const [busy, setBusy] = useState(false),
    [confirmed, setConfirmed] = useState(false);
  const lock = useRef(false);
  const fetchSnapshot = async () => {
    const next = parseShopping(await app.api!.request('/api/v1/planning/shopping'));
    await app.store.setSetting(SHOPPING_CACHE, next);
    setData(next);
    setStale(false);
    return next;
  };
  useEffect(() => {
    let alive = true,
      loading = false;
    void app.store
      .setting<unknown>(SHOPPING_CACHE, null)
      .then((value) => {
        if (alive && value) {
          try {
            setData((previous) => previous ?? parseShopping(value));
          } catch {
            setError('shoppingLoadError');
          }
        }
      })
      .catch(() => {
        if (alive) setError('shoppingLoadError');
      });
    const refresh = async () => {
      if (loading || !alive || !app.api || !navigator.onLine) return;
      loading = true;
      try {
        const next = parseShopping(await app.api.request('/api/v1/planning/shopping'));
        await app.store.setSetting(SHOPPING_CACHE, next);
        if (alive) {
          setData(next);
          setStale(false);
          setError((old) => (old === 'shoppingLoadError' ? null : old));
        }
      } catch {
        if (alive) {
          setStale(true);
          setError('shoppingLoadError');
        }
      } finally {
        loading = false;
      }
    };
    setStale(true);
    void refresh();
    const timer = setInterval(() => void refresh(), 4000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [app.api, app.store, app.online]);
  const action = async (verify = false) => {
    if (lock.current || !app.api || !app.online || !data) return;
    lock.current = true;
    setBusy(true);
    setError(null);
    try {
      if (verify) {
        if (!confirmed) return;
        await app.api.request('/api/v1/integrations/bring/verify', {
          method: 'POST',
          body: JSON.stringify({ list_id: data.list_id, dedicated_test_list_confirmed: true }),
        });
        setConfirmed(false);
      } else {
        await app.sync();
        if ((await app.store.pending()).length) {
          setError('shoppingLocalPending');
          return;
        }
        await app.api.request('/api/v1/integrations/bring/reconcile', { method: 'POST' });
      }
      await fetchSnapshot();
    } catch {
      setError('shoppingActionError');
    } finally {
      setBusy(false);
      lock.current = false;
    }
  };
  const inProgress =
    data?.connection_state === 'ready' &&
    (data.job_state === 'running' || (data.job_state === 'queued' && !data.error_code));
  const verifying = data?.verification_state === 'running' || data?.verification_state === 'queued';
  const dateTime = (value: number) =>
    new Intl.DateTimeFormat(app.language, {
      dateStyle: 'medium',
      timeStyle: 'short',
      timeZone: app.household.timezone,
    }).format(value * 1000);
  const failure = (code: string | null | undefined): Key =>
    code === 'bring_capability_unverified'
      ? 'shoppingVerificationNeeded'
      : code === 'bring_uuid_not_supported' || code === 'bring_write_not_confirmed'
        ? 'shoppingUUIDError'
        : code === 'bring_configuration_changed'
          ? 'shoppingConfigurationChanged'
          : 'shoppingSyncError';
  return (
    <div className="shopping-page">
      <PageHeader
        title={t('shoppingTitle')}
        subtitle={
          data
            ? `${displayDate(data.period, app.language)} – ${displayDate(addDays(data.period, 6), app.language)}`
            : t('shoppingWeek')
        }
      />
      <p className="shopping-intro">{t('shoppingIntro')}</p>
      {app.demo && <p className="info-note">{t('demoUnavailable')}</p>}
      {(stale || !app.online) && data && (
        <p className="info-note" role="status">
          {t('shoppingCached')} {dateTime(data.calculated_at)}
        </p>
      )}
      {app.pending.length > 0 && (
        <p className="info-note" role="status">
          {t('shoppingLocalPending')}
        </p>
      )}
      {error && (
        <p className="error-note" role="alert">
          {t(error)}
        </p>
      )}
      {!data ? (
        <Empty
          title={t(app.demo ? 'demoUnavailable' : app.online ? 'loading' : 'shoppingNoCache')}
        />
      ) : (
        <>
          <section className="shopping-connection" aria-label={t('bring')}>
            <div>
              <h2>{data.list_name ?? t('bring')}</h2>
              <p>
                {t(
                  data.connection_state === 'ready'
                    ? 'shoppingReady'
                    : data.connection_state === 'compatibility_unverified'
                      ? 'shoppingVerificationNeeded'
                      : 'shoppingConnectFirst',
                )}
              </p>
            </div>
            <button
              className={
                (data.connection_state === 'ready' ? 'primary' : 'secondary') + ' shopping-sync'
              }
              onClick={() => void action()}
              disabled={
                busy ||
                verifying ||
                inProgress ||
                stale ||
                !app.online ||
                data.connection_state !== 'ready'
              }
            >
              <RefreshCw size={18} />
              {t(
                (data.connection_state === 'ready' && busy) || inProgress
                  ? 'shoppingSyncing'
                  : 'shoppingSync',
              )}
            </button>
            <div className="shopping-sync-status" role="status" aria-live="polite">
              {data.error_code &&
              !(
                data.error_code === 'bring_capability_unverified' &&
                data.connection_state === 'compatibility_unverified'
              ) ? (
                <p className="error-note">{t(failure(data.error_code))}</p>
              ) : inProgress ? (
                <p>{t('shoppingQueued')}</p>
              ) : null}
              {data.last_success_at && (
                <p className="muted">
                  {t('shoppingLastSuccess')} {dateTime(data.last_success_at)}
                </p>
              )}
            </div>
            {data.connection_state !== 'ready' && (
              <a
                className={
                  data.connection_state === 'compatibility_unverified' ? 'text-button' : 'primary'
                }
                href="/admin/#bring"
                target="_blank"
                rel="noreferrer"
              >
                {t('shoppingConfigure')} <ArrowUpRight size={16} />
              </a>
            )}
            {data.connection_state === 'compatibility_unverified' && (
              <details className="shopping-verification">
                <summary>{t('shoppingVerifyTitle')}</summary>
                <p>{t('shoppingVerifyHint')}</p>
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={confirmed}
                    onChange={(e) => setConfirmed(e.target.checked)}
                    disabled={busy || verifying}
                  />
                  {t('shoppingVerifyConsent')}
                </label>
                <button
                  className="secondary"
                  disabled={!confirmed || busy || verifying || stale || !app.online}
                  onClick={() => void action(true)}
                >
                  {t(verifying ? 'shoppingVerifying' : 'shoppingVerify')}
                </button>
                {data.verification_error && (
                  <p role="alert" className="error-note">
                    {t(failure(data.verification_error))} {t('shoppingTestLeftover')}
                  </p>
                )}
              </details>
            )}
          </section>
          <section aria-labelledby="shopping-ingredients">
            <div className="section-heading">
              <h2 id="shopping-ingredients">{t('ingredients')}</h2>
              <span className="muted">{data.requirements.length}</span>
            </div>
            {!data.requirements.length ? (
              <Empty title={t('shoppingEmpty')} body={t('shoppingEmptyHint')}>
                <ShoppingBag size={32} />
              </Empty>
            ) : (
              <ul className="shopping-items">
                {data.requirements.map((item) => (
                  <li key={item.id}>
                    <div>
                      <strong>{item.name}</strong>
                      <span className="shopping-spec">{item.spec}</span>
                    </div>
                    <span className={`shopping-item-state shopping-${item.state}`}>
                      {t(itemLabels[item.state])}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
          {data.excluded_staples.length > 0 && (
            <details className="shopping-excluded">
              <summary>
                {t('shoppingExcluded')} · {data.excluded_staples.length}
              </summary>
              <p>{t('shoppingExcludedHint')}</p>
              <p>{data.excluded_staples.join(', ')}</p>
            </details>
          )}
          <p className="muted shopping-footnote">{t('shoppingOwnership')}</p>
        </>
      )}
    </div>
  );
}
