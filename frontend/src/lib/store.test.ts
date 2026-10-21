import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { LocalStore } from './store.ts';
import { emptyRecipe, entityKey, uuid } from './domain.ts';
import type { Change, Meal } from './domain.ts';

const token = 'a'.repeat(32);
test('offline edits, queue identities and drafts survive closing the local database', async () => {
  const instance = uuid();
  const store = await LocalStore.open(instance);
  const id = uuid();
  const recipe = { ...emptyRecipe(), title: 'Offline soup' };
  await store.saveDraft('new-recipe', recipe);
  await store.saveBatch([{ kind: 'recipe', id, value: recipe }], { draft: 'new-recipe' });
  const pending = await store.pending();
  const device = await store.device();
  store.close();
  const reopened = await LocalStore.open(instance);
  assert.deepEqual(await reopened.pending(), pending);
  assert.equal(await reopened.device(), device);
  assert.equal((await reopened.entities('recipe'))[0].payload.title, recipe.title);
  assert.equal(await reopened.draft('new-recipe'), undefined);
  reopened.close();
});

test('invalid leftover booking rolls back recipes, photos, draft deletion and outgoing mutations', async () => {
  const store = await LocalStore.open(uuid());
  const recipeID = uuid();
  await store.saveDraft('recipe', { title: 'Still here' });
  const meal: Meal = {
    recipe_id: recipeID,
    date: '2026-10-21',
    category: 'dinner',
    servings: '2',
    cooked: false,
    order: 0,
    leftover_id: uuid(),
  };
  await assert.rejects(
    store.saveBatch(
      [
        { kind: 'recipe', id: recipeID, value: { ...emptyRecipe(), title: 'Soup' } },
        { kind: 'meal', id: uuid(), value: meal },
      ],
      { photos: [{ id: uuid(), blob: new Blob(['sample']), pending: true }], draft: 'recipe' },
    ),
    /leftover_unavailable/,
  );
  assert.deepEqual(await store.all(), []);
  assert.deepEqual(await store.pending(), []);
  assert.deepEqual(await store.photos(), []);
  assert.ok(await store.draft('recipe'));
  store.close();
});

test('incoming changes cannot replace unsent edits and rejected deletions keep the queue', async () => {
  const store = await LocalStore.open(uuid());
  const id = uuid();
  await store.saveBatch([
    { kind: 'recipe', id, value: { ...emptyRecipe(), title: 'My offline draft' } },
  ]);
  const queued = (await store.pending())[0];
  const change: Change = {
    revision: 2,
    kind: 'recipe',
    entity_id: id,
    deleted: true,
    payload: {},
    updated_at: '2026-10-21T00:00:00Z',
  };
  await store.merge([change], { cursor: 2, token });
  assert.equal((await store.entities('recipe'))[0].payload.title, 'My offline draft');
  assert.equal((await store.entities('recipe'))[0].serverShadow?.deleted, true);
  await store.acknowledge({
    mutation_id: queued.mutation.mutation_id,
    status: 'rejected_tombstone',
    revision: 2,
    conflict: true,
  });
  assert.equal((await store.pending())[0].blocked, 'rejected_tombstone');
  assert.equal((await store.entities('recipe'))[0].payload.title, 'My offline draft');
  store.close();
});

test('an older acknowledgement cannot erase a newer local edit', async () => {
  const store = await LocalStore.open(uuid());
  const id = uuid();
  await store.saveBatch([{ kind: 'recipe', id, value: { ...emptyRecipe(), title: 'First' } }]);
  const first = (await store.pending())[0];
  await store.saveBatch([{ kind: 'recipe', id, value: { ...emptyRecipe(), title: 'Second' } }]);
  await store.acknowledge({
    mutation_id: first.mutation.mutation_id,
    status: 'accepted',
    revision: 1,
    conflict: false,
  });
  assert.equal((await store.pending()).length, 1);
  assert.equal((await store.entities('recipe'))[0].payload.title, 'Second');
  await store.merge(
    [
      {
        revision: 1,
        kind: 'recipe',
        entity_id: id,
        deleted: false,
        payload: { ...emptyRecipe(), title: 'First' },
        updated_at: '2026-10-21T00:00:00Z',
      },
    ],
    { cursor: 1, token },
  );
  assert.equal((await store.entities('recipe'))[0].payload.title, 'Second');
  store.close();
});

