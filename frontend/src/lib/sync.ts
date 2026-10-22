import type { components } from '../api-schema';
import { APIError } from './api.ts';
import type { APIClient } from './api.ts';
import { assertUUID, entityKey, payload } from './domain.ts';
import { LocalStore } from './store.ts';
import { extractionPreview } from './imports.ts';
import type { ImportTask, Queued } from './store.ts';

type Wire = components['schemas'];
type Transport = Pick<APIClient, 'request' | 'upload'>;
export type SyncProgress = { sent: number; received: number; blocked: number; hasMore: boolean };
const MAX_PAGES = 50;

/** Foreground-only by design: durable server jobs continue independently after delivery. */
export class SyncEngine {
  private readonly store: LocalStore;
  private readonly api: Transport;
  private running: Promise<SyncProgress> | null = null;
  constructor(store: LocalStore, api: Transport) {
    this.store = store;
    this.api = api;
  }

  synchronise(): Promise<SyncProgress> {
    if (this.running) return this.running;
    const work = async () => this.run();
    const pending = (async () => {
      if (typeof navigator !== 'undefined' && navigator.locks)
        return await navigator.locks.request('aircooker-sync:' + this.store.instanceID, work);
      return work();
    })();
    this.running = pending
      .then((value) => value)
      .finally(() => {
        this.running = null;
      });
    return this.running;
  }

