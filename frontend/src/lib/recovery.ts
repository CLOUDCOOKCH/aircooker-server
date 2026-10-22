import type { components } from '../api-schema';
import { APIError } from './api.ts';
import type { APIClient } from './api.ts';
import type { Change } from './domain.ts';
import { validateChange } from './domain.ts';
import { LocalStore } from './store.ts';
async function rebuild(store: LocalStore, api: Pick<APIClient, 'request'>): Promise<void> {
  if (await store.setting('demo', false)) throw new APIError('demo_server_unavailable', 0);
  const state = await api.request<components['schemas']['SyncState']>(
    '/api/v1/sync/state?cursor=0',
  );
  if (state.instance_id !== store.instanceID) throw new APIError('server_identity_changed', 409);
  const changes: Change[] = [];
  let after = '';
  for (let page = 0; page < 1000; page++) {
    const result = await api.request<components['schemas']['SyncSnapshot']>(
      `/api/v1/sync/snapshot?cursor=${state.cursor}&token=${state.token}&after=${encodeURIComponent(after)}&limit=100`,
    );
    if (
      result.instance_id !== store.instanceID ||
      result.checkpoint.cursor !== state.cursor ||
      result.checkpoint.token !== state.token ||
      !Array.isArray(result.changes) ||
      result.changes.length > 100
    )
      throw new APIError('invalid_server_response', 0);
    result.changes.forEach(validateChange);
    changes.push(...result.changes);
    if (JSON.stringify(result.changes).length > 3 * 1024 * 1024 || changes.length > 100_000)
      throw new APIError('response_too_large', 0);
    if (result.next_after === null) {
      const proof = await api.request<components['schemas']['SyncState']>(
        '/api/v1/sync/state?cursor=' + state.cursor,
      );
      if (proof.instance_id !== store.instanceID || proof.requested_token !== state.token)
        throw new APIError('sync_history_changed', 409);
      await store.replaceSnapshot(changes, { cursor: state.cursor, token: state.token });
      return;
    }
    if (!result.next_after || result.next_after <= after || result.changes.length === 0)
      throw new APIError('invalid_server_response', 0);
    after = result.next_after;
  }
  throw new APIError('response_too_large', 0);
}

export async function rebuildFromServer(
  store: LocalStore,
  api: Pick<APIClient, 'request'>,
): Promise<void> {
  if (typeof navigator !== 'undefined' && navigator.locks)
    return navigator.locks.request(store.syncLock, () => rebuild(store, api));
  return rebuild(store, api);
}