test('server order replaces synchronised records and stale pages cannot regress the cursor', async () => {
  const store = await LocalStore.open(uuid());
  const id = uuid();
  const change = (revision: number, title: string): Change => ({
    revision,
    kind: 'recipe',
    entity_id: id,
    deleted: false,
    payload: { ...emptyRecipe(), title },
    updated_at: '2000-01-01T00:00:00Z',
  });
  await store.merge([change(2, 'Server second')], { cursor: 2, token });
  await assert.rejects(
    store.merge([change(1, 'Server first')], { cursor: 1, token }),
    /stale_sync_page/,
  );
  assert.equal((await store.entities('recipe'))[0].payload.title, 'Server second');
  assert.equal((await store.anchor()).cursor, 2);
  await store.merge([{ ...change(3, 'Deleted'), deleted: true, payload: {} }], {
    cursor: 3,
    token,
  });
  assert.deepEqual(await store.entities('recipe'), []);
  await assert.rejects(
    store.saveBatch([{ kind: 'recipe', id, value: { ...emptyRecipe(), title: 'Resurrect' } }]),
    /deleted_identity/,
  );
  assert.equal((await store.all())[0].key, entityKey('recipe', id));
  store.close();
});

test('household identities have separate local stores', async () => {
  const a = await LocalStore.open(uuid());
  const b = await LocalStore.open(uuid());
  await a.saveBatch([
    { kind: 'recipe', id: uuid(), value: { ...emptyRecipe(), title: 'Private A' } },
  ]);
  assert.deepEqual(await b.all(), []);
  assert.deepEqual(await b.pending(), []);
  a.close();
  b.close();
});

test('storage failure after the first write rolls back the entire batch and keeps its draft', async () => {
  const store = await LocalStore.open(uuid());
  const second = uuid();
  await store.saveDraft('editing', { title: 'Unsaved text' });
  const original = IDBObjectStore.prototype.put;
  IDBObjectStore.prototype.put = function (value: unknown, key?: IDBValidKey) {
    if (
      typeof value === 'object' &&
      value !== null &&
      'key' in value &&
      value.key === entityKey('recipe', second)
    ) {
      throw new DOMException('Storage full', 'QuotaExceededError');
    }
    return original.call(this, value, key);
  };
  try {
    await assert.rejects(
      store.saveBatch(
        [
          { kind: 'recipe', id: uuid(), value: { ...emptyRecipe(), title: 'First write' } },
          { kind: 'recipe', id: second, value: { ...emptyRecipe(), title: 'Second write' } },
        ],
        { photos: [{ id: uuid(), blob: new Blob(['photo']), pending: true }], draft: 'editing' },
      ),
    );
  } finally {
    IDBObjectStore.prototype.put = original;
  }
  assert.deepEqual(await store.all(), []);
  assert.deepEqual(await store.pending(), []);
  assert.deepEqual(await store.photos(), []);
  assert.ok(await store.draft('editing'));
  store.close();
});

test('two local clients cannot reserve more leftover portions than exist', async () => {
  const instance = uuid();
  const a = await LocalStore.open(instance);
  const b = await LocalStore.open(instance);
  const recipeID = uuid();
  const leftoverID = uuid();
  await a.saveBatch([
    { kind: 'recipe', id: recipeID, value: { ...emptyRecipe(), title: 'Soup' } },
    {
      kind: 'leftover',
      id: leftoverID,
      value: { recipe_id: recipeID, portions: '2', produced_on: '2026-10-21', discarded: false },
    },
  ]);
  const value: Meal = {
    recipe_id: recipeID,
    date: '2026-10-22',
    category: 'dinner',
    servings: '2',
    cooked: false,
    order: 0,
    leftover_id: leftoverID,
  };
  const results = await Promise.allSettled([
    a.saveBatch([{ kind: 'meal', id: uuid(), value }]),
    b.saveBatch([{ kind: 'meal', id: uuid(), value }]),
  ]);
  assert.equal(results.filter((result) => result.status === 'fulfilled').length, 1);
  assert.equal((await a.entities('meal')).length, 1);
  a.close();
  b.close();
});

