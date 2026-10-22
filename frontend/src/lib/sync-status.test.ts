import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { syncStatus } from './sync-status.ts';
import { syncDiagnostics } from './sync-diagnostics.ts';
import { LocalStore } from './store.ts';
import { emptyRecipe, uuid } from './domain.ts';
import { APIError } from './api.ts';

test('no pending edits never disguises a failed or unchecked sync as up to date', () => {
  const state = { online: true, syncing: false, error: null, pending: 0, checked: false };
  assert.equal(syncStatus(state), 'syncNotChecked');
  assert.equal(syncStatus({ ...state, checked: true }), 'synced');
  for (const error of ['connection_unavailable', 'authentication_required', 'sync_incomplete'])
    assert.equal(syncStatus({ ...state, checked: true, error }), 'syncFailed');
  assert.equal(syncStatus({ ...state, error: 'blocked' }), 'blocked');
  assert.equal(syncStatus({ ...state, pending: 1, checked: true }), 'pending');
  assert.equal(syncStatus({ ...state, syncing: true, error: 'old_failure' }), 'syncing');
  assert.equal(syncStatus({ ...state, online: false, checked: true }), 'offline');
});

test('diagnostics compare history and device identity without exporting household content or tokens', async () => {
  const store = await LocalStore.open(uuid()),
    device = await store.device(),
    id = uuid();
  const privateText = 'PRIVATE recipe, password and prompt';
  await store.saveBatch([
    { kind: 'recipe', id, value: { ...emptyRecipe(), title: privateText, notes: privateText } },
  ]);
  await store.saveImport({
    id: uuid(),
    state: 'queued',
    body: {
      text: privateText,
      source_url: 'https://private.invalid/recipe',
      use_ai: true,
      consent_external_ai: true,
    },
  });
  await store.setSetting('anchor', { cursor: 3, token: 'a'.repeat(32) });
  const report = await syncDiagnostics(
    store,
    {
      async request<T>(path: string): Promise<T> {
        if (path.includes('/info'))
          return {
            instance_id: store.instanceID,
            version: '0.1.0',
            api_major: 1,
            sync_protocol: 1,
          } as T;
        if (path.includes('/state'))
          return {
            instance_id: store.instanceID,
            cursor: 5,
            requested_cursor: 3,
            requested_token: 'a'.repeat(32),
          } as T;
        if (path.includes('/session'))
          return { authenticated: true, device_id: device, session_id: privateText } as T;
        throw new APIError('private-provider-key-detail', 503);
      },
    },
    { syncing: false, error: 'sync_incomplete', phase: 'receiving_changes', checked: false },
  );
  assert.equal(report.local.records.recipe, 1);
  assert.equal(report.local.pending_mutations, 1);
  assert.equal(report.local.imports.queued, 1);
  assert.deepEqual(report.history, {
    cursor: 5,
    identity_matches: true,
    local_proof_matches: true,
  });
  assert.deepEqual(report.session, { authenticated: true, device_matches: true });
  assert.deepEqual(report.storage, { ok: false, status: 503, error: 'unclassified_error' });
  const json = JSON.stringify(report);
  for (const secret of [
    privateText,
    store.instanceID,
    device,
    id,
    'a'.repeat(32),
    'private.invalid',
    'private-provider-key-detail',
  ])
    assert.ok(!json.includes(secret), secret);
  assert.equal((await store.pending()).length, 1);
  assert.equal((await store.imports()).length, 1);
  store.close();
});
