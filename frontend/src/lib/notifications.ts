import { civil } from './domain.ts';
import type { components } from '../api-schema';
export type PushStatus = components['schemas']['PushStatus'];
export type PushPreferences = components['schemas']['ReminderPreferences'];
export type ReminderTarget = { tab: 'calendar' | 'settings'; day?: string };

export function reminderTarget(search: string): ReminderTarget | null {
  const parameters = new URLSearchParams(search);
  if (parameters.get('tab') === 'settings') return { tab: 'settings' };
  const day = parameters.get('day');
  if (parameters.get('tab') === 'calendar' && day) {
    try {
      civil(day);
      return { tab: 'calendar', day };
    } catch {
      /* Ignore malformed civil dates rather than changing the plan. */
    }
  }
  return null;
}

export function pushKey(value: string): ArrayBuffer {
  const raw = atob(
    value.replaceAll('-', '+').replaceAll('_', '/') + '='.repeat((4 - (value.length % 4)) % 4),
  );
  if (raw.length !== 65 || raw.charCodeAt(0) !== 4) throw new Error('invalid_push_key');
  return Uint8Array.from(raw, (character) => character.charCodeAt(0)).buffer;
}

export async function subscriptionFingerprint(subscription: PushSubscription): Promise<string> {
  const digest = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(subscription.endpoint),
  );
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, '0')).join('');
}

export function subscriptionServerKey(subscription: PushSubscription): string | null {
  const key = subscription.options.applicationServerKey;
  return key
    ? btoa(String.fromCharCode(...new Uint8Array(key)))
        .replaceAll('+', '-')
        .replaceAll('/', '_')
        .replaceAll('=', '')
    : null;
}
