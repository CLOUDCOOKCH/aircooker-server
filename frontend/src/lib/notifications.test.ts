import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';
import { pushKey, reminderTarget } from './notifications.ts';

test('notification targets keep civil dates and reject malformed/external navigation hints', () => {
  assert.deepEqual(reminderTarget('?tab=calendar&day=2026-10-25'), {
    tab: 'calendar',
    day: '2026-10-25',
  });
  assert.deepEqual(reminderTarget('?tab=settings'), { tab: 'settings' });
  for (const search of [
    '?tab=calendar&day=2026-02-30',
    '?tab=calendar&day=0000-01-01',
    '?tab=calendar&day=https://evil.example',
    '?tab=https://evil.example',
  ])
    assert.equal(reminderTarget(search), null);
  const key = new Uint8Array(65);
  key[0] = 4;
  assert.equal(pushKey(Buffer.from(key).toString('base64url')).byteLength, 65);
  assert.throws(() => pushKey('not-a-p256-key'));
});

test('the actual push handler always displays a visible fallback and confines click navigation', async () => {
  const source = await readFile(new URL('../../public/push-handler.js', import.meta.url), 'utf8');
  type Options = { body: string; data: { url: string }; tag: string };
  const shown: { title: string; options: Options }[] = [];
  const opened: string[] = [],
    messages: unknown[] = [];
  const listeners: Record<string, (event: unknown) => void> = {};
  const origin = 'https://kitchen.example';
  const self = {
    location: { origin },
    addEventListener: (name: string, listener: (event: unknown) => void) => {
      listeners[name] = listener;
    },
    registration: {
      showNotification: async (title: string, options: Options) => {
        shown.push({ title, options });
      },
    },
    clients: {
      matchAll: async () => [
        {
          url: origin + '/',
          focus: async () => undefined,
          postMessage: (value: unknown) => messages.push(value),
        },
      ],
      openWindow: async (url: string) => {
        opened.push(url);
      },
    },
  };
  runInNewContext(source, { self, URL });
  let work: Promise<unknown> = Promise.resolve();
  const waitUntil = (value: Promise<unknown>) => {
    work = value;
  };
  listeners.push({
    data: {
      json: () => {
        throw new Error('malformed');
      },
    },
    waitUntil,
  });
  await work;
  assert.equal(shown[0].title, 'mealf');
  assert.equal(shown[0].options.body, 'mealf');
  listeners.push({
    data: {
      json: () => ({
        title: 'Impersonated title',
        body: 'A reminder',
        url: 'https://evil.example/',
        tag: 'invalid\nvalue',
      }),
    },
    waitUntil,
  });
  await work;
  assert.equal(shown[1].title, 'mealf');
  assert.equal(shown[1].options.data.url, origin + '/app/');
  assert.equal(shown[1].options.tag, 'mealf-reminder');
  listeners.notificationclick({
    notification: { close: () => undefined, data: { url: 'https://evil.example/' } },
    waitUntil,
  });
  await work;
  assert.deepEqual(opened, [origin + '/app/']);
  assert.equal(messages.length, 0); // The existing administration window is left alone.
  self.clients.matchAll = async () => [
    {
      url: origin + '/app/',
      focus: async () => undefined,
      postMessage: (value: unknown) => messages.push(value),
    },
  ];
  listeners.notificationclick({
    notification: { close: () => undefined, data: { url: '/app/?tab=calendar&day=2026-10-25' } },
    waitUntil,
  });
  await work;
  assert.equal((messages[0] as { type: string }).type, 'MEAL_REMINDER');
  assert.equal(opened.length, 1); // Existing app handles editor protection before navigation.
});
