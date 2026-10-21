import 'fake-indexeddb/auto';
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { LocalStore } from './store.ts';
import { rebuildFromServer } from './recovery.ts';
import { emptyRecipe, uuid } from './domain.ts';
import type { APIClient } from './api.ts';

test('snapshot recovery verifies every page and final retained-history proof before replacing records', async () => {
  const instance = uuid(),
    store = await LocalStore.open(instance),
    id = uuid();
  await store.saveBatch([{ kind: 'recipe', id, value: { ...emptyRecipe(), title: 'Pending' } }]);
  const token = 'a'.repeat(32);
  let forked = true;
  const api = {
    request: async (path: string) =>
      path.includes('/snapshot')
        ? {
            instance_id: instance,
            checkpoint: { cursor: 1, token },
            changes: [
              {
                entity_id: uuid(),
                kind: 'recipe',
                revision: 1,
                deleted: false,
                payload: { ...emptyRecipe(), title: 'Server' },
                updated_at: '2026-10-21T00:00:00Z',
              },
            ],
            next_after: null,
          }
        : {
            instance_id: instance,
            cursor: 1,
            token,
            requested_cursor: path.endsWith('cursor=0') ? 0 : 1,
            requested_token: path.endsWith('cursor=0') ? 'root' : forked ? 'b'.repeat(32) : token,
          },
  } as Pick<APIClient, 'request'>;
  await assert.rejects(rebuildFromServer(store, api));
  assert.equal((await store.pending()).length, 1);
  assert.equal((await store.entities('recipe'))[0].payload.title, 'Pending');
  assert.equal((await store.archives()).length, 0);
  forked = false;
  await rebuildFromServer(store, api);
  assert.equal((await store.entities('recipe'))[0].payload.title, 'Server');
  assert.equal((await store.archives())[0].outbox.length, 1);
  store.close();
});
