import { useEffect, useState } from 'react';
import {
  ArrowRight,
  CalendarDays,
  Check,
  ChefHat,
  CircleAlert,
  CloudOff,
  Home as HomeIcon,
  Leaf,
  Settings2,
  X,
} from 'lucide-react';
import {
  api,
  connectRuntime,
  enterDemo,
  leaveRuntime,
  Provider,
  restoreRuntime,
  useApp,
} from './model';
import type { Runtime, SystemInfo, Tab } from './model';
import { Brand, Peach } from './Brand';
import { translate } from './i18n';
import type { Language } from './i18n';
import { LocalStore } from './lib/store';
import type { ImportTask } from './lib/store';
import { APIError } from './lib/api';
import { emptyRecipe, today, uuid } from './lib/domain';
import { Calendar, Home, ManageMeal, PlanMeal, Suggestions } from './Calendar';
import type { PlanningTarget } from './Calendar';
import type { Recipe } from './lib/domain';
import type { Occurrence } from './lib/planning';
import { RecipeDetail, RecipeEditor, Recipes } from './Recipes';
import { Pantry } from './Pantry';
import { Settings } from './Settings';
import { Imports } from './Imports';
import { activateUpdate, installWorker } from './worker-client';
import { reminderTarget } from './lib/notifications';
import type { ReminderTarget } from './lib/notifications';

type View =
  | { kind: 'main' }
  | { kind: 'recipe'; id: string }
  | { kind: 'editor'; id?: string; task?: ImportTask; initial?: Recipe; draftID?: string }
  | { kind: 'imports' };
