import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { openDB } from 'idb';
import { emptyRecipe, entityKey, uuid } from './domain.ts';
import { databaseExists, legacy } from './legacy.ts';
import { LocalStore } from './store.ts';

test('an installed preview keeps its exact offline outbox, device, photos, imports and drafts', async () => {
  const instance = uuid(),
    device = uuid(),
    id = uuid(),
    mid = uuid(),
    photoID = uuid();
  const name = legacy.prefix + ':' + instance;
  const db = await openDB(name, 1, {
    upgrade(database) {
      database.createObjectStore('entities', { keyPath: 'key' }).createIndex('kind', 'kind');
      database
        .createObjectStore('outbox', { keyPath: 'sequence', autoIncrement: true })
        .createIndex('mutation', 'mutation.mutation_id', { unique: true });
      database.createObjectStore('photos', { keyPath: 'id' });
      database.createObjectStore('meta');
      database.createObjectStore('drafts');
      database.createObjectStore('imports', { keyPath: 'id' });
      database.createObjectStore('archives');
    },
  });
  const recipe = { ...emptyRecipe(), title: 'Unsynchronised dinner' };
  const queued = {
    sequence: 7,
    mutation: {
      mutation_id: mid,
      idempotency_key: mid,
      entity_id: id,
      kind: 'recipe',
      operation: 'upsert',
      base_revision: 0,
      device_id: device,
      client_timestamp: '2000-01-01T00:00:00Z',
      payload: recipe,
    },
  };
  const tx = db.transaction(
    ['entities', 'outbox', 'photos', 'meta', 'drafts', 'imports', 'archives'],
    'readwrite',
  );
  await tx.objectStore('entities').put({
    key: entityKey('recipe', id),
    kind: 'recipe',
    id,
    revision: 0,
    deleted: false,
    payload: recipe,
  });
  await tx.objectStore('outbox').put(queued);
  await tx.objectStore('meta').put(device, 'device');
  await tx.objectStore('meta').put({ cursor: 0, token: 'root' }, 'anchor');
  await tx
    .objectStore('photos')
    .put({ id: photoID, blob: new Blob(['original photo']), pending: true });
  await tx
    .objectStore('drafts')
    .put({ value: recipe, photo: new Blob(['draft photo']) }, 'recipe:new');
  await tx.objectStore('imports').put({
    id: uuid(),
    body: { text: 'Queued recipe', use_ai: false, consent_external_ai: false },
    state: 'queued',
  });
  await tx.objectStore('archives').put(
    {
      created_at: '2026-10-21T00:00:00Z',
      reason: 'sync_history_changed',
      entities: [],
      outbox: [queued],
    },
    'saved-recovery',
  );
  await tx.done;
  db.close();
  const store = await LocalStore.open(instance);
  assert.equal(store.namespace, name);
  assert.equal(store.syncLock, legacy.prefix + '-sync:' + instance);
  assert.equal(await databaseExists('mealf:' + instance), false);
  assert.equal(await store.device(), device);
  assert.deepEqual(await store.pending(), [queued]);
  assert.equal((await store.entities('recipe'))[0].payload.title, recipe.title);
  assert.equal(await (await store.photos())[0].blob.text(), 'original photo');
  assert.equal(await (await store.draft('recipe:new'))?.photo?.text(), 'draft photo');
  assert.equal((await store.imports())[0].state, 'queued');
  assert.deepEqual((await store.archives())[0].outbox, [queued]);
  store.close();
  const reopened = await LocalStore.open(instance);
  assert.deepEqual(await reopened.pending(), [queued]);
  reopened.close();
});

test('new installations use Mealf and ambiguous duplicate namespaces fail without deleting either', async () => {
  const instance = uuid();
  const store = await LocalStore.open(instance);
  assert.equal(store.namespace, 'mealf:' + instance);
  assert.equal(store.syncLock, 'mealf-sync:' + instance);
  await store.saveDraft('keep', { title: 'Never discard' });
  store.close();
  const previous = await openDB(legacy.prefix + ':' + instance, 1);
  previous.close();
  await assert.rejects(LocalStore.open(instance), /local_storage_namespace_conflict/);
  assert.equal(await databaseExists(legacy.prefix + ':' + instance), true);
  const current = await openDB('mealf:' + instance);
  assert.deepEqual((await current.get('drafts', 'keep')).value, { title: 'Never discard' });
  current.close();
});

test('the non-enumerating browser probe never leaves an empty database behind', async () => {
  const descriptor = Object.getOwnPropertyDescriptor(indexedDB, 'databases');
  Object.defineProperty(indexedDB, 'databases', { configurable: true, value: undefined });
  const name = 'probe:' + uuid();
  try {
    assert.equal(await databaseExists(name), false);
    const db = await openDB(name, 1);
    db.close();
    assert.equal(await databaseExists(name), true);
  } finally {
    if (descriptor) Object.defineProperty(indexedDB, 'databases', descriptor);
    else Reflect.deleteProperty(indexedDB, 'databases');
  }
});
