import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { APIError } from './api.ts';
import { uuid } from './domain.ts';
import { LocalStore } from './store.ts';
import { SyncEngine } from './sync.ts';

test('personal import consent survives restart and changed connection keeps text without rebinding or retrying', async () => {
  const instance = uuid(),
    connection = uuid(),
    id = uuid();
  let store = await LocalStore.open(instance);
  const device = await store.device();
  await store.saveImport({
    id,
    state: 'queued',
    body: {
      ai_account: 'chatgpt',
      chatgpt_connection_id: connection,
      use_ai: true,
      consent_external_ai: true,
      consent_chatgpt_background: true,
      ai_destination: ['chatgpt', 'https://api.openai.com/v1', 'selected-model'],
      text: 'My offline recipe text',
    },
  });
  store.close();
  store = await LocalStore.open(instance);
  let calls = 0;
  const sync = new SyncEngine(store, {
    async request<T>(path: string, init?: RequestInit): Promise<T> {
      let value: unknown;
      if (path.startsWith('/api/v1/sync/state'))
        value = {
          instance_id: instance,
          cursor: 0,
          token: 'root',
          requested_cursor: 0,
          requested_token: 'root',
        };
      else if (path.endsWith('/session')) value = { device_id: device, authenticated: true };
      else if (path.startsWith('/api/v1/sync/pull'))
        value = { changes: [], cursor: 0, cursor_token: 'root', has_more: false };
      else if (path === '/api/v1/imports') {
        const body = JSON.parse(String(init?.body));
        assert.equal(body.chatgpt_connection_id, connection);
        assert.equal(body.consent_chatgpt_background, true);
        assert.equal(body.ai_account, 'chatgpt');
        calls += 1;
        throw new APIError('chatgpt_connection_changed', 409);
      } else throw Error('Unexpected network request');
      return value as T;
    },
    async upload() {
      throw Error('Personal text import must not upload media');
    },
  });
  await sync.synchronise();
  const task = (await store.imports())[0];
  assert.equal(task.state, 'needs_input');
  assert.equal(task.error, 'chatgpt_connection_changed');
  assert.equal(task.body.text, 'My offline recipe text');
  assert.equal(task.body.chatgpt_connection_id, connection);
  await sync.synchronise();
  assert.equal(calls, 1);
  store.close();
});
