import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { APIError } from './api.ts';
import { emptyRecipe, uuid } from './domain.ts';
import { prepareImportImage } from './image-import.ts';
import { LocalStore } from './store.ts';
import type { ImportTask } from './store.ts';
import { SyncEngine } from './sync.ts';

async function transport(
  store: LocalStore,
  handle: (path: string, init?: RequestInit) => Promise<unknown>,
  upload: (id: string, blob: Blob) => Promise<void>,
) {
  const device = await store.device();
  return {
    async request<T>(path: string, init?: RequestInit): Promise<T> {
      if (path.startsWith('/api/v1/sync/state'))
        return {
          instance_id: store.instanceID,
          cursor: 0,
          token: 'root',
          requested_cursor: 0,
          requested_token: 'root',
        } as T;
      if (path.endsWith('/session')) return { device_id: device } as T;
      if (path.startsWith('/api/v1/sync/pull'))
        return { changes: [], cursor: 0, cursor_token: 'root', has_more: false } as T;
      return (await handle(path, init)) as T;
    },
    upload,
  };
}
function task(): ImportTask {
  return {
    id: uuid(),
    state: 'queued',
    body: { image_id: uuid(), use_ai: false, consent_external_ai: false },
  };
}

test('image queue and original bytes survive reopening and recovery export', async () => {
  const instance = uuid();
  let store = await LocalStore.open(instance);
  const value = task(),
    blob = new Blob(['durable photo bytes'], { type: 'image/jpeg' });
  await store.saveImport(value, { id: value.body.image_id!, blob, pending: true });
  store.close();
  store = await LocalStore.open(instance);
  assert.equal((await store.imports())[0].body.image_id, value.body.image_id);
  assert.equal(await (await store.photo(value.body.image_id!))!.blob.text(), 'durable photo bytes');
  const backup = JSON.parse(JSON.stringify(await store.localExport()));
  assert.equal(backup.imports[0].id, value.id);
  assert.equal(
    atob(backup.media.find((p: { id: string }) => p.id === value.body.image_id).base64),
    'durable photo bytes',
  );
  assert.deepEqual(await store.entities('recipe'), []);
  store.close();
});

test('lost import response retries the same identity and does not reupload an acknowledged image', async () => {
  const store = await LocalStore.open(uuid()),
    value = task();
  await store.saveImport(value, {
    id: value.body.image_id!,
    blob: new Blob(['photo']),
    pending: true,
  });
  let uploads = 0,
    posts = 0;
  const sent: string[] = [];
  const api = await transport(
    store,
    async (path, init) => {
      if (path === '/api/v1/imports') {
        const body = JSON.parse(String(init?.body));
        sent.push(body.request_id);
        posts++;
        assert.equal(body.image_id, value.body.image_id);
        if (posts === 1) throw new APIError('connection_unavailable', 0);
        return { id: value.id };
      }
      if (path === '/api/v1/imports/' + value.id)
        return {
          id: value.id,
          state: 'preview',
          recipe: { ...emptyRecipe(), title: 'Reviewed later', image_id: value.body.image_id },
          warnings: ['image_text_requires_review'],
          recognized_text: 'Original recognized recipe',
        };
      throw new Error(path);
    },
    async (id, blob) => {
      assert.equal(id, value.body.image_id);
      assert.equal(await blob.text(), 'photo');
      uploads++;
    },
  );
  const engine = new SyncEngine(store, api);
  await assert.rejects(engine.synchronise(), APIError);
  assert.equal((await store.imports())[0].state, 'queued');
  await engine.synchronise();
  assert.equal(uploads, 1);
  assert.equal(posts, 2);
  assert.deepEqual(sent, [value.id, value.id]);
  const saved = (await store.imports())[0];
  assert.equal(saved.state, 'preview');
  assert.equal(saved.recognizedText, 'Original recognized recipe');
  assert.equal((await store.photo(value.body.image_id!))?.pending, false);
  assert.deepEqual(await store.entities('recipe'), []);
  store.close();
});

test('cancellation during image upload prevents import submission and stale polls cannot undo it', async () => {
  const store = await LocalStore.open(uuid()),
    value = task();
  await store.saveImport(value, {
    id: value.body.image_id!,
    blob: new Blob(['photo']),
    pending: true,
  });
  let posts = 0;
  const api = await transport(
    store,
    async (path, init) => {
      if (init?.method === 'DELETE') throw new APIError('not_found', 404);
      posts++;
      throw new Error('Unexpected import submission: ' + path);
    },
    async () => {
      await store.saveImport({ ...value, state: 'cancel_pending' });
    },
  );
  const engine = new SyncEngine(store, api);
  await engine.synchronise();
  assert.equal((await store.imports())[0].state, 'cancel_pending');
  await store.saveImport({ ...value, state: 'preview' });
  assert.equal((await store.imports())[0].state, 'cancel_pending');
  await engine.synchronise();
  assert.equal((await store.imports())[0].state, 'cancelled');
  assert.equal(posts, 0);
  await store.saveImport({ ...value, state: 'queued' });
  assert.equal((await store.imports())[0].state, 'cancelled');
  store.close();
});

test('mismatched image and import identities write neither record', async () => {
  const store = await LocalStore.open(uuid()),
    value = task(),
    other = uuid();
  await assert.rejects(
    store.saveImport(value, { id: other, blob: new Blob(['photo']), pending: true }),
    /invalid_import_photo/,
  );
  assert.deepEqual(await store.imports(), []);
  assert.equal(await store.photo(other), undefined);
  store.close();
});

test('active image content is rejected by signature before any browser decoder runs', async () => {
  await assert.rejects(
    prepareImportImage(
      new File(['<svg onload="alert(1)"></svg>'], 'fake.jpg', { type: 'image/jpeg' }),
    ),
    /imageInputError/,
  );
  await assert.rejects(
    prepareImportImage(new File([], 'empty.png', { type: 'image/png' })),
    /imageInputError/,
  );
});

test('terminal import history cannot starve a newly queued photo', async () => {
  const store = await LocalStore.open(uuid());
  for (let index = 0; index < 100; index++) {
    await store.saveImport({
      ...task(),
      id: `00000000-0000-4000-8000-${String(index).padStart(12, '0')}`,
      state: index % 2 ? 'cancelled' : 'confirmed',
    });
  }
  const value = { ...task(), id: 'ffffffff-ffff-4fff-8fff-ffffffffffff' };
  await store.saveImport(value, {
    id: value.body.image_id!,
    blob: new Blob(['photo']),
    pending: true,
  });
  let uploads = 0;
  const api = await transport(
    store,
    async (path) => {
      if (path === '/api/v1/imports') return { id: value.id };
      assert.equal(path, '/api/v1/imports/' + value.id);
      return { id: value.id, state: 'preview', recipe: { ...emptyRecipe(), title: 'Photo rice' } };
    },
    async () => {
      uploads++;
    },
  );
  await new SyncEngine(store, api).synchronise();
  assert.equal(uploads, 1);
  assert.equal((await store.imports()).find((item) => item.id === value.id)?.state, 'preview');
  store.close();
});
