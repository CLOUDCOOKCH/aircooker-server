import type { components } from '../api-schema';
import { APIError } from './api.ts';
import type { APIClient } from './api.ts';
import type { LocalStore } from './store.ts';
import { syncErrorCode } from './sync-status.ts';

/** Deliberately excludes payloads, names, URLs, IDs, history tokens and credentials. */
export async function syncDiagnostics(
  store: LocalStore,
  api: Pick<APIClient, 'request'>,
  attempt: { syncing: boolean; error: string | null; phase: string; checked: boolean },
) {
  const local = await store.syncSummary();
  const probe = async <T>(path: string) => {
    try {
      const value = await api.request<T>(path);
      if (typeof value !== 'object' || value === null || Array.isArray(value))
        throw new APIError('invalid_server_response', 0);
      return { ok: true as const, value };
    } catch (error) {
      return {
        ok: false as const,
        status: error instanceof APIError ? error.status : 0,
        error: syncErrorCode(error instanceof APIError ? error.code : 'connection_unavailable'),
      };
    }
  };
  const [info, state, session, status] = await Promise.all([
    probe<{ instance_id: string; version: string; api_major: number; sync_protocol: number }>(
      '/api/v1/system/info',
    ),
    probe<components['schemas']['SyncState']>('/api/v1/sync/state?cursor=' + local.cursor),
    probe<components['schemas']['BrowserSession']>('/api/v1/pwa/auth/session'),
    probe<components['schemas']['AdministrationStatus']>('/api/v1/admin/status'),
  ]);
  const script =
    typeof document === 'undefined'
      ? null
      : document.querySelector<HTMLScriptElement>('script[type="module"][src]');
  const bundle = script?.src.match(/\/(index-[A-Za-z0-9_-]+\.js)(?:\?|$)/)?.[1] ?? null;
  return {
    format: 'mealf-sync-diagnostics',
    version: 1,
    client_bundle: bundle,
    captured_at: new Date().toISOString(),
    attempt: { ...attempt, error: syncErrorCode(attempt.error) },
    local: {
      cursor: local.cursor,
      records: local.records,
      pending_mutations: local.pending,
      blocked_mutations: local.blocked,
      imports: local.imports,
      last_success: local.lastSuccess,
    },
    server: info.ok
      ? {
          version: info.value.version,
          api_major: info.value.api_major,
          sync_protocol: info.value.sync_protocol,
          identity_matches: info.value.instance_id === store.instanceID,
        }
      : info,
    history: state.ok
      ? {
          cursor: state.value.cursor,
          identity_matches: state.value.instance_id === store.instanceID,
          local_proof_matches:
            state.value.requested_cursor === local.cursor &&
            state.value.requested_token === local.token,
        }
      : state,
    session: session.ok
      ? {
          authenticated: session.value.authenticated === true,
          device_matches: session.value.device_id === local.device,
        }
      : session,
    storage: status.ok
      ? {
          server_recipes: status.value.recipes,
          pending_jobs: status.value.pending_jobs,
        }
      : status,
  };
}