test('import approval marks the draft saving in the same transaction and prevents double save', async () => {
  const store = await LocalStore.open(uuid()),
    importID = uuid();
  await store.saveImport({
    id: importID,
    body: { use_ai: false, consent_external_ai: false, text: 'Soup' },
    state: 'preview',
  });
  await store.saveBatch(
    [{ kind: 'recipe', id: uuid(), value: { ...emptyRecipe(), title: 'Reviewed' } }],
    { importID },
  );
  assert.equal((await store.imports())[0].state, 'saving');
  await assert.rejects(
    store.saveBatch(
      [{ kind: 'recipe', id: uuid(), value: { ...emptyRecipe(), title: 'Duplicate' } }],
      { importID },
    ),
  );
  assert.equal((await store.entities('recipe')).length, 1);
  assert.equal((await store.pending()).length, 1);
  store.close();
});
test('server snapshot recovery archives unsent work atomically and preserves photos and drafts', async () => {
  const store = await LocalStore.open(uuid()),
    id = uuid();
  await store.saveDraft('recipe:new', { title: 'Unsaved' });
  await store.saveBatch(
    [{ kind: 'recipe', id, value: { ...emptyRecipe(), title: 'Offline work' } }],
    { photos: [{ id: uuid(), blob: new Blob(['photo'], { type: 'image/png' }), pending: true }] },
  );
  const snapshot: Change = {
    kind: 'recipe',
    entity_id: uuid(),
    revision: 1,
    deleted: false,
    payload: { ...emptyRecipe(), title: 'Restored server' },
    updated_at: '2026-10-21T00:00:00Z',
  };
  await store.replaceSnapshot([snapshot], { cursor: 1, token });
  assert.equal((await store.entities('recipe'))[0].payload.title, 'Restored server');
  assert.equal((await store.pending()).length, 0);
  const archive = (await store.archives())[0];
  assert.equal((archive.entities[0].payload as { title: string }).title, 'Offline work');
  assert.equal(archive.outbox.length, 1);
  assert.ok(await store.draft('recipe:new'));
  assert.equal((await store.photos()).length, 1);
  const exported = (await store.localExport()) as {
    media: { base64: string }[];
    drafts: { key: string }[];
  };
  assert.equal(exported.media[0].base64, btoa('photo'));
  assert.equal(exported.drafts[0].key, 'recipe:new');
  await assert.rejects(store.replaceSnapshot([{ ...snapshot, revision: 2 }], { cursor: 1, token }));
  assert.equal((await store.entities('recipe'))[0].payload.title, 'Restored server');
  store.close();
});
test('rejected recipe recovery keeps its archive and creates a new identity without resurrecting a tombstone', async () => {
  const store = await LocalStore.open(uuid()),
    id = uuid();
  await store.saveBatch([
    { kind: 'recipe', id, value: { ...emptyRecipe(), title: 'Keep my edit' } },
  ]);
  const mutation = (await store.pending())[0].mutation;
  await store.acknowledge({
    mutation_id: mutation.mutation_id,
    status: 'rejected_tombstone',
    revision: 2,
    conflict: true,
  });
  await store.merge(
    [
      {
        kind: 'recipe',
        entity_id: id,
        revision: 2,
        deleted: true,
        payload: {},
        updated_at: '2026-10-21T00:00:00Z',
      },
    ],
    { cursor: 2, token },
  );
  await store.resolveRejected(id, true);
  const recipes = await store.entities('recipe');
  assert.equal(recipes.length, 1);
  assert.notEqual(recipes[0].id, id);
  assert.equal(recipes[0].payload.title, 'Keep my edit');
  assert.equal((await store.pending())[0].mutation.base_revision, 0);
  assert.equal((await store.archives())[0].outbox[0].mutation.entity_id, id);
  store.close();
});

test('equal-revision deltas canonicalise accepted payloads and edits preserve the last known server copy', async () => {
  const store = await LocalStore.open(uuid()),
    id = uuid();
  await store.merge(
    [
      {
        kind: 'recipe',
        entity_id: id,
        revision: 1,
        deleted: false,
        payload: { ...emptyRecipe(), title: 'Server copy' },
        updated_at: '2026-10-21T00:00:00Z',
      },
    ],
    { cursor: 1, token },
  );
  await store.saveBatch([
    { kind: 'recipe', id, value: { ...emptyRecipe(), title: 'Rejected edit' } },
  ]);
  const m = (await store.pending())[0].mutation;
  await store.block(m.mutation_id, 'photo_upload_rejected');
  await store.resolveRejected(id, false);
  assert.equal((await store.entities('recipe'))[0].payload.title, 'Server copy');
  await store.saveBatch([
    { kind: 'recipe', id, value: { ...emptyRecipe(), title: 'Accepted local' } },
  ]);
  const m2 = (await store.pending())[0].mutation;
  await store.acknowledge({
    mutation_id: m2.mutation_id,
    status: 'accepted',
    revision: 2,
    conflict: false,
  });
  await store.merge(
    [
      {
        kind: 'recipe',
        entity_id: id,
        revision: 2,
        deleted: false,
        payload: { ...emptyRecipe(), title: 'Canonical server' },
        updated_at: '2026-10-21T00:00:00Z',
      },
    ],
    { cursor: 2, token },
  );
  assert.equal((await store.entities('recipe'))[0].payload.title, 'Canonical server');
  store.close();
});
