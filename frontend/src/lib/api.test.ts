import assert from 'node:assert/strict';
import { test } from 'node:test';
import { APIClient, APIError, csrfToken } from './api.ts';

test('repeated sync reads bypass URL-keyed proxy caches at the same cursor', async () => {
  const previousFetch = globalThis.fetch;
  const previousDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
  Object.defineProperty(globalThis, 'document', { configurable: true, value: { cookie: '' } });
  const cache = new Map<string, number>();
  let head = 0;
  globalThis.fetch = async (input, init) => {
    const url = new URL(String(input), 'https://test.invalid');
    assert.match(url.searchParams.get('_mealf_sync') ?? '', /^[a-f\d-]{36}$/i);
    assert.equal(new Headers(init?.headers).get('Cache-Control'), 'no-cache, no-store');
    if (!cache.has(String(input))) cache.set(String(input), head);
    return Response.json({ cursor: cache.get(String(input)) });
  };
  try {
    const api = new APIClient();
    assert.deepEqual(await api.request('/api/v1/sync/state?cursor=0'), { cursor: 0 });
    head = 1;
    assert.deepEqual(await api.request('/api/v1/sync/state?cursor=0'), { cursor: 1 });
    assert.equal(cache.size, 2);
  } finally {
    globalThis.fetch = previousFetch;
    if (previousDocument) Object.defineProperty(globalThis, 'document', previousDocument);
    else Reflect.deleteProperty(globalThis, 'document');
  }
});

test('previous cookies remain readable until rotation; an explicit current cookie takes precedence', () => {
  const priorDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
  const document = { cookie: 'aircooker_pwa_csrf=existing' };
  Object.defineProperty(globalThis, 'document', { configurable: true, value: document });
  try {
    assert.equal(csrfToken(), 'existing');
    document.cookie += '; mealf_pwa_csrf=current';
    assert.equal(csrfToken(), 'current');
    document.cookie = 'aircooker_pwa_csrf=existing; mealf_pwa_csrf=';
    assert.equal(csrfToken(), '');
  } finally {
    if (priorDocument) Object.defineProperty(globalThis, 'document', priorDocument);
    else Reflect.deleteProperty(globalThis, 'document');
  }
});

test('concurrent expired requests share one refresh and retry with browser cookies', async () => {
  const priorFetch = globalThis.fetch;
  const priorDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
  Object.defineProperty(globalThis, 'document', {
    configurable: true,
    value: { cookie: 'mealf_pwa_csrf=test-csrf' },
  });
  let refreshed = false;
  let refreshCalls = 0;
  globalThis.fetch = async (input, init) => {
    assert.equal(init?.credentials, 'same-origin');
    const headers = new Headers(init?.headers);
    assert.equal(headers.get('X-Mealf-Client'), 'pwa');
    if (String(input).endsWith('/refresh')) {
      assert.equal(headers.get('X-CSRF-Token'), 'test-csrf');
      refreshCalls += 1;
      refreshed = true;
      return Response.json({ authenticated: true });
    }
    return refreshed
      ? Response.json({ items: [] })
      : Response.json({ error: { code: 'authentication_required' } }, { status: 401 });
  };
  try {
    const client = new APIClient();
    const results = await Promise.all([
      client.request('/api/v1/recipes'),
      client.request('/api/v1/recipes'),
    ]);
    assert.equal(refreshCalls, 1);
    assert.deepEqual(results, [{ items: [] }, { items: [] }]);
  } finally {
    globalThis.fetch = priorFetch;
    if (priorDocument) Object.defineProperty(globalThis, 'document', priorDocument);
    else Reflect.deleteProperty(globalThis, 'document');
  }
});

test('a parallel CSRF rotation retries once; unrelated forbidden errors are surfaced', async () => {
  const priorFetch = globalThis.fetch;
  const priorDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
  const document = { cookie: 'mealf_pwa_csrf=before' };
  Object.defineProperty(globalThis, 'document', { configurable: true, value: document });
  let calls = 0;
  globalThis.fetch = async (_input, init) => {
    calls += 1;
    if (calls === 1) {
      document.cookie = 'mealf_pwa_csrf=after';
      return Response.json({ error: { code: 'csrf_failed' } }, { status: 403 });
    }
    assert.equal(new Headers(init?.headers).get('X-CSRF-Token'), 'after');
    return Response.json({ saved: true });
  };
  try {
    const client = new APIClient();
    assert.deepEqual(await client.request('/api/v1/sync/push', { method: 'POST', body: '{}' }), {
      saved: true,
    });
    assert.equal(calls, 2);
    globalThis.fetch = async () => {
      calls += 1;
      return Response.json({ error: { code: 'origin_forbidden' } }, { status: 403 });
    };
    await assert.rejects(
      client.request('/api/v1/sync/push', { method: 'POST', body: '{}' }),
      (error: unknown) => error instanceof APIError && error.code === 'origin_forbidden',
    );
    assert.equal(calls, 3);
  } finally {
    globalThis.fetch = priorFetch;
    if (priorDocument) Object.defineProperty(globalThis, 'document', priorDocument);
    else Reflect.deleteProperty(globalThis, 'document');
  }
});

test('external paths, malformed JSON and network failures have bounded redacted errors', async () => {
  const priorFetch = globalThis.fetch;
  const client = new APIClient();
  try {
    await assert.rejects(
      client.request('https://other.invalid/api/v1/recipes'),
      (error: unknown) => error instanceof APIError && error.code === 'invalid_api_path',
    );
    globalThis.fetch = async () => new Response('private malformed response', { status: 200 });
    await assert.rejects(
      client.request('/api/v1/recipes'),
      (error: unknown) => error instanceof APIError && error.message === 'invalid_server_response',
    );
    globalThis.fetch = async () => {
      throw new TypeError('private transport detail');
    };
    await assert.rejects(
      client.request('/api/v1/recipes'),
      (error: unknown) =>
        error instanceof APIError && error.code === 'connection_unavailable' && error.status === 0,
    );
  } finally {
    globalThis.fetch = priorFetch;
  }
});
