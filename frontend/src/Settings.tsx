import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import {
  ArrowUpRight,
  ChevronRight,
  Download,
  LogOut,
  RefreshCw,
  ShieldCheck,
  Smartphone,
} from 'lucide-react';
import { useApp } from './model';
import type { Tab } from './model';
import { PageHeader, Sheet } from './components';
import { ReminderSettings } from './ReminderSettings';
import { ThemeLibrary } from './ThemeLibrary';
import { PlanningSettings } from './PlanningSettings';
import { AISettings } from './AISettings';
import { ChatGPTSettings } from './ChatGPTSettings';
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
function SettingsDisclosure({
  title,
  description,
  children,
  attention = false,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  attention?: boolean;
}) {
  return (
    <details className="settings-disclosure" open={attention || undefined}>
      <summary>
        <span>
          <strong>{title}</strong>
          {description && <small>{description}</small>}
        </span>
        <ChevronRight size={20} aria-hidden="true" />
      </summary>
      <div className="settings-disclosure-body">{children}</div>
    </details>
  );
}
export function Settings({
  back,
  logout,
  reauthenticate,
  shopping,
}: {
  back?: () => void;
  logout: () => Promise<void>;
  reauthenticate: () => void;
  shopping: () => void;
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
  const [syncReport, setSyncReport] = useState('');
  const [checkingSync, setCheckingSync] = useState(false);
  const [copiedSync, setCopiedSync] = useState(false);
  const diagnoseSync = async () => {
    if (!app.api) return;
    setCheckingSync(true);
    setCopiedSync(false);
    try {
      const { syncDiagnostics } = await import('./lib/sync-diagnostics');
      const report = await syncDiagnostics(app.store, app.api, {
        syncing: app.syncing,
        error: app.error,
        phase: app.syncPhase(),
        checked: app.syncChecked,
      });
      setSyncReport(JSON.stringify(report, null, 2));
    } catch {
      setError(true);
    } finally {
      setCheckingSync(false);
    }
  };
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
      <PageHeader title={t('settings')} subtitle={t('settingsIntro')} back={back} />
      <div className="settings-hub">
        <div>
          <SettingsDisclosure
            title={t('account')}
            description={app.household.name + ' · ' + app.household.timezone}
          >
            <div className="settings-surface">
              <div className="settings-row">
                <div>
                  <strong>{app.currentUser?.username ?? app.household.name}</strong>
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
              {!app.demo && app.isAdmin && (
                <a className="settings-row" href="/admin/" target="_blank" rel="noreferrer">
                  {t('openAdmin')}
                  <ArrowUpRight size={18} />
                </a>
              )}
            </div>
          </SettingsDisclosure>
          <SettingsDisclosure
            title={t('device')}
            description={t('deviceSummary')}
            attention={!!app.error}
          >
            <div className="settings-surface">
              <button
                className="settings-row"
                onClick={() => void app.sync()}
                disabled={app.demo || app.syncing}
              >
                <span>
                  {t('sync')} · {app.outgoingCount} {t('pending')}
                </span>
                <RefreshCw size={17} />
              </button>
              {!app.demo && (
                <>
                  <button
                    className="settings-row"
                    onClick={() => void diagnoseSync()}
                    disabled={checkingSync}
                  >
                    {t(checkingSync ? 'loading' : 'syncDiagnostics')}
                    <ShieldCheck size={18} />
                  </button>
                  {syncReport && (
                    <div className="settings-copy">
                      <p>{t('syncDiagnosticsHint')}</p>
                      <label htmlFor="sync-report">{t('syncReport')}</label>
                      <textarea
                        id="sync-report"
                        className="sync-report"
                        rows={10}
                        readOnly
                        value={syncReport}
                      />
                      <div className="form-actions">
                        <button
                          className="text-button"
                          onClick={() => {
                            void navigator.clipboard
                              .writeText(syncReport)
                              .then(() => setCopiedSync(true))
                              .catch(() => setError(true));
                          }}
                        >
                          {t(copiedSync ? 'syncReportCopied' : 'syncReportCopy')}
                        </button>
                        <button
                          className="text-button"
                          onClick={() =>
                            download(JSON.parse(syncReport), 'mealf-sync-diagnostics.json')
                          }
                        >
                          {t('export')}
                          <Download size={18} />
                        </button>
                      </div>
                    </div>
                  )}
                  <button className="settings-row" onClick={reauthenticate}>
                    {t('signInAgain')}
                    <ArrowUpRight size={18} />
                  </button>
                </>
              )}
              <button
                className="settings-row danger"
                onClick={() => (app.demo ? void logout() : setConfirm(true))}
              >
                {t(app.demo ? 'exitDemo' : 'logout')}
                <LogOut size={18} />
              </button>
            </div>
          </SettingsDisclosure>
          <SettingsDisclosure title={t('themes')} description={t('appearanceSummary')}>
            <ThemeLibrary />
          </SettingsDisclosure>
          <SettingsDisclosure title={t('planningPreferences')} description={t('planningSummary')}>
            <PlanningSettings />
          </SettingsDisclosure>
          <SettingsDisclosure title={t('pushReminders')} description={t('reminderSummary')}>
            <ReminderSettings />
          </SettingsDisclosure>
          {(app.demo || app.isAdmin) && (
            <SettingsDisclosure title={t('aiSettingsTitle')} description={t('aiSummary')}>
              <AISettings />
            </SettingsDisclosure>
          )}
          <SettingsDisclosure title={t('chatgptTitle')} description={t('chatgptSummary')}>
            <ChatGPTSettings />
          </SettingsDisclosure>
          <SettingsDisclosure title={t('bring')} description={t('bringBody')}>
            <div className="settings-surface">
              <button className="settings-row" onClick={shopping}>
                {t('shoppingTitle')}
                <RefreshCw size={18} />
              </button>
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
                  {app.isAdmin && (
                    <a
                      className="settings-row"
                      href="/admin/#bring"
                      target="_blank"
                      rel="noreferrer"
                    >
                      {t('openAdmin')}
                      <ArrowUpRight size={18} />
                    </a>
                  )}
                </>
              )}
              {app.demo && <p className="settings-description">{t('demoUnavailable')}</p>}
            </div>
          </SettingsDisclosure>
        </div>
        <div>
          <SettingsDisclosure title={t('installation')} description={t('installationSummary')}>
            <div className="settings-surface settings-copy">
              <Smartphone size={28} strokeWidth={1.4} />
              <p>{t('installHint')}</p>
              <p className="muted">{t('reminderLimits')}</p>
            </div>
          </SettingsDisclosure>
          <SettingsDisclosure title={t('storage')} description={t('storageSummary')}>
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
          </SettingsDisclosure>
          {!app.demo && (
            <SettingsDisclosure title={t('recover')} description={t('recoverySummary')}>
              <p className="muted">{t('recoverHint')}</p>
              <button
                className="text-button"
                disabled={!app.online}
                onClick={() => setRecovery(true)}
              >
                {t('recover')}
              </button>
            </SettingsDisclosure>
          )}
          {archives.length > 0 && (
            <SettingsDisclosure title={t('archives')} description={t('archiveHint')}>
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
            </SettingsDisclosure>
          )}
          {app.pending.some((row) => row.blocked) && (
            <SettingsDisclosure title={t('blocked')} description={t('recoveryHint')} attention>
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
            </SettingsDisclosure>
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
