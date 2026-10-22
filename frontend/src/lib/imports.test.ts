import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { extractionPreview, sourceKind } from './imports.ts';
import type { Extraction } from './imports.ts';
import { payload, uuid } from './domain.ts';
import { LocalStore } from './store.ts';
import { SyncEngine } from './sync.ts';

function result(): Extraction {
  return JSON.parse(
    readFileSync(
      new URL('../../../contracts/recipe-import/examples/extraction-result.json', import.meta.url),
      'utf8',
    ),
  ) as Extraction;
}

test('neutral extraction preserves amounts, timers and source text through review normalization', () => {
  const draft = extractionPreview(result(), 'https://example.org/recipe');
  const saved = payload('recipe', draft);
  assert.equal(saved.servings, '2');
  assert.equal(saved.times?.cookMinutes, 15);
  assert.equal(saved.ingredients[0].quantity_text, '200 g');
  assert.equal(saved.ingredients[0].quantity, '200');
  assert.equal(saved.language, 'de-CH');
  assert.equal(saved.source_url, 'https://example.org/recipe');
  assert.deepEqual(saved.tags, ['pasta', 'vegetarisch']);
});

test('missing OCR facts stay editable and cannot pass canonical validation before correction', () => {
  const data = result();
  data.recipe.title = null;
  data.recipe.servings = null;
  data.recipe.ingredients[0].name = null;
  const draft = extractionPreview(data);
  assert.equal(draft.title, '');
  assert.equal(draft.servings, '');
  assert.equal(draft.ingredients[0].name, '');
  assert.throws(() => payload('recipe', draft));
});

test('media capabilities classify explicit formats and reject arbitrary files', () => {
  assert.equal(sourceKind('image/webp'), 'image');
  assert.equal(sourceKind('application/pdf'), 'pdf');
  assert.equal(sourceKind('video/mp4'), 'video');
  assert.equal(sourceKind('text/html'), null);
  assert.equal(sourceKind('image/heic'), null);
});

test('queued source bytes survive reload and recovery export, then upload before import submission', async () => {
  const instance = uuid(),
    id = uuid(),
    sourceID = uuid();
  let store = await LocalStore.open(instance);
  const device = await store.device();
  await store.saveImport({
    id,
    body: { source_id: sourceID, use_ai: true, consent_external_ai: true },
    state: 'queued',
    source: { name: 'scan.pdf', blob: new Blob(['synthetic PDF'], { type: 'application/pdf' }) },
  });
  store.close();
  store = await LocalStore.open(instance);
  const exported = (await store.localExport()) as { media: { source: boolean; base64: string }[] };
  assert.equal(atob(exported.media[0].base64), 'synthetic PDF');
  assert.equal(exported.media[0].source, true);
  const calls: string[] = [];
  await new SyncEngine(store, {
    async request<T>(path: string, init?: RequestInit): Promise<T> {
      let response: unknown;
      if (path.startsWith('/api/v1/sync/state'))
        response = {
          instance_id: instance,
          cursor: 0,
          token: 'root',
          requested_cursor: 0,
          requested_token: 'root',
        };
      else if (path.endsWith('/session')) response = { device_id: device, authenticated: true };
      else if (path.startsWith('/api/v1/sync/pull'))
        response = { changes: [], cursor: 0, cursor_token: 'root', has_more: false };
      else if (path.startsWith('/api/v1/import-sources/')) {
        assert.equal(path, '/api/v1/import-sources/' + sourceID);
        assert.ok(init?.body instanceof FormData);
        assert.equal(await (init.body.get('file') as Blob).text(), 'synthetic PDF');
        calls.push('upload');
        response = { id: sourceID };
      } else if (path === '/api/v1/imports') {
        calls.push('submit');
        response = { id };
      } else if (path === '/api/v1/imports/' + id)
        response = { id, state: 'preview', extraction: result(), warnings: [] };
      else throw Error('unexpected request ' + path);
      return response as T;
    },
    async upload() {
      throw Error('No recipe photo expected');
    },
  }).synchronise();
  assert.deepEqual(calls, ['upload', 'submit']);
  const task = (await store.imports())[0];
  assert.equal(task.state, 'preview');
  assert.equal(task.recipe?.times?.prepMinutes, 10);
  assert.equal(task.source, undefined);
  assert.equal(task.extraction?.schemaVersion, '1.0.0');
  store.close();
});

test('cancelling a cloud source during upload prevents import creation and keeps cancellation durable', async () => {
  const store = await LocalStore.open(uuid());
  const id = uuid(),
    sourceID = uuid(),
    device = await store.device();
  const task = {
    id,
    body: { source_id: sourceID, use_ai: true, consent_external_ai: true },
    state: 'queued' as const,
    source: { name: 'scan.pdf', blob: new Blob(['synthetic PDF']) },
  };
  await store.saveImport(task);
  let submissions = 0;
  const engine = new SyncEngine(store, {
    async request<T>(path: string, init?: RequestInit): Promise<T> {
      let response: unknown;
      if (path.startsWith('/api/v1/sync/state'))
        response = {
          instance_id: store.instanceID,
          cursor: 0,
          token: 'root',
          requested_cursor: 0,
          requested_token: 'root',
        };
      else if (path.endsWith('/session')) response = { device_id: device, authenticated: true };
      else if (path.startsWith('/api/v1/sync/pull'))
        response = { changes: [], cursor: 0, cursor_token: 'root', has_more: false };
      else if (path.startsWith('/api/v1/import-sources/')) {
        await store.saveImport({ ...task, state: 'cancel_pending' });
        response = { id: sourceID };
      } else if (init?.method === 'DELETE') response = undefined;
      else {
        submissions++;
        throw new Error('Unexpected import submission');
      }
      return response as T;
    },
    async upload() {
      throw new Error('No recipe photo expected');
    },
  });
  await engine.synchronise();
  assert.equal((await store.imports())[0].state, 'cancel_pending');
  await engine.synchronise();
  assert.equal((await store.imports())[0].state, 'cancelled');
  assert.equal(submissions, 0);
  store.close();
});
