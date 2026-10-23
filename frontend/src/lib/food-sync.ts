import { APIError } from './api.ts';
import type { APIClient } from './api.ts';
import type { LocalStore } from './store.ts';
import { FOOD_PATH, parseFoodContext } from './food.ts';
import type { components } from '../api-schema';

/** Entity sync and history/session validation run first; this durable queue cannot starve recipes. */
export async function syncFood(store: LocalStore, api: Pick<APIClient, 'request'>): Promise<void> {
  const work = async () => {
    for (let count = 0; count < 50; count++) {
      const state = await store.foodState();
      const next = state.queue[0];
      if (!next) break;
      const receipt = await api.request<components['schemas']['FoodProfileReceipt']>(FOOD_PATH, {
        method: 'PUT',
        body: JSON.stringify(next),
      });
      if (
        receipt.request_id !== next.request_id ||
        !Number.isSafeInteger(receipt.revision) ||
        receipt.revision < 1 ||
        typeof receipt.conflict !== 'boolean'
      )
        throw new APIError('invalid_server_response', 0);
      const context = parseFoodContext(await api.request(FOOD_PATH));
      if (context.revision < receipt.revision) throw new APIError('invalid_server_response', 0);
      await store.acceptFood(context, next.request_id);
    }
    await store.acceptFood(parseFoodContext(await api.request(FOOD_PATH)));
  };
  if (typeof navigator !== 'undefined' && navigator.locks)
    await navigator.locks.request(store.syncLock, work);
  else await work();
}
