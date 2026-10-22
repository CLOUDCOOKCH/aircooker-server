import type { components } from '../api-schema';
export type ShoppingSnapshot = components['schemas']['ShoppingSnapshot'];
export const SHOPPING_CACHE = 'shopping:snapshot:v1';
export function parseShopping(value: unknown): ShoppingSnapshot {
  const data = value as ShoppingSnapshot;
  const states = ['not_sent', 'pending', 'synced', 'purchased', 'removed_by_user', 'manual'];
  if (
    !data ||
    typeof data.period !== 'string' ||
    !/^\d{4}-\d{2}-\d{2}$/.test(data.period) ||
    !Number.isFinite(data.calculated_at) ||
    !Number.isInteger(data.planned_meals) ||
    data.planned_meals < 0 ||
    !(data.list_name === null || typeof data.list_name === 'string') ||
    !(data.list_id === null || typeof data.list_id === 'string') ||
    !(data.last_success_at === null || Number.isFinite(data.last_success_at)) ||
    !['idle', 'queued', 'running', 'done', 'failed'].includes(data.job_state) ||
    !['idle', 'queued', 'running', 'done', 'failed'].includes(data.verification_state) ||
    !['not_configured', 'list_not_selected', 'compatibility_unverified', 'ready'].includes(
      data.connection_state,
    ) ||
    !Array.isArray(data.requirements) ||
    !Array.isArray(data.excluded_staples) ||
    !data.excluded_staples.every((x) => typeof x === 'string') ||
    !data.requirements.every(
      (x) =>
        x &&
        Number.isInteger(x.sources) &&
        x.sources >= 1 &&
        typeof x.id === 'string' &&
        typeof x.name === 'string' &&
        typeof x.spec === 'string' &&
        states.includes(x.state),
    )
  )
    throw new Error('shopping_snapshot_invalid');
  return data;
}
