import test from 'node:test';
import assert from 'node:assert/strict';
import 'fake-indexeddb/auto';
import { LocalStore } from './store.ts';
import { parseShopping, SHOPPING_CACHE } from './shopping.ts';

test('server shopping snapshot keeps exact quantities and ownership statuses across offline reopen', async () => {
  const value = {
    period: '2026-10-19',
    calculated_at: 1792400000,
    planned_meals: 1,
    excluded_staples: ['Salt'],
    last_success_at: null,
    job_state: 'failed',
    error_code: 'bring_capability_unverified',
    verification_state: 'idle',
    verification_error: null,
    list_id: 'synthetic-list',
    list_name: 'Synthetic shopping list',
    connection_state: 'compatibility_unverified',
    requirements: [
      { id: 'rice-g', name: 'Rice', spec: '400 g', sources: 2, state: 'not_sent' },
      { id: 'rice-ml', name: 'Rice', spec: '100 ml', sources: 1, state: 'purchased' },
    ],
  };
  let store = await LocalStore.open(crypto.randomUUID());
  const instance = store.instanceID;
  await store.setSetting(SHOPPING_CACHE, parseShopping(value));
  store.close();
  store = await LocalStore.open(instance);
  assert.deepEqual(parseShopping(await store.setting(SHOPPING_CACHE, null)), value);
  assert.equal((await store.pending()).length, 0);
  store.close();
});

test('invalid cached shopping data cannot silently become a valid result', () => {
  for (const value of [
    null,
    {},
    { period: 'not-a-date' },
    {
      period: '2026-10-19',
      calculated_at: 1,
      excluded_staples: [],
      requirements: [{ id: 'x', name: 'Rice', spec: '2', state: 'made-up-success' }],
    },
  ]) {
    assert.throws(() => parseShopping(value));
  }
});