export default function App() {
  const [runtime, setRuntime] = useState<Runtime | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(false);
  useEffect(() => {
    void restoreRuntime()
      .then(setRuntime)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
    void installWorker();
  }, []);
  if (loading)
    return (
      <div className="boot-screen">
        <img className="boot-icon" src="/app/brand/peach-v1.png" alt="" width="384" height="384" />
        <div className="loading-line" />
        <Brand icon={false} />
      </div>
    );
  return runtime ? (
    <Provider key={runtime.store.instanceID} runtime={runtime}>
      <Kitchen
        onLeave={async () => {
          await leaveRuntime(runtime);
          setRuntime(null);
        }}
        reauthenticate={() => setRuntime(null)}
      />
    </Provider>
  ) : (
    <Welcome onEnter={setRuntime} storageError={error} />
  );
}
function Welcome({
  onEnter,
  storageError,
}: {
  onEnter: (runtime: Runtime) => void;
  storageError: boolean;
}) {
  const [language, setLanguage] = useState<Language>(
      navigator.language.startsWith('de') ? 'de' : 'en',
    ),
    [info, setInfo] = useState<SystemInfo | null>(null),
    [form, setForm] = useState(false),
    [error, setError] = useState<string | null>(null),
    [busy, setBusy] = useState(false);
  const t = (key: Parameters<typeof translate>[1]) => translate(language, key);
  const check = async () => {
    setBusy(true);
    setError(null);
    try {
      if (!isSecureContext) throw new APIError('secure_required', 0);
      const response = await api.request<SystemInfo>('/api/v1/system/info', {}, false);
      if (response.api_major !== 1 || response.sync_protocol !== 1)
        throw new APIError('unsupported', 0);
      setInfo(response);
      setForm(true);
    } catch (e) {
      setError(
        e instanceof APIError && e.code === 'secure_required'
          ? t('secureRequired')
          : e instanceof APIError && e.code === 'unsupported'
            ? t('unsupported')
            : t('unavailable'),
      );
    } finally {
      setBusy(false);
    }
  };
  const demo = async () => {
    setBusy(true);
    try {
      onEnter(await enterDemo());
    } catch {
      setError(t('storageError'));
    } finally {
      setBusy(false);
    }
  };
  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!info) return;
    setBusy(true);
    setError(null);
    const data = new FormData(e.currentTarget);
    try {
      let device: string = uuid();
      if (info.instance_id) {
        const store = await LocalStore.open(info.instance_id);
        device = await store.device();
        store.close();
      }
      const credentials = {
        username: String(data.get('username')),
        password: String(data.get('password')),
        device_id: device,
        ...(!info.configured
          ? { name: String(data.get('name')), timezone: String(data.get('timezone')), language }
          : {}),
      };
      onEnter(
        await connectRuntime(
          info,
          credentials,
          info.configured ? undefined : String(data.get('token')),
        ),
      );
    } catch (e) {
      setError(e instanceof APIError && e.status === 401 ? t('invalidLogin') : t('invalid'));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="welcome-shell">
      <header className="welcome-header">
        <Brand href="/app/" language={language} />
        <select
          aria-label={t('language')}
          value={language}
          onChange={(e) => setLanguage(e.target.value as Language)}
        >
          <option value="en">English</option>
          <option value="de">Deutsch</option>
        </select>
      </header>
      <main className="welcome-content">
        <Peach language={language} hero />
        <h1>{form ? (info?.configured ? t('loginHeadline') : t('setup')) : t('welcome')}</h1>
        <p className="welcome-description">
          {form ? (info?.configured ? t('loginJoke') : t('selfHosted')) : t('welcomeBody')}
        </p>
        {form && info?.configured && (
          <p className="welcome-household">
            {info.name} · {t('selfHosted')}
          </p>
        )}
        {!form ? (
          <>
            <button
              className="primary welcome-primary"
              disabled={busy}
              onClick={() => void check()}
            >
              {t('connect')}
              <ArrowRight size={18} />
            </button>
            <button className="text-button" disabled={busy} onClick={() => void demo()}>
              {t('tryDemo')}
            </button>
            <p className="welcome-footnote">{t('connectHint')}</p>
          </>
        ) : (
          <form className="welcome-form" onSubmit={(e) => void submit(e)}>
            <label>
              {t('username')}
              <input
                autoComplete="username"
                aria-label={t('username')}
                name="username"
                required
                maxLength={100}
              />
            </label>
            <label>
              {t('password')}
              <input
                type="password"
                autoComplete={info?.configured ? 'current-password' : 'new-password'}
                aria-label={t('password')}
                name="password"
                required
                minLength={info?.configured ? 1 : 12}
                maxLength={1024}
              />
              {!info?.configured && <small>{t('setupPassword')}</small>}
            </label>
            {!info?.configured && (
              <>
                <label>
                  {t('setupToken')}
                  <input
                    aria-label={t('setupToken')}
                    name="token"
                    required
                    autoComplete="off"
                    type="password"
                  />
                  <small>{t('setupHint')}</small>
                </label>
                <label>
                  {t('householdName')}
                  <input required name="name" maxLength={100} />
                </label>
                <label>
                  {t('timezone')}
                  <input
                    required
                    name="timezone"
                    defaultValue={Intl.DateTimeFormat().resolvedOptions().timeZone}
                  />
                </label>
              </>
            )}
            <button className="primary full" disabled={busy}>
              {busy ? t('loading') : t(info?.configured ? 'login' : 'setup')}
            </button>
            <button type="button" className="text-button" onClick={() => setForm(false)}>
              {t('back')}
            </button>
          </form>
        )}
        {(error || storageError) && (
          <p role="alert" className="error-note">
            {error ?? t('storageError')}
          </p>
        )}
      </main>
      <footer className="welcome-footer">{t('selfHosted')}</footer>
    </div>
  );
}
function Kitchen({
  onLeave,
  reauthenticate,
}: {
  onLeave: () => Promise<void>;
  reauthenticate: () => void;
}) {
  const app = useApp(),
    { t } = app;
  const [day, setDay] = useState(
      reminderTarget(location.search)?.day ?? today(app.household.timezone),
    ),
    [view, setView] = useState<View>({ kind: 'main' }),
    [target, setTarget] = useState<PlanningTarget | null>(null),
    [managed, setManaged] = useState<Occurrence | null>(null),
    [suggestions, setSuggestions] = useState(false);
  const [update, setUpdate] = useState<ServiceWorker | null>(null);
  const [reminder, setReminder] = useState<ReminderTarget | null>(null);
  useEffect(() => {
    if (app.ready && reminderTarget(location.search))
      history.replaceState(history.state, '', '/app/');
  }, [app.ready]);
  useEffect(() => {
    const receive = (event: MessageEvent) => {
      if (event.data?.type !== 'MEAL_REMINDER') return;
      try {
        const url = new URL(event.data.url, location.origin);
        if (url.origin !== location.origin || url.pathname !== '/app/') return;
        const target = reminderTarget(url.search);
        if (target) {
          if (view.kind === 'editor') setReminder(target);
          else {
            app.setTab(target.tab);
            if (target.day) setDay(target.day);
            setView({ kind: 'main' });
          }
        }
      } catch {
        /* An invalid message never changes the current editor or calendar. */
      }
    };
    navigator.serviceWorker?.addEventListener('message', receive);
    return () => navigator.serviceWorker?.removeEventListener('message', receive);
  }, [view.kind]);
  useEffect(() => {
    const listen = (event: Event) => setUpdate((event as CustomEvent<ServiceWorker>).detail);
    window.addEventListener('aircooker:update', listen);
    return () => window.removeEventListener('aircooker:update', listen);
  }, []);
  useEffect(() => {
    if (!app.notice) return;
    const timer = setTimeout(() => app.setNotice(null), 3000);
    return () => clearTimeout(timer);
  }, [app.notice]);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
    document.getElementById('main')?.focus({ preventScroll: true });
  }, [view, app.tab]);
  const back = () => setView({ kind: 'main' }),
    open = (id: string) => setView({ kind: 'recipe', id }),
    create = () => setView({ kind: 'editor' }),
    importRecipe = () => setView({ kind: 'imports' });
  const tabs: { id: Tab; icon: typeof HomeIcon }[] = [
    { id: 'home', icon: HomeIcon },
    { id: 'calendar', icon: CalendarDays },
    { id: 'recipes', icon: ChefHat },
    { id: 'pantry', icon: Leaf },
    { id: 'settings', icon: Settings2 },
  ];
  let content;
  if (!app.ready)
    content = (
      <div className="skeleton-content" aria-label={t('loading')}>
        <div />
        <div />
        <div />
      </div>
    );
  else if (view.kind === 'recipe')
    content = (
      <RecipeDetail
        id={view.id}
        back={back}
        edit={() => setView({ kind: 'editor', id: view.id })}
        plan={() => setTarget({ day, category: 'dinner', recipeID: view.id })}
      />
    );
  else if (view.kind === 'editor')
    content = (
      <RecipeEditor
        key={view.id ?? view.task?.id ?? 'new'}
        entity={app.entities('recipe').find((row) => row.id === view.id)}
        task={view.task}
        initialRecipe={view.initial}
        draftID={view.draftID}
        back={back}
      />
    );
  else if (view.kind === 'imports')
    content = (
      <Imports
        back={back}
        review={(task) => setView({ kind: 'editor', task })}
        manual={(task) =>
          task
            ? setView({
                kind: 'editor',
                initial: {
                  ...emptyRecipe(),
                  source_url: task.body.source_url ?? null,
                  notes: task.recognizedText ?? task.body.text ?? '',
                  image_id: task.body.image_id ?? null,
                  source_platform: task.body.image_id ? 'image' : 'manual',
                  provenance: { fallback: 'manual_review' },
                },
                draftID: 'manual-import:' + task.id,
              })
            : create()
        }
      />
    );
  else if (app.tab === 'home')
    content = (
      <Home
        day={day}
        setDay={setDay}
        open={open}
        plan={setTarget}
        manage={setManaged}
        create={create}
        importRecipe={importRecipe}
        suggest={() => setSuggestions(true)}
      />
    );
  else if (app.tab === 'calendar')
    content = (
      <Calendar
        day={day}
        setDay={setDay}
        open={open}
        plan={setTarget}
        manage={setManaged}
        suggest={() => setSuggestions(true)}
      />
    );
  else if (app.tab === 'recipes')
    content = <Recipes open={open} create={create} importRecipe={importRecipe} />;
  else if (app.tab === 'pantry') content = <Pantry />;
  else content = <Settings logout={onLeave} reauthenticate={reauthenticate} />;
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        {t('kitchen')}
      </a>
      <nav className="app-nav" aria-label="mealf">
        <div className="nav-brand">
          <Brand language={app.language} />
        </div>
        <div className="nav-links">
          {tabs.map(({ id, icon: Icon }) => (
            <button
              key={id}
              className={app.tab === id ? 'active' : ''}
              aria-current={app.tab === id ? 'page' : undefined}
              aria-label={t(id)}
              onClick={() => {
                app.setTab(id);
                back();
              }}
            >
              <Icon size={22} strokeWidth={app.tab === id ? 2 : 1.6} />
              <span className={id === 'settings' ? 'nav-label-full' : undefined}>{t(id)}</span>
              {id === 'settings' && (
                <span className="nav-label-short" aria-hidden="true">
                  {t('navSettings')}
                </span>
              )}
            </button>
          ))}
        </div>
        <div className="nav-bottom">
          <span>{app.household.name}</span>
          <small>{app.demo ? t('demo') : new URL(location.href).hostname}</small>
        </div>
      </nav>
      <div className="main-shell">
        <div className="connection-bar">
          {app.demo ? (
            <>
              <span className="demo-label">{t('demo')}</span>
              <span className="muted">{t('demoHint')}</span>
              <button className="text-button" onClick={() => void onLeave()}>
                {t('exitDemo')}
                <X size={14} />
              </button>
            </>
          ) : (
            <>
              <span className={'connection-status ' + (!app.online ? 'is-offline' : '')}>
                {!app.online ? (
                  <CloudOff size={15} />
                ) : app.error ? (
                  <CircleAlert size={15} />
                ) : (
                  <Check size={15} />
                )}{' '}
                {t(
                  !app.online
                    ? 'offline'
                    : app.syncing
                      ? 'syncing'
                      : app.pending.length
                        ? 'pending'
                        : 'synced',
                )}
                {app.pending.length > 0 && <span> · {app.pending.length}</span>}
              </span>
              <button
                className="text-button"
                disabled={app.syncing}
                onClick={() => void app.sync()}
              >
                {t('sync')}
              </button>
            </>
          )}
        </div>
        {app.error && (
          <div className="status-banner" role="alert">
            <CircleAlert size={18} />
            <p>{t(app.error === 'blocked' ? 'blocked' : 'syncError')}</p>
            <button
              className="text-button"
              onClick={() => {
                app.setTab('settings');
                back();
              }}
            >
              {t('settings')}
            </button>
          </div>
        )}
        {update && (
          <div className="status-banner">
            <p>{t('update')}</p>
            <button
              className="text-button"
              disabled={view.kind === 'editor'}
              onClick={() => {
                activateUpdate(update);
              }}
            >
              {t('applyUpdate')}
            </button>
          </div>
        )}
        <main id="main" tabIndex={-1} className="page-content" key={app.tab}>
          {reminder && (
            <div className="status-banner" role="status">
              <p>{t('pushReminderReady')}</p>
              <button
                className="text-button"
                disabled={view.kind === 'editor'}
                onClick={() => {
                  app.setTab(reminder.tab);
                  if (reminder.day) setDay(reminder.day);
                  setView({ kind: 'main' });
                  setReminder(null);
                }}
              >
                {t('pushOpenReminder')}
              </button>
            </div>
          )}
          {content}
        </main>
        <footer className="app-footer">
          <Brand compact language={app.language} />
        </footer>
      </div>
      {app.notice && (
        <div className="toast" role="status">
          <Check size={16} />
          {t(app.notice)}
        </div>
      )}
      {target && <PlanMeal target={target} onClose={() => setTarget(null)} />}{' '}
      {managed && <ManageMeal item={managed} onClose={() => setManaged(null)} />}{' '}
      {suggestions && <Suggestions day={day} onClose={() => setSuggestions(false)} />}
    </div>
  );
}