  private async run(): Promise<SyncProgress> {
    if (await this.store.setting('demo', false)) throw new APIError('demo_server_unavailable', 0);
    const progress: SyncProgress = { sent: 0, received: 0, blocked: 0, hasMore: false };
    const anchor = await this.store.anchor();
    const state = await this.api.request<Wire['SyncState']>(
      '/api/v1/sync/state?cursor=' + anchor.cursor,
    );
    if (assertUUID(state.instance_id) !== this.store.instanceID)
      throw new APIError('server_identity_changed', 409);
    if (state.requested_cursor !== anchor.cursor || !Number.isSafeInteger(state.cursor))
      throw new APIError('invalid_server_response', 0);
    if (state.requested_token !== anchor.token || state.cursor < anchor.cursor)
      throw new APIError('sync_history_changed', 409);
    const session = await this.api.request<Wire['BrowserSession']>('/api/v1/pwa/auth/session');
    if (assertUUID(session.device_id) !== (await this.store.device()))
      throw new APIError('device_session_changed', 401);

    await this.imports();
    const queue = await this.store.pending();
    const neededPhotos = new Set(
      queue.flatMap((entry) =>
        entry.mutation.kind === 'recipe' &&
        entry.mutation.payload &&
        'image_id' in entry.mutation.payload &&
        entry.mutation.payload.image_id
          ? [entry.mutation.payload.image_id]
          : [],
      ),
    );
    const failedPhotos = new Set<string>();
    for (const photo of await this.store.photos()) {
      if (!photo.pending || !neededPhotos.has(photo.id)) continue;
      if (photo.error) {
        failedPhotos.add(photo.id);
        continue;
      }
      try {
        await this.api.upload(photo.id, photo.blob);
        await this.store.acknowledgePhoto(photo.id);
      } catch (error) {
        if (error instanceof APIError && [400, 409, 413, 415, 422, 507].includes(error.status)) {
          await this.store.failPhoto(photo.id, 'photo_upload_rejected');
          failedPhotos.add(photo.id);
        } else throw error;
      }
    }
    const blocked = new Set<string>();
    const approvals = new Set<string>();
    for (const entry of queue.slice(0, 100)) {
      const imageID =
        entry.mutation.kind === 'recipe' &&
        entry.mutation.payload &&
        'image_id' in entry.mutation.payload
          ? entry.mutation.payload.image_id
          : null;
      if (imageID && failedPhotos.has(imageID)) {
        await this.store.block(entry.mutation.mutation_id, 'photo_upload_rejected');
        entry.blocked = 'photo_upload_rejected';
      }
      if (entry.approval) {
        const group = entry.approval;
        if (approvals.has(group.request_id)) continue;
        approvals.add(group.request_id);
        if (entry.blocked) {
          progress.blocked += group.mutations.length;
          for (const mutation of group.mutations)
            blocked.add(entityKey(mutation.kind, mutation.entity_id));
          continue;
        }
        try {
          const results = await this.api.request<Wire['MutationResult'][]>(
            '/api/v1/suggestions/apply',
            { method: 'POST', body: JSON.stringify(group) },
          );
          if (
            !Array.isArray(results) ||
            results.length !== group.mutations.length ||
            results.some(
              (result, i) =>
                result.mutation_id !== group.mutations[i].mutation_id ||
                !['accepted', 'deleted'].includes(result.status) ||
                !Number.isSafeInteger(result.revision) ||
                result.revision < 1,
            )
          )
            throw new APIError('invalid_server_response', 0);
          for (const result of results) await this.store.acknowledge(result);
          progress.sent += results.length;
        } catch (error) {
          if (
            error instanceof APIError &&
            [400, 409, 422].includes(error.status) &&
            error.code !== 'sync_history_changed'
          ) {
            for (const mutation of group.mutations) {
              await this.store.block(mutation.mutation_id, error.code);
              blocked.add(entityKey(mutation.kind, mutation.entity_id));
            }
            progress.blocked += group.mutations.length;
          } else throw error;
        }
        continue;
      }
      const key = entityKey(entry.mutation.kind, entry.mutation.entity_id);
      if (entry.blocked) {
        blocked.add(key);
        progress.blocked += 1;
        continue;
      }
      if (blocked.has(key)) continue;
      try {
        const result = await this.push(entry, anchor);
        if (result.mutation_id !== entry.mutation.mutation_id)
          throw new APIError('invalid_server_response', 0);
        await this.store.acknowledge(result);
        if (result.status === 'rejected_tombstone') {
          blocked.add(key);
          progress.blocked += 1;
        } else {
          progress.sent += 1;
          if (entry.importID) {
            const task = (await this.store.imports()).find((task) => task.id === entry.importID);
            if (task) await this.store.saveImport({ ...task, state: 'confirmed' });
          }
        }
      } catch (error) {
        if (
          error instanceof APIError &&
          [400, 409, 422].includes(error.status) &&
          !['sync_history_changed', 'sync_checkpoint_required'].includes(error.code)
        ) {
          await this.store.block(entry.mutation.mutation_id, error.code);
          blocked.add(key);
          progress.blocked += 1;
        } else {
          throw error;
        }
      }
    }
    for (let page = 0; page < MAX_PAGES; page += 1) {
      const checkpoint = await this.store.anchor();
      const result = await this.api.request<Wire['Pull']>(
        `/api/v1/sync/pull?cursor=${checkpoint.cursor}&token=${checkpoint.token}&limit=100`,
      );
      if (
        !Array.isArray(result.changes) ||
        result.changes.length > 500 ||
        typeof result.has_more !== 'boolean'
      )
        throw new APIError('invalid_server_response', 0);
      if (result.has_more && result.cursor <= checkpoint.cursor)
        throw new APIError('invalid_server_response', 0);
      await this.store.merge(result.changes, { cursor: result.cursor, token: result.cursor_token });
      progress.received += result.changes.length;
      progress.hasMore = result.has_more;
      if (!result.has_more) break;
    }
    return progress;
  }

  private async push(
    entry: Queued,
    checkpoint: Wire['SyncAnchor'],
  ): Promise<Wire['MutationResult']> {
    if (entry.importID) {
      return this.api.request('/api/v1/imports/' + assertUUID(entry.importID) + '/confirm', {
        method: 'POST',
        body: JSON.stringify(entry.mutation),
        headers: {
          'X-Aircooker-Sync-Cursor': String(checkpoint.cursor),
          'X-Aircooker-Sync-Token': checkpoint.token,
        },
      });
    }
    const result = await this.api.request<Wire['MutationResult'][]>('/api/v1/sync/push', {
      method: 'POST',
      body: JSON.stringify({ mutations: [entry.mutation], checkpoint } satisfies Wire['Push']),
    });
    if (!Array.isArray(result) || result.length !== 1)
      throw new APIError('invalid_server_response', 0);
    return result[0];
  }

