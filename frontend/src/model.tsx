import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { APIClient, APIError } from './lib/api';
import { LocalStore } from './lib/store';
import { legacy } from './lib/legacy';
import { SyncEngine } from './lib/sync';
import { reminderTarget } from './lib/notifications';
import { DEFAULT_PLANNING, PLANNING_PATH, parsePlanningContext } from './lib/preferences';
import type { PlanningContext } from './lib/preferences';
import { openDemo, DEMO_ID } from './lib/demo';
import { translate } from './i18n';
import type { Key, Language } from './i18n';
import type { Entity, Kind } from './lib/domain';
import type { Edit, ImportTask, Queued } from './lib/store';
export type Tab = 'home' | 'calendar' | 'recipes' | 'pantry' | 'settings';
export type Household = { name: string; timezone: string; language: Language };
export type SystemInfo = {
  name: string;
  instance_id: string | null;
  configured: boolean;
  api_major: number;
  sync_protocol: number;
  version: string;
};
export type Runtime = {
  store: LocalStore;
  api: APIClient | null;
  demo: boolean;
  household: Household;
};
const LAST = 'mealf:last-kitchen';
export const api = new APIClient();
const Context = createContext<ReturnType<typeof useRuntime> | null>(null);
function useRuntime(runtime: Runtime) {
  const [rows, setRows] = useState<Entity[]>([]),
    [pending, setPending] = useState<Queued[]>([]),
    [imports, setImports] = useState<ImportTask[]>([]);
  const [household, setHousehold] = useState(runtime.household);
  const [planning, setPlanning] = useState<PlanningContext>(DEFAULT_PLANNING);
  const [language, setLanguageState] = useState<Language>(runtime.household.language);
  const [tab, setTabState] = useState<Tab>('home');
  const [syncing, setSyncing] = useState(false),
    [error, setError] = useState<string | null>(null),
    [notice, setNotice] = useState<Key | null>(null);
  const [online, setOnline] = useState(navigator.onLine),
    [ready, setReady] = useState(false);
  const store = runtime.store;
  const engine = useMemo(
    () => (runtime.api ? new SyncEngine(store, runtime.api) : null),
    [store, runtime.api],
  );
  const refresh = async () => {
    const [all, queue, tasks] = await Promise.all([store.all(), store.pending(), store.imports()]);
    setRows(all.filter((row) => !row.deleted));
    setPending(queue);
    setImports(tasks);
  };
  const refreshPlanning = async () => {
    const current =
      runtime.api && navigator.onLine
        ? parsePlanningContext(await runtime.api.request(PLANNING_PATH))
        : parsePlanningContext(await store.setting('planning:context', DEFAULT_PLANNING));
    await store.setSetting('planning:context', current);
    setPlanning(current);
    return current;
  };
  const sync = async () => {
    if (!runtime.api || !navigator.onLine) return;
    setSyncing(true);
    try {
      const result = await engine!.synchronise();
      setError(result.blocked ? 'blocked' : null);
      const updated = await runtime.api.request<Household>('/api/v1/household');
      if (!updated.name || !['en', 'de'].includes(updated.language))
        throw new Error('invalid_household');
      new Intl.DateTimeFormat('en', { timeZone: updated.timezone });
      await store.setSetting('household', updated);
      setHousehold(updated);
      await refreshPlanning();
    } catch (e) {
      setError(e instanceof APIError ? e.code : 'connection_unavailable');
    } finally {
      setSyncing(false);
      await refresh();
    }
  };
  useEffect(() => {
    let alive = true;
    void (async () => {
      await refresh();
      try {
        setPlanning(
          parsePlanningContext(await store.setting('planning:context', DEFAULT_PLANNING)),
        );
      } catch {
        setError('storage_error');
      }
      const [savedTab, savedLanguage] = await Promise.all([
        store.setting<Tab>('start', 'home'),
        store.setting<Language>('language', runtime.household.language),
      ]);
      if (alive) {
        setTabState(reminderTarget(location.search)?.tab ?? savedTab);
        setLanguageState(savedLanguage);
        setReady(true);
        await sync();
      }
    })().catch(() => setError('storage_error'));
    const onlineEvent = () => {
      setOnline(navigator.onLine);
      if (navigator.onLine) void sync();
    };
    const foreground = () => {
      if (document.visibilityState === 'visible') {
        void refresh();
        void sync();
      }
    };
    const channel =
      typeof BroadcastChannel === 'undefined' ? null : new BroadcastChannel(store.namespace);
    if (channel)
      channel.onmessage = () => {
        void refresh();
      };
    window.addEventListener('online', onlineEvent);
    window.addEventListener('offline', onlineEvent);
    document.addEventListener('visibilitychange', foreground);
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void sync();
    }, 30_000);
    return () => {
      alive = false;
      channel?.close();
      clearInterval(timer);
      window.removeEventListener('online', onlineEvent);
      window.removeEventListener('offline', onlineEvent);
      document.removeEventListener('visibilitychange', foreground);
    };
  }, [store]);
  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);
  const changed = async () => {
    await refresh();
    if (typeof BroadcastChannel !== 'undefined') {
      const channel = new BroadcastChannel(store.namespace);
      channel.postMessage('changed');
      channel.close();
    }
    void sync();
  };
  const save = async (edits: Edit[], options?: Parameters<LocalStore['saveBatch']>[1]) => {
    await store.saveBatch(edits, options);
    setNotice('saved');
    await changed();
  };
  const setLanguage = async (value: Language) => {
    await store.setSetting('language', value);
    setLanguageState(value);
  };
  const entities = <K extends Kind>(kind: K) =>
    rows.filter((row) => row.kind === kind) as Entity<K>[];
  return {
    ...runtime,
    household,
    planning,
    refreshPlanning,
    rows,
    pending,
    imports,
    language,
    setLanguage,
    tab,
    setTab: setTabState,
    online,
    ready,
    syncing,
    error,
    setError,
    notice,
    setNotice,
    refresh,
    changed,
    sync,
    save,
    entities,
    t: (key: Key) => translate(language, key),
  };
}
export function Provider({ runtime, children }: { runtime: Runtime; children: ReactNode }) {
  const value = useRuntime(runtime);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useApp() {
  const value = useContext(Context);
  if (!value) throw new Error('missing_runtime');
  return value;
}
export async function restoreRuntime(): Promise<Runtime | null> {
  const last = localStorage.getItem(LAST) ?? localStorage.getItem(legacy.kitchen);
  if (last && !localStorage.getItem(LAST)) {
    try {
      localStorage.setItem(LAST, last);
    } catch {
      /* Preserve readable legacy state when storage is full. */
    }
  }
  if (!last) return null;
  const connection = JSON.parse(last) as { instance: string; demo: boolean };
  if (connection.demo) {
    const store = await openDemo();
    return {
      store,
      api: null,
      demo: true,
      household: await store.setting('household', {
        name: 'Demo kitchen',
        timezone: 'UTC',
        language: 'en' as Language,
      }),
    };
  }
  const store = await LocalStore.open(connection.instance);
  const household = await store.setting<Household>('household', {
    name: 'mealf',
    timezone: 'UTC',
    language: 'en',
  });
  if (!(await store.setting('unlocked', false))) {
    store.close();
    return null;
  }
  // Offline viewing is available after a previous successful sign-in. Never sends stored credentials.
  if (navigator.onLine) {
    try {
      const info = await api.request<SystemInfo>('/api/v1/system/info', {}, false);
      if (info.instance_id !== connection.instance)
        throw new APIError('server_identity_changed', 409);
      const session = await api.request<{ device_id: string }>('/api/v1/pwa/auth/session');
      if (session.device_id !== (await store.device()))
        throw new APIError('device_session_changed', 401);
    } catch (e) {
      if (e instanceof APIError && (e.status === 401 || e.code === 'server_identity_changed')) {
        store.close();
        return null;
      }
    }
  }
  return { store, api, demo: false, household };
}
export async function enterDemo(): Promise<Runtime> {
  const store = await openDemo();
  localStorage.setItem(LAST, JSON.stringify({ instance: DEMO_ID, demo: true }));
  return {
    store,
    api: null,
    demo: true,
    household: await store.setting('household', {
      name: 'Demo kitchen',
      timezone: 'UTC',
      language: 'en' as Language,
    }),
  };
}
export async function connectRuntime(
  info: SystemInfo,
  credentials: {
    username: string;
    password: string;
    device_id: string;
    name?: string;
    timezone?: string;
    language?: Language;
  },
  token?: string,
): Promise<Runtime> {
  const session = await api.request<{ device_id: string }>(
    `/api/v1/pwa/auth/${info.configured ? 'login' : 'setup'}`,
    {
      method: 'POST',
      body: JSON.stringify(credentials),
      headers: token ? { 'X-Setup-Token': token } : undefined,
    },
    false,
  );
  const connected = info.configured
    ? info
    : await api.request<SystemInfo>('/api/v1/system/info', {}, false);
  if (!connected.instance_id) throw new Error('invalid_server_response');
  const store = await LocalStore.open(connected.instance_id);
  await store.bindDevice(session.device_id);
  const household = await api.request<Household>('/api/v1/household');
  await store.setSetting('household', household);
  await store.setSetting('unlocked', true);
  localStorage.setItem(LAST, JSON.stringify({ instance: connected.instance_id, demo: false }));
  return { store, api, demo: false, household };
}
export async function leaveRuntime(runtime: Runtime): Promise<void> {
  if (runtime.api) await runtime.api.request('/api/v1/pwa/auth/logout', { method: 'POST' }, false);
  await runtime.store.setSetting('unlocked', false);
  localStorage.removeItem(LAST);
  localStorage.removeItem(legacy.kitchen);
  runtime.store.close();
}
