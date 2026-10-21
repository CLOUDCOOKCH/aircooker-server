import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { components } from '../api-schema';
import { APIError } from './api.ts';
import { emptyRecipe, uuid } from './domain.ts';
import { LocalStore } from './store.ts';
import { SyncEngine } from './sync.ts';

type Wire = components['schemas'];
test('sync pushes once and atomically records the returned delta and history proof', async () => {
  const instance = uuid();
  const store = await LocalStore.open(instance);
  const device = await store.device();
  const recipe = { ...emptyRecipe(), title: 'Offline soup' };
  const id = uuid();
  await store.saveBatch([{ kind: 'recipe', id, value: recipe }]);
  let pushes = 0;
  let mutationID = '';
  const api = {
    async request<T>(path: string, init?: RequestInit): Promise<T> {
      let result: unknown;
      if (path.startsWith('/api/v1/sync/state'))
        result = {
          instance_id: instance,
          cursor: 0,
          token: 'root',
          requested_cursor: 0,
          requested_token: 'root',
        };
      else if (path.endsWith('/session')) result = { device_id: device, authenticated: true };
      else if (path.endsWith('/push')) {
        const body = JSON.parse(String(init?.body)) as Wire['Push'];
        assert.deepEqual(body.checkpoint, { cursor: 0, token: 'root' });
        assert.equal(body.mutations.length, 1);
        mutationID = body.mutations[0].mutation_id;
        assert.equal(body.mutations[0].entity_id, id);
        pushes += 1;
        result = [{ mutation_id: mutationID, revision: 1, status: 'accepted', conflict: false }];
      } else if (path.startsWith('/api/v1/sync/pull')) {
        result = {
          changes: [
            {
              kind: 'recipe',
              entity_id: id,
              payload: recipe,
              deleted: false,
              revision: 1,
              updated_at: '2026-10-21T00:00:00Z',
            },
          ],
          cursor: 1,
          cursor_token: 'a'.repeat(32),
          has_more: false,
        };
      } else throw new Error('Unexpected request: ' + path);
      return result as T;
    },
    async upload() {
      throw new Error('No photo expected');
    },
  };
  const engine = new SyncEngine(store, api);
  const [a, b] = await Promise.all([engine.synchronise(), engine.synchronise()]);
  assert.equal(pushes, 1);
  assert.deepEqual(a, b);
  assert.equal(a.sent, 1);
  assert.deepEqual(await store.pending(), []);
  assert.equal((await store.anchor()).cursor, 1);
  assert.equal((await store.entities('recipe'))[0].payload.title, recipe.title);
  store.close();
});

test('restored history and a changed server identity stop before uploads or mutations', async () => {
  for (const identityChanged of [false, true]) {
    const instance = uuid();
    const store = await LocalStore.open(instance);
    await store.setSetting('anchor', { cursor: 5, token: 'a'.repeat(32) });
    await store.saveBatch([
      { kind: 'recipe', id: uuid(), value: { ...emptyRecipe(), title: 'Keep me' } },
    ]);
    let calls = 0;
    const engine = new SyncEngine(store, {
      async request<T>(): Promise<T> {
        calls += 1;
        return {
          instance_id: identityChanged ? uuid() : instance,
          cursor: 5,
          token: 'b'.repeat(32),
          requested_cursor: 5,
          requested_token: 'b'.repeat(32),
        } as T;
      },
      async upload() {
        throw new Error('Must not upload');
      },
    });
    await assert.rejects(
      engine.synchronise(),
      (error: unknown) =>
        error instanceof APIError &&
        error.code === (identityChanged ? 'server_identity_changed' : 'sync_history_changed'),
    );
    assert.equal(calls, 1);
    assert.equal((await store.pending()).length, 1);
    store.close();
  }
});

test('lost or mismatched push receipts cannot acknowledge an outgoing mutation', async () => {
  const instance = uuid();
  const store = await LocalStore.open(instance);
  const device = await store.device();
  await store.saveBatch([
    { kind: 'recipe', id: uuid(), value: { ...emptyRecipe(), title: 'Pending' } },
  ]);
  const engine = new SyncEngine(store, {
    async request<T>(path: string): Promise<T> {
      if (path.includes('/state'))
        return {
          instance_id: instance,
          cursor: 0,
          requested_cursor: 0,
          requested_token: 'root',
        } as T;
      if (path.endsWith('/session')) return { device_id: device } as T;
      return [{ mutation_id: uuid(), revision: 1, status: 'accepted', conflict: false }] as T;
    },
    async upload() {},
  });
  await assert.rejects(
    engine.synchronise(),
    (error: unknown) => error instanceof APIError && error.code === 'invalid_server_response',
  );
  assert.equal((await store.pending()).length, 1);
  store.close();
});

test('a failed import does not prevent unrelated recipe changes from syncing', async () => {
  const instance = uuid();
  const store = await LocalStore.open(instance);
  const device = await store.device();
  const importID = uuid();
  await store.saveImport({
    id: importID,
    state: 'queued',
    body: {
      source_url: 'https://example.invalid/recipe',
      use_ai: false,
      consent_external_ai: false,
    },
  });
  await store.saveBatch([
    { kind: 'recipe', id: uuid(), value: { ...emptyRecipe(), title: 'Unrelated edit' } },
  ]);
  const engine = new SyncEngine(store, {
    async request<T>(path: string, init?: RequestInit): Promise<T> {
      if (path.includes('/state'))
        return {
          instance_id: instance,
          cursor: 0,
          requested_cursor: 0,
          requested_token: 'root',
        } as T;
      if (path.endsWith('/session')) return { device_id: device } as T;
      if (path === '/api/v1/imports') throw new APIError('validation_failed', 422);
      if (path.endsWith('/push')) {
        const body = JSON.parse(String(init?.body)) as Wire['Push'];
        return [
          {
            mutation_id: body.mutations[0].mutation_id,
            revision: 1,
            status: 'accepted',
            conflict: false,
          },
        ] as T;
      }
      return { changes: [], cursor: 1, cursor_token: 'a'.repeat(32), has_more: false } as T;
    },
    async upload() {},
  });
  const result = await engine.synchronise();
  assert.equal(result.sent, 1);
  assert.deepEqual(await store.pending(), []);
  const task = (await store.imports())[0];
  assert.equal(task.state, 'needs_input');
  assert.equal(task.body.source_url, 'https://example.invalid/recipe');
  store.close();
});

test('the isolated demo cannot construct network work even with an API client supplied', async () => {
  const store = await LocalStore.open(uuid());
  await store.setSetting('demo', true);
  const engine = new SyncEngine(store, {
    async request<T>(): Promise<T> {
      throw new Error('No demo networking');
    },
    async upload() {
      throw new Error('No demo networking');
    },
  });
  await assert.rejects(
    engine.synchronise(),
    (error: unknown) => error instanceof APIError && error.code === 'demo_server_unavailable',
  );
  store.close();
});