  private async imports(): Promise<void> {
    const active = (await this.store.imports()).filter((task) =>
      ['queued', 'processing', 'cancel_pending'].includes(task.state),
    );
    for (const task of active.slice(0, 100)) {
      const delay = (task.nextAttempt ?? 0) - Date.now();
      if (delay > 0 && delay <= 60_000) continue;
      try {
        if (task.state === 'cancel_pending') {
          try {
            await this.api.request('/api/v1/imports/' + assertUUID(task.id), { method: 'DELETE' });
          } catch (error) {
            if (!(error instanceof APIError && error.status === 404)) throw error;
          }
          await this.store.saveImport({ ...task, state: 'cancelled' });
          continue;
        }
        if (task.state === 'queued') {
          if (task.source && task.body.source_id) {
            const data = new FormData();
            data.set('file', task.source.blob, task.source.name);
            await this.api.request('/api/v1/import-sources/' + assertUUID(task.body.source_id), {
              method: 'PUT',
              body: data,
            });
          }
          if (task.body.image_id) {
            const photo = await this.store.photo(assertUUID(task.body.image_id));
            if (!photo) throw new APIError('image_not_available_locally', 422);
            if (photo.pending) {
              await this.api.upload(photo.id, photo.blob);
              await this.store.acknowledgePhoto(photo.id);
            }
          }
          const current = (await this.store.imports()).find((item) => item.id === task.id);
          if (current?.state === 'cancel_pending' || current?.state === 'cancelled') continue;
          const result = await this.api.request<{ id: string }>('/api/v1/imports', {
            method: 'POST',
            body: JSON.stringify({ ...task.body, request_id: task.id }),
          });
          if (result.id !== task.id) throw new APIError('invalid_server_response', 0);
          await this.store.saveImport({
            ...task,
            state: 'processing',
            source: undefined,
            error: undefined,
          });
        }
        const result = await this.api.request<{
          id: string;
          state: string;
          recipe?: unknown;
          warnings?: unknown;
          error_code?: string;
          extraction?: Wire['ExtractionResult'];
          source_photo?: Wire['ImportSourcePhoto'] | null;
          recognized_text?: string | null;
        }>('/api/v1/imports/' + assertUUID(task.id));
        if (
          result.id !== task.id ||
          !['queued', 'preview', 'needs_input', 'confirmed', 'cancelled'].includes(result.state)
        )
          throw new APIError('invalid_server_response', 0);
        const warnings = Array.isArray(result.warnings)
          ? result.warnings.filter((warning): warning is string => typeof warning === 'string')
          : [];
        const recipe = result.recipe
          ? payload('recipe', result.recipe)
          : result.extraction
            ? extractionPreview(result.extraction, task.body.source_url)
            : undefined;
        if (recipe && result.source_photo) {
          const photo = result.source_photo;
          if (typeof photo.source_url !== 'string' || photo.source_url.length > 2048)
            throw new APIError('invalid_server_response', 0);
          recipe.image_id = assertUUID(photo.image_id);
          recipe.provenance = {
            ...recipe.provenance,
            image_source: photo.source_url,
            image_extractor: 'source-metadata-v1',
          };
        }
        await this.store.saveImport({
          ...task,
          state: result.state === 'queued' ? 'processing' : (result.state as ImportTask['state']),
          recipe,
          extraction: result.extraction,
          source: undefined,
          warnings,
          recognizedText:
            typeof result.recognized_text === 'string'
              ? result.recognized_text.slice(0, 100000)
              : undefined,
          error: typeof result.error_code === 'string' ? result.error_code : undefined,
        });
      } catch (error) {
        if (
          error instanceof APIError &&
          (error.status === 401 || error.status === 403 || error.code === 'connection_unavailable')
        )
          throw error;
        const temporary =
          error instanceof APIError && (error.status >= 500 || error.status === 429);
        const attempts = Math.min(20, (task.attempts ?? 0) + 1);
        await this.store.saveImport({
          ...task,
          state: temporary ? task.state : 'needs_input',
          error: error instanceof APIError ? error.code : 'invalid_extracted_recipe',
          attempts,
          nextAttempt: temporary ? Date.now() + Math.min(60_000, 2000 * 2 ** attempts) : undefined,
        });
      }
    }
  }
}
