import type { Key } from '../i18n.ts';

export function syncStatus(state: {
  online: boolean;
  syncing: boolean;
  error: string | null;
  pending: number;
  checked: boolean;
}): Key {
  if (!state.online) return 'offline';
  if (state.syncing) return 'syncing';
  if (state.error) return state.error === 'blocked' ? 'blocked' : 'syncFailed';
  if (state.pending) return 'pending';
  return state.checked ? 'synced' : 'syncNotChecked';
}

const PUBLIC_CODES = new Set([
  'authentication_required',
  'invalid_session',
  'invalid_refresh_token',
  'refresh_replay',
  'csrf_failed',
  'origin_forbidden',
  'device_session_changed',
  'server_identity_changed',
  'sync_history_changed',
  'sync_checkpoint_required',
  'sync_incomplete',
  'invalid_server_response',
  'connection_unavailable',
  'rate_limited',
  'blocked',
  'storage_unavailable',
  'storage_error',
  'device_mismatch',
]);
export function syncErrorCode(code: string | null): string | null {
  return code === null ? null : PUBLIC_CODES.has(code) ? code : 'unclassified_error';
}
