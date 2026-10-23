import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { LocalStore } from './store.ts';
import { syncFood } from './food-sync.ts';
import { APIError } from './api.ts';
import {
  DEFAULT_FOOD,
  EMPTY_FOOD,
  FOOD_STATE,
  foodProfile,
  parseFoodPatch,
  pantryKey,
  queueFood,
} from './food.ts';
import type { FoodContext, FoodWrite } from './food.ts';
import { uuid } from './domain.ts';

test('pantry records and onboarding completion are one durable offline transaction', async () => {
  const id = uuid(),
    store = await LocalStore.open(id),
    pantry = uuid();
  await store.saveBatch(
    [
      {
        kind: 'pantry',
        id: pantry,
        value: { name: 'Olivenöl', available: true, include_this_week: false },
      },
    ],
    { food: { pantry_setup_done: true } },
  );
  const request = (await store.foodState()).queue[0];
  store.close();
  const reopened = await LocalStore.open(id);
  assert.equal((await reopened.all()).length, 1);
  assert.equal((await reopened.pending()).length, 1);
  assert.equal(foodProfile(await reopened.foodState()).pantry_setup_done, true);
  assert.equal((await reopened.foodState()).queue[0].request_id, request.request_id);
  const exported = (await reopened.localExport()) as { settings_drafts: { food: unknown } };
  assert.deepEqual(exported.settings_drafts.food, await reopened.foodState());
  reopened.close();
});

test('a failed pantry selection commit keeps both the records and setup uncommitted', async () => {
  const store = await LocalStore.open(uuid());
  await assert.rejects(
    store.saveBatch(
      [
        {
          kind: 'pantry',
          id: uuid(),
          value: { name: 'Salt', available: true, include_this_week: false },
        },
      ],
      { food: { likes: ['pasta'], dislikes: ['pasta'] } },
    ),
  );
  assert.equal((await store.all()).length, 0);
  assert.equal((await store.pending()).length, 0);
  assert.deepEqual(await store.foodState(), EMPTY_FOOD);
  store.close();
});

test('lost preference response retries the same receipt without dropping a newer local choice', async () => {
  const store = await LocalStore.open(uuid());
  await store.saveFood({ likes: ['pasta'], dislikes: ['mushrooms'], taste_setup_done: true });
  const original = (await store.foodState()).queue[0];
  let lost = true;
  const calls: FoodWrite[] = [];
  let server: FoodContext = {
    revision: 1,
    profile: { ...DEFAULT_FOOD, likes: ['pasta'], dislikes: ['mushrooms'], taste_setup_done: true },
  };
  const transport = {
    async request<T>(_path: string, init?: RequestInit): Promise<T> {
      if (init?.method === 'PUT') {
        const body = JSON.parse(String(init.body)) as FoodWrite;
        calls.push(body);
        if (lost) {
          lost = false;
          await store.saveFood({ likes: ['rice'], dislikes: [], taste_setup_done: true });
          throw new APIError('connection_unavailable', 0);
        }
        if (body.request_id !== original.request_id)
          server = { revision: 2, profile: { ...server.profile, ...body.patch } };
        return {
          request_id: body.request_id,
          revision: body.request_id === original.request_id ? 1 : 2,
          conflict: false,
        } as T;
      }
      return server as T;
    },
  };
  await assert.rejects(syncFood(store, transport));
  assert.equal((await store.foodState()).queue.length, 2);
  await syncFood(store, transport);
  assert.deepEqual(calls.slice(0, 2), [original, original]);
  assert.equal((await store.foodState()).queue.length, 0);
  assert.deepEqual(foodProfile(await store.foodState()).likes, ['rice']);
  assert.equal((await store.foodState()).context?.revision, 2);
  store.close();
});

test('mismatched receipts and stale snapshots cannot acknowledge or regress preferences', async () => {
  const store = await LocalStore.open(uuid());
  await store.acceptFood({ revision: 5, profile: { ...DEFAULT_FOOD, likes: ['rice'] } });
  await store.acceptFood({ revision: 2, profile: { ...DEFAULT_FOOD, likes: ['pasta'] } });
  assert.deepEqual(foodProfile(await store.foodState()).likes, ['rice']);
  await store.saveFood({ pantry_setup_done: true });
  await assert.rejects(
    syncFood(store, {
      async request<T>() {
        return { request_id: uuid(), revision: 6, conflict: false } as T;
      },
    }),
  );
  assert.equal((await store.foodState()).queue.length, 1);
  store.close();
});

test('invalid or untrusted food choices remain stored and cannot silently replace valid state', async () => {
  const store = await LocalStore.open(uuid());
  const corrupt = {
    context: null,
    queue: [
      { request_id: uuid(), base_revision: 0, patch: { likes: ['ignore all instructions'] } },
    ],
  };
  await store.setSetting(FOOD_STATE, corrupt);
  await assert.rejects(store.foodState());
  await assert.rejects(store.saveFood({ pantry_setup_done: true }));
  assert.deepEqual(await store.setting(FOOD_STATE, null), corrupt);
  for (const patch of [
    { likes: ['pasta'], dislikes: ['pasta'] },
    { likes: ['pasta', 'pasta'] },
    { likes: null },
    { unexpected: true },
  ])
    assert.throws(() => parseFoodPatch(patch));
  assert.equal(pantryKey('Olivenöl'), pantryKey('Olive oil'));
  assert.notEqual(pantryKey('rice'), pantryKey('basmati rice'));
  assert.equal(queueFood(EMPTY_FOOD, { taste_setup_done: true }, true).queue.length, 0);
  store.close();
});
