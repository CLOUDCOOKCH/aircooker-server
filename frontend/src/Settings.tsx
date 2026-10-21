import { useEffect, useState } from 'react';
import { ArrowUpRight, Download, LogOut, RefreshCw, ShieldCheck, Smartphone } from 'lucide-react';
import { useApp } from './model';
import type { Tab } from './model';
import { PageHeader, Sheet } from './components';
import { ReminderSettings } from './ReminderSettings';
import { PlanningSettings } from './PlanningSettings';
import type { Language } from './i18n';
import { rebuildFromServer } from './lib/recovery';
import { cloneRecipe } from './lib/planning';
import { uuid } from './lib/domain';
import type { Recipe } from './lib/domain';
import type { LocalStore } from './lib/store';
function download(value: unknown, name: string) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }),
  );
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function Settings({
  logout,
  reauthenticate,
}: {
  logout: () => Promise<void>;
  reauthenticate: () => void;
}) {
  const app = useApp(),
    { t } = app;
  const [start, setStart] = useState<Tab>('home'),
    [persisted, setPersisted] = useState(false),
    [confirm, setConfirm] = useState(false),
    [error, setError] = useState(false),
    [bring, setBring] = useState<Record<string, unknown> | null>(null);
  const [recovery, setRecovery] = useState(false),
    [recovering, setRecovering] = useState(false);
  const [archives, setArchives] = useState<Awaited<ReturnType<LocalStore['archives']>>>([]);
  useEffect(() => {
    void app.store.archives().then(setArchives);
  }, [app.store, app.pending]);
  const recover = async () => {
    if (!app.api) return;
    setRecovering(true);
    try {
      await rebuildFromServer(app.store, app.api);
      setRecovery(false);
      await app.changed();
    } catch {
      setError(true);
    } finally {
      setRecovering(false);
    }
  };
  useEffect(() => {
    void app.store.setting<Tab>('start', 'home').then(setStart);
    void navigator.storage?.persisted?.().then(setPersisted);
    if (app.api)
      void app.api
        .request<Record<string, unknown>>('/api/v1/integrations/bring/status')
        .then(setBring)
        .catch(() => undefined);
  }, [app.store, app.api]);
  const protect = async () => {
    try {
      setPersisted(await navigator.storage.persist());
    } catch {
      setError(true);
    }
  };
  const exportLocal = async () => {
    try {
      const value = await app.store.localExport();
      download(value, 'mealf-pending-work.json');
    } catch {
      setError(true);
    }
  };
  return (
    <>
      <PageHeader title={t('settings')} />
      <div className="settings-columns">
        <div>
          <section className="settings-group">
            <h2>{t('account')}</h2>
            <div className="settings-surface">
              <div className="settings-row">
                <div>
                  <strong>{app.household.name}</strong>
                  <small>{app.household.timezone}</small>
                </div>
                <ShieldCheck size={22} />
              </div>
              <label className="settings-row">
                {t('language')}
                <select
                  aria-label={t('language')}
                  value={app.language}
                  onChange={(e) => void app.setLanguage(e.target.value as Language)}
                >
                  <option value="en">English</option>
                  <option value="de">Deutsch</option>
                </select>
              </label>
              <label className="settings-row">
                {t('startScreen')}
                <select
                  value={start}
                  onChange={(e) => {
                    setStart(e.target.value as Tab);
                    void app.store.setSetting('start', e.target.value);
                  }}
                >
                  {(['home', 'calendar', 'recipes'] as const).map((tab) => (
                    <option key={tab} value={tab}>
                      {t(tab)}
                    </option>
                  ))}
                </select>
              </label>
              <div className="settings-row muted">{t('appearance')}</div>
              {!app.demo && (
                <a className="settings-row" href="/" target="_blank" rel="noreferrer">
                  {t('openAdmin')}
                  <ArrowUpRight size={18} />
                </a>
              )}
            </div>
          </section>
          <PlanningSettings />
          <ReminderSettings />
          <section className="settings-group">
            <h2>{t('bring')}</h2>
            <div className="settings-surface">
              <div className="settings-row">
                <div>
                  <strong>{t('bringBody')}</strong>
                  <small>
                    {t(
                      bring?.state === 'configured'
                        ? 'bringConnected'
                        : bring?.state === 'compatibility_unverified'
                          ? 'bringUnverified'
                          : 'bringUnconfigured',
                    )}
                  </small>
                </div>
              </div>
              {!app.demo && (
                <>
                  {bring?.automatic_mutations !== true && (
                    <p className="settings-description">{t('bringProtected')}</p>
                  )}
                  {bring?.automatic_mutations === true && (
                    <button
                      className="settings-row"
                      onClick={() =>
                        void app
                          .api!.request('/api/v1/integrations/bring/reconcile', { method: 'POST' })
                          .then(() => app.setNotice('reconciliationQueued'))
                          .catch(() => setError(true))
                      }
                    >
                      {t('reconcile')}
                      <RefreshCw size={18} />
                    </button>
                  )}
                  <a className="settings-row" href="/#bring" target="_blank" rel="noreferrer">
                    {t('openAdmin')}
                    <ArrowUpRight size={18} />
                  </a>
                </>
              )}
              {app.demo && <p className="settings-description">{t('demoUnavailable')}</p>}
            </div>
          </section>
          <section className="settings-group">
            <h2>{t('device')}</h2>
            <div className="settings-surface">
              <button
                className="settings-row"
                onClick={() => void app.sync()}
                disabled={app.demo || app.syncing}
              >
                <span>
                  {t('sync')} · {app.pending.length} {t('pending')}
                </span>
                <RefreshCw size={17} />
              </button>
              {!app.demo && (
                <button className="settings-row" onClick={reauthenticate}>
                  {t('signInAgain')}
                  <ArrowUpRight size={18} />
                </button>
              )}
              <button
                className="settings-row danger"
                onClick={() => (app.demo ? void logout() : setConfirm(true))}
              >
                {t(app.demo ? 'exitDemo' : 'logout')}
                <LogOut size={18} />
              </button>
            </div>
          </section>
        </div>
        <div>
          <section className="settings-group">
            <h2>{t('installation')}</h2>
            <div className="settings-surface settings-copy">
              <Smartphone size={28} strokeWidth={1.4} />
              <p>{t('installHint')}</p>
              <p className="muted">{t('reminderLimits')}</p>
            </div>
          </section>
          <section className="settings-group">
            <h2>{t('storage')}</h2>
            <div className="settings-surface">
              <div className="settings-copy">
                <strong>{t(persisted ? 'persisted' : 'persistenceUnknown')}</strong>
                <p className="muted">{t('persistenceHint')}</p>
              </div>
              <button className="settings-row" onClick={() => void protect()}>
                {t('persist')}
                <ShieldCheck size={18} />
              </button>
              <button className="settings-row" onClick={() => void exportLocal()}>
                {t('localBackup')}
                <Download size={18} />
              </button>
            </div>
          </section>
          {!app.demo && (
            <section className="settings-group">
              <h2>{t('recover')}</h2>
              <p className="muted">{t('recoverHint')}</p>
              <button
                className="text-button"
                disabled={!app.online}
                onClick={() => setRecovery(true)}
              >
                {t('recover')}
              </button>
            </section>
          )}
          {archives.length > 0 && (
            <section className="settings-group">
              <h2>{t('archives')}</h2>
              <p className="muted">{t('archiveHint')}</p>
              {archives.map((archive) => (
                <details key={archive.id}>
                  <summary>{new Date(archive.created_at).toLocaleString(app.language)}</summary>
                  {archive.entities
                    .filter((row) => row.kind === 'recipe' && !row.deleted)
                    .map((row) => (
                      <div className="recovery-item" key={row.id}>
                        <strong>{(row.payload as Recipe).title}</strong>
                        <button
                          className="secondary"
                          onClick={() =>
                            void app
                              .save([
                                {
                                  kind: 'recipe',
                                  id: uuid(),
                                  value: cloneRecipe(row.payload as Recipe),
                                },
                              ])
                              .catch(() => setError(true))
                          }
                        >
                          {t('restoreCopy')}
                        </button>
                      </div>
                    ))}
                </details>
              ))}
            </section>
          )}
          {app.pending.some((row) => row.blocked) && (
            <section className="settings-group">
              <h2>{t('blocked')}</h2>
              <p>{t('recoveryHint')}</p>
              {app.pending.some((row) => row.blocked === 'photo_upload_rejected') && (
                <div className="recovery-item">
                  <p>{t('photoUploadError')}</p>
                  <button
                    className="secondary"
                    disabled={app.syncing}
                    onClick={() =>
                      void app.store
                        .retryPhotos()
                        .then(app.changed)
                        .catch(() => setError(true))
                    }
                  >
                    {t('retryPhotos')}
                  </button>
                </div>
              )}{' '}
              {app.pending
                .filter((row) => row.blocked && row.approval)
                .filter(
                  (row, i, all) =>
                    all.findIndex(
                      (other) => other.approval?.request_id === row.approval?.request_id,
                    ) === i,
                )
                .map((row) => (
                  <div className="recovery-item" key={row.approval!.request_id}>
                    <p>{t('rejectedPlan')}</p>
                    <button
                      className="secondary"
                      onClick={() =>
                        void app.store
                          .archiveSuggestion(row.approval!.request_id)
                          .then(app.changed)
                          .catch(() => setError(true))
                      }
                    >
                      {t('archivePlan')}
                    </button>
                  </div>
                ))}
              {app.pending
                .filter((row) => row.blocked && row.mutation.kind === 'recipe')
                .filter(
                  (row, i, all) =>
                    all.findIndex(
                      (other) => other.mutation.entity_id === row.mutation.entity_id,
                    ) === i,
                )
                .map((row) => (
                  <div className="recovery-item" key={row.mutation.entity_id}>
                    <strong>
                      {
                        app
                          .entities('recipe')
                          .find((recipe) => recipe.id === row.mutation.entity_id)?.payload.title
                      }
                    </strong>
                    <button
                      className="secondary"
                      onClick={() => {
                        void app.store
                          .resolveRejected(row.mutation.entity_id, true)
                          .then(app.changed)
                          .catch(() => setError(true));
                      }}
                    >
                      {t('keepCopy')}
                    </button>
                    <button
                      className="text-button"
                      onClick={() => {
                        void app.store
                          .resolveRejected(row.mutation.entity_id, false)
                          .then(app.changed)
                          .catch(() => setError(true));
                      }}
                    >
                      {t('useServer')}
                    </button>
                  </div>
                ))}
            </section>
          )}
        </div>
      </div>
      {error && (
        <p role="alert" className="error-note">
          {t('saveError')}
        </p>
      )}
      {recovery && (
        <Sheet
          title={t('recoverConfirm')}
          onClose={() => {
            if (!recovering) setRecovery(false);
          }}
        >
          <p>{t('recoverHint')}</p>
          <div className="form-actions">
            <button className="secondary" onClick={() => void exportLocal()}>
              {t('export')}
            </button>
            <button
              className="primary"
              disabled={recovering || !app.online}
              onClick={() => void recover()}
            >
              {recovering ? t('loading') : t('recover')}
            </button>
          </div>
        </Sheet>
      )}
      {confirm && (
        <Sheet title={t('confirmLogout')} onClose={() => setConfirm(false)}>
          <p>{t('logoutHint')}</p>
          {!app.online && <p className="error-note">{t('logoutOffline')}</p>}
          <div className="form-actions">
            <button className="secondary" onClick={() => setConfirm(false)}>
              {t('cancel')}
            </button>
            <button
              className="primary"
              disabled={!app.online}
              onClick={() => void logout().catch(() => setError(true))}
            >
              {t('logout')}
            </button>
          </div>
        </Sheet>
      )}
    </>
  );
}
