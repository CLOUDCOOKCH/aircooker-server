import { openDB } from 'idb';
import type { DBSchema, IDBPDatabase } from 'idb';
import Decimal from 'decimal.js';
import { cloneRecipe } from './planning.ts';
import type { components } from '../api-schema';
import { assertUUID, entityKey, payload, uuid, validateChange } from './domain.ts';
import type { Change, Entity, Kind, Leftover, Meal, Mutation, Payloads, Recipe } from './domain.ts';

export type Edit<K extends Kind = Kind> = {
  kind: K;
  id: string;
  value: Payloads[K];
  deleted?: boolean;
};
export type Queued = {
  sequence?: number;
  mutation: Mutation;
  blocked?: string;
  importID?: string;
  approval?: components['schemas']['SuggestionApply'];
};
export type Photo = { id: string; blob: Blob; pending: boolean; error?: string };
export type ImportTask = {
  id: string;
  body: components['schemas']['ImportRequest'];
  state:
    | 'queued'
    | 'processing'
    | 'preview'
    | 'needs_input'
    | 'confirmed'
    | 'cancelled'
    | 'saving'
    | 'cancel_pending';
  recipe?: Payloads['recipe'];
  warnings?: string[];
  recognizedText?: string;
  error?: string;
  attempts?: number;
  nextAttempt?: number;
  source?: { blob: Blob; name: string };
  extraction?: components['schemas']['RecipeImportStatus']['extraction'];
};
type Anchor = components['schemas']['SyncAnchor'];
interface Schema extends DBSchema {
  entities: { key: string; value: Entity; indexes: { kind: Kind } };
  outbox: { key: number; value: Queued; indexes: { mutation: string } };
  photos: { key: string; value: Photo };
  meta: { key: string; value: unknown };
  drafts: { key: string; value: { value: unknown; photo?: Blob } };
  imports: { key: string; value: ImportTask };
  archives: {
    key: string;
    value: { created_at: string; reason: string; entities: Entity[]; outbox: Queued[] };
  };
}

function validateBookings(rows: Entity[], edited: Edit[]): void {
  const active = new Map(rows.filter((row) => !row.deleted).map((row) => [row.key, row]));
  const used = new Map<string, Decimal>();
  for (const row of active.values()) {
    if (row.kind !== 'meal') continue;
    const meal = row.payload as Meal;
    if (!meal.leftover_id) continue;
    const source = active.get(entityKey('leftover', meal.leftover_id));
    const leftover = source?.payload as Leftover | undefined;
    if (
      !leftover ||
      leftover.discarded ||
      leftover.recipe_id !== meal.recipe_id ||
      meal.date < leftover.produced_on
    )
      throw new Error('leftover_unavailable');
    const total = (used.get(source!.id) ?? new Decimal(0)).plus(meal.servings);
    if (total.gt(leftover.portions)) throw new Error('insufficient_leftovers');
    used.set(source!.id, total);
  }
  for (const edit of edited) {
    if (edit.deleted) continue;
    if (edit.kind === 'meal' || edit.kind === 'leftover') {
      const recipeID = (edit.value as Meal | Leftover).recipe_id;
      if (!active.has(entityKey('recipe', recipeID))) throw new Error('recipe_unavailable');
    }
  }
}

/** All local edits, their photos and outgoing mutations share one IndexedDB transaction. */
export class LocalStore {
  readonly instanceID: string;
  private readonly db: IDBPDatabase<Schema>;
  private constructor(instanceID: string, db: IDBPDatabase<Schema>) {
    this.instanceID = instanceID;
    this.db = db;
  }

  static async open(instanceID: string): Promise<LocalStore> {
    instanceID = assertUUID(instanceID);
    const db = await openDB<Schema>('aircooker:' + instanceID, 1, {
      upgrade(database) {
        const entities = database.createObjectStore('entities', { keyPath: 'key' });
        entities.createIndex('kind', 'kind');
        const outbox = database.createObjectStore('outbox', {
          keyPath: 'sequence',
          autoIncrement: true,
        });
        outbox.createIndex('mutation', 'mutation.mutation_id', { unique: true });
        database.createObjectStore('photos', { keyPath: 'id' });
        database.createObjectStore('meta');
        database.createObjectStore('drafts');
        database.createObjectStore('imports', { keyPath: 'id' });
        database.createObjectStore('archives');
      },
      blocking() {
        db.close();
      },
    });
    return new LocalStore(instanceID, db);
  }
  close(): void {
    this.db.close();
  }
  async setting<T>(key: string, fallback: T): Promise<T> {
    return ((await this.db.get('meta', key)) as T | undefined) ?? fallback;
  }
  async setSetting(key: string, value: unknown): Promise<void> {
    await this.db.put('meta', value, key);
  }
  async device(): Promise<string> {
    const tx = this.db.transaction('meta', 'readwrite');
    const existing = await tx.store.get('device');
    const id = typeof existing === 'string' ? assertUUID(existing) : uuid();
    if (!existing) await tx.store.put(id, 'device');
    await tx.done;
    return id;
  }
  async bindDevice(deviceID: string): Promise<void> {
    const id = assertUUID(deviceID);
    const tx = this.db.transaction(['meta', 'outbox'], 'readwrite');
    const prior = await tx.objectStore('meta').get('device');
    if (prior && prior !== id) {
      tx.abort();
      await tx.done.catch(() => undefined);
      throw new Error('device_session_changed');
    }
    await tx.objectStore('meta').put(id, 'device');
    await tx.done;
  }
  async seedDemo(edits: Edit[], photos: Photo[] = []): Promise<void> {
    if (this.instanceID !== '00000000-0000-4000-8000-000000000001')
      throw new Error('invalid_demo_store');
    const prepared = edits.map((edit) => ({
      kind: edit.kind,
      id: assertUUID(edit.id),
      value: payload(edit.kind, edit.value),
    }));
    const tx = this.db.transaction(['entities', 'photos', 'meta'], 'readwrite');
    if (await tx.objectStore('meta').get('demo')) {
      await tx.done;
      return;
    }
    if (await tx.objectStore('entities').count()) {
      tx.abort();
      await tx.done.catch(() => undefined);
      throw new Error('demo_not_empty');
    }
    for (const edit of prepared)
      await tx.objectStore('entities').put({
        key: entityKey(edit.kind, edit.id),
        kind: edit.kind,
        id: edit.id,
        payload: edit.value,
        deleted: false,
        revision: 0,
      });
    for (const photo of photos) await tx.objectStore('photos').put(photo);
    await tx.objectStore('meta').put(true, 'demo');
    await tx.done;
  }
  async localExport(): Promise<unknown> {
    const tx = this.db.transaction(
      ['entities', 'outbox', 'drafts', 'imports', 'archives', 'meta', 'photos'],
      'readonly',
    );
    const draftKeys = await tx.objectStore('drafts').getAllKeys();
    const draftValues = await tx.objectStore('drafts').getAll();
    const photos = await tx.objectStore('photos').getAll();
    const result = {
      format: 'aircooker-browser-recovery',
      version: 1,
      instance_id: this.instanceID,
      entities: await tx.objectStore('entities').getAll(),
      outbox: await tx.objectStore('outbox').getAll(),
      drafts: draftKeys.map((key, i) => ({ key, value: draftValues[i].value })),
      imports: await tx.objectStore('imports').getAll(),
      archives: await tx.objectStore('archives').getAll(),
      anchor: await tx.objectStore('meta').get('anchor'),
      settings_drafts: {
        planning: await tx.objectStore('meta').get('planning:preferences-draft'),
        reminders: await tx.objectStore('meta').get('push:preferences-draft'),
      },
    };
    await tx.done;
    const draftPhotos = draftValues.flatMap((draft, i) =>
      draft.photo ? [{ id: String(draftKeys[i]), blob: draft.photo, draft: true }] : [],
    );
    const media = [
      ...photos.map((photo) => ({ id: photo.id, blob: photo.blob, draft: false })),
      ...draftPhotos,
      ...result.imports.flatMap((task) =>
        task.source ? [{ id: task.id, blob: task.source.blob, draft: false, source: true }] : [],
      ),
    ];
    if (media.reduce((total, photo) => total + photo.blob.size, 0) > 100 * 1024 * 1024)
      throw new Error('export_too_large');
    const encoded = [];
    for (const photo of media) {
      const bytes = new Uint8Array(await photo.blob.arrayBuffer());
      let binary = '';
      for (let offset = 0; offset < bytes.length; offset += 32768)
        binary += String.fromCharCode(...bytes.subarray(offset, offset + 32768));
      encoded.push({
        id: photo.id,
        draft: photo.draft,
        content_type: photo.blob.type,
        base64: btoa(binary),
        source: 'source' in photo && photo.source === true,
      });
    }
    return {
      ...result,
      imports: result.imports.map(({ source, ...task }) => ({
        ...task,
        ...(source ? { source: { name: source.name, media_id: task.id } } : {}),
      })),
      media: encoded,
    };
  }
  async archives() {
    const tx = this.db.transaction('archives', 'readonly');
    const keys = await tx.store.getAllKeys(),
      values = await tx.store.getAll();
    await tx.done;
    return keys.map((id, i) => ({ id, ...values[i] }));
  }
  /** Explicit recovery only. Preserve the previous records/queue before adopting server history. */
  async replaceSnapshot(changes: Change[], anchor: Anchor): Promise<void> {
    changes.forEach(validateChange);
    if (
      changes.some((row) => row.revision > anchor.cursor) ||
      new Set(changes.map((row) => entityKey(row.kind, row.entity_id))).size !== changes.length ||
      !Number.isSafeInteger(anchor.cursor) ||
      anchor.cursor < 0 ||
      !(anchor.cursor === 0 ? anchor.token === 'root' : /^[a-f\d]{32}$/.test(anchor.token))
    )
      throw new Error('invalid_server_response');
    const tx = this.db.transaction(
      ['entities', 'outbox', 'meta', 'archives', 'imports'],
      'readwrite',
    );
    try {
      const entities = await tx.objectStore('entities').getAll(),
        outbox = await tx.objectStore('outbox').getAll();
      await tx.objectStore('archives').put(
        {
          created_at: new Date().toISOString(),
          reason: 'server_history_recovery',
          entities,
          outbox,
        },
        uuid(),
      );
      await tx.objectStore('entities').clear();
      await tx.objectStore('outbox').clear();
      for (const change of changes)
        await tx.objectStore('entities').put({
          key: entityKey(change.kind, change.entity_id),
          id: change.entity_id,
          kind: change.kind,
          revision: change.revision,
          deleted: change.deleted,
          payload: change.deleted
            ? (change.payload as Payloads[Kind])
            : payload(change.kind, change.payload),
        });
      for (const task of await tx.objectStore('imports').getAll())
        if (task.state === 'saving')
          await tx
            .objectStore('imports')
            .put({ ...task, state: 'needs_input', error: 'archived_after_server_restore' });
      await tx.objectStore('meta').put(anchor, 'anchor');
      await tx.done;
    } catch (error) {
      try {
        tx.abort();
      } catch {
        /* already aborted */
      }
      await tx.done.catch(() => undefined);
      throw error;
    }
  }
  async resolveRejected(id: string, copy: boolean): Promise<void> {
    const key = entityKey('recipe', id);
    const tx = this.db.transaction(['entities', 'outbox', 'archives'], 'readwrite');
    try {
      const row = await tx.objectStore('entities').get(key);
      if (!row) throw new Error('recipe_unavailable');
      const pending = (await tx.objectStore('outbox').getAll()).filter(
        (entry) => entry.mutation.kind === 'recipe' && entry.mutation.entity_id === id,
      );
      if (!pending.some((entry) => entry.blocked)) throw new Error('no_rejected_changes');
      await tx.objectStore('archives').put(
        {
          created_at: new Date().toISOString(),
          reason: 'rejected_recipe',
          entities: [row],
          outbox: pending,
        },
        uuid(),
      );
      for (const entry of pending) await tx.objectStore('outbox').delete(entry.sequence!);
      if (copy) {
        const newID = uuid(),
          mutationID = uuid();
        const value = cloneRecipe(payload('recipe', row.payload));
        await tx.objectStore('entities').put({
          key: entityKey('recipe', newID),
          id: newID,
          kind: 'recipe',
          revision: 0,
          deleted: false,
          payload: value,
          lastMutation: mutationID,
        });
        await tx.objectStore('outbox').add({
          mutation: {
            ...pending[pending.length - 1].mutation,
            entity_id: newID,
            mutation_id: mutationID,
            idempotency_key: mutationID,
            base_revision: 0,
            operation: 'upsert',
            payload: value,
            client_timestamp: new Date().toISOString(),
          },
        });
      }
      const shadow = row.serverShadow;
      if (shadow)
        await tx.objectStore('entities').put({
          key,
          id,
          kind: 'recipe',
          revision: shadow.revision,
          deleted: shadow.deleted,
          payload: shadow.payload as Recipe,
        });
      else await tx.objectStore('entities').put({ ...row, deleted: true, lastMutation: undefined });
      await tx.done;
    } catch (error) {
      try {
        tx.abort();
      } catch {
        /* already aborted */
      }
      await tx.done.catch(() => undefined);
      throw error;
    }
  }
  async entities<K extends Kind>(kind: K): Promise<Entity<K>[]> {
    return (await this.db.getAllFromIndex('entities', 'kind', kind)).filter(
      (row) => !row.deleted,
    ) as Entity<K>[];
  }
  async all(): Promise<Entity[]> {
    return this.db.getAll('entities');
  }
  async pending(): Promise<Queued[]> {
    return this.db.getAll('outbox');
  }
  async anchor(): Promise<Anchor> {
    return this.setting('anchor', { cursor: 0, token: 'root' });
  }
  async photos(): Promise<Photo[]> {
    return this.db.getAll('photos');
  }
  async photo(id: string): Promise<Photo | undefined> {
    return this.db.get('photos', id);
  }
  async cachePhoto(photo: Photo): Promise<void> {
    const tx = this.db.transaction('photos', 'readwrite');
    const prior = await tx.store.get(photo.id);
    if (!prior?.pending) await tx.store.put(photo);
    await tx.done;
  }
  async acknowledgePhoto(id: string): Promise<void> {
    const tx = this.db.transaction('photos', 'readwrite');
    const photo = await tx.store.get(id);
    if (photo) await tx.store.put({ ...photo, pending: false });
    await tx.done;
  }
  async failPhoto(id: string, reason: string): Promise<void> {
    const tx = this.db.transaction('photos', 'readwrite');
    const photo = await tx.store.get(id);
    if (photo) await tx.store.put({ ...photo, error: reason });
    await tx.done;
  }
  async retryPhotos(): Promise<void> {
    const tx = this.db.transaction(['photos', 'outbox'], 'readwrite');
    for (const photo of await tx.objectStore('photos').getAll())
      if (photo.error) await tx.objectStore('photos').put({ ...photo, error: undefined });
    for (const entry of await tx.objectStore('outbox').getAll())
      if (entry.blocked === 'photo_upload_rejected')
        await tx.objectStore('outbox').put({ ...entry, blocked: undefined });
    await tx.done;
  }
  async draft(key: string): Promise<{ value: unknown; photo?: Blob } | undefined> {
    return this.db.get('drafts', key);
  }
  async saveDraft(key: string, value: unknown, photo?: Blob): Promise<void> {
    await this.db.put('drafts', { value, photo }, key);
  }
  async discardDraft(key: string): Promise<void> {
    await this.db.delete('drafts', key);
  }
  async imports(): Promise<ImportTask[]> {
    return this.db.getAll('imports');
  }
  async saveImport(task: ImportTask, photo?: Photo): Promise<void> {
    if (photo && photo.id !== task.body.image_id) throw new Error('invalid_import_photo');
    const tx = this.db.transaction(['imports', 'photos'], 'readwrite');
    const prior = await tx.objectStore('imports').get(task.id);
    // An in-flight poll or upload must never undo a cancellation/confirmation.
    if (
      prior &&
      ((['cancelled', 'confirmed'].includes(prior.state) && task.state !== prior.state) ||
        (prior.state === 'cancel_pending' && !['cancel_pending', 'cancelled'].includes(task.state)))
    ) {
      await tx.done;
      return;
    }
    if (photo) {
      if (!(await tx.objectStore('photos').get(photo.id)))
        await tx.objectStore('photos').put(photo);
    }
    await tx.objectStore('imports').put(task);
    await tx.done;
  }

  async saveBatch(
    edits: Edit[],
    options: {
      photos?: Photo[];
      draft?: string;
      importID?: string;
      suggestion?: { request_id: string; monday: string; basis: string | null };
    } = {},
  ): Promise<void> {
    if (!edits.length || edits.length > 100) throw new Error('invalid_batch');
    const device = await this.device();
    const normal = edits.map((edit) => ({
      ...edit,
      id: assertUUID(edit.id),
      value: payload(edit.kind, edit.value),
    }));
    if (new Set(normal.map((edit) => entityKey(edit.kind, edit.id))).size !== normal.length)
      throw new Error('duplicate_edit');
    const tx = this.db.transaction(
      ['entities', 'outbox', 'photos', 'drafts', 'imports', 'meta'],
      'readwrite',
    );
    try {
      const rows = new Map(
        (await tx.objectStore('entities').getAll()).map((row) => [row.key, row]),
      );
      const changes: { row: Entity; mutation: Mutation }[] = [];
      for (const edit of normal) {
        const key = entityKey(edit.kind, edit.id);
        const prior = rows.get(key);
        if (prior?.deleted && !edit.deleted) throw new Error('deleted_identity');
        const id = uuid();
        const row: Entity = {
          key,
          kind: edit.kind,
          id: edit.id,
          revision: prior?.revision ?? 0,
          deleted: edit.deleted ?? false,
          payload: edit.value,
          lastMutation: id,
          serverShadow:
            prior?.serverShadow ??
            (prior && prior.revision > 0 && !prior.lastMutation
              ? {
                  kind: prior.kind,
                  entity_id: prior.id,
                  revision: prior.revision,
                  deleted: prior.deleted,
                  payload: prior.payload,
                }
              : undefined),
        };
        rows.set(key, row);
        const mutation: Mutation = {
          mutation_id: id,
          idempotency_key: id,
          device_id: device,
          entity_id: edit.id,
          kind: edit.kind,
          operation: edit.deleted ? 'delete' : 'upsert',
          base_revision: prior?.revision ?? 0,
          client_timestamp: new Date().toISOString(),
          payload: edit.value,
        };
        changes.push({ row, mutation });
      }
      validateBookings([...rows.values()], normal);
      if (options.importID) {
        const task = await tx.objectStore('imports').get(options.importID);
        if (!task || !['preview', 'needs_input'].includes(task.state))
          throw new Error('import_not_reviewable');
        await tx.objectStore('imports').put({ ...task, state: 'saving' });
      }
      for (const photo of options.photos ?? []) await tx.objectStore('photos').put(photo);
      const approval = options.suggestion
        ? {
            ...options.suggestion,
            checkpoint: ((await tx.objectStore('meta').get('anchor')) as Anchor | undefined) ?? {
              cursor: 0,
              token: 'root',
            },
            mutations: changes.map((change) => change.mutation),
          }
        : undefined;
      if (
        approval &&
        (changes.length > 21 ||
          normal.some(
            (edit) =>
              edit.kind !== 'meal' ||
              edit.deleted ||
              rows.get(entityKey(edit.kind, edit.id))?.revision !== 0,
          ))
      )
        throw new Error('invalid_suggestions');
      for (const { row, mutation } of changes) {
        await tx.objectStore('entities').put(row);
        await tx.objectStore('outbox').add({
          mutation,
          ...(options.importID ? { importID: options.importID } : {}),
          ...(approval ? { approval } : {}),
        });
      }
      if (options.draft) await tx.objectStore('drafts').delete(options.draft);
      await tx.done;
    } catch (error) {
      try {
        tx.abort();
      } catch {
        /* already aborted */
      }
      await tx.done.catch(() => undefined);
      throw error;
    }
  }

  async archiveSuggestion(requestID: string): Promise<void> {
    const tx = this.db.transaction(['entities', 'outbox', 'archives'], 'readwrite');
    try {
      const queue = await tx.objectStore('outbox').getAll();
      const group = queue.find(
        (entry) => entry.approval?.request_id === requestID && entry.blocked,
      )?.approval;
      if (!group) throw new Error('no_rejected_changes');
      const ids = new Set(group.mutations.map((mutation) => mutation.entity_id));
      const rows = (await tx.objectStore('entities').getAll()).filter(
        (row) => row.kind === 'meal' && ids.has(row.id),
      );
      const pending = queue.filter(
        (entry) => entry.mutation.kind === 'meal' && ids.has(entry.mutation.entity_id),
      );
      await tx.objectStore('archives').put(
        {
          created_at: new Date().toISOString(),
          reason: 'rejected_suggestion',
          entities: rows,
          outbox: pending,
        },
        uuid(),
      );
      for (const entry of pending) await tx.objectStore('outbox').delete(entry.sequence!);
      for (const row of rows) {
        if (row.serverShadow)
          await tx.objectStore('entities').put({
            ...row,
            revision: row.serverShadow.revision,
            deleted: row.serverShadow.deleted,
            payload: row.serverShadow.payload as Meal,
            lastMutation: undefined,
            serverShadow: undefined,
          });
        else await tx.objectStore('entities').delete(row.key);
      }
      await tx.done;
    } catch (error) {
      try {
        tx.abort();
      } catch {
        /* already aborted */
      }
      await tx.done.catch(() => undefined);
      throw error;
    }
  }
  async acknowledge(result: components['schemas']['MutationResult']): Promise<void> {
    if (
      !['accepted', 'deleted', 'rejected_tombstone'].includes(result.status) ||
      !Number.isSafeInteger(result.revision) ||
      result.revision < 0
    )
      throw new Error('invalid_server_response');
    const tx = this.db.transaction(['entities', 'outbox'], 'readwrite');
    const sequence = await tx.objectStore('outbox').index('mutation').getKey(result.mutation_id);
    if (sequence === undefined) {
      await tx.done;
      return;
    }
    const queued = await tx.objectStore('outbox').get(sequence);
    if (!queued) throw new Error('invalid_local_queue');
    if (result.status === 'rejected_tombstone') {
      await tx.objectStore('outbox').put({ ...queued, blocked: 'rejected_tombstone' });
    } else {
      await tx.objectStore('outbox').delete(sequence);
      const key = entityKey(queued.mutation.kind, queued.mutation.entity_id);
      const row = await tx.objectStore('entities').get(key);
      if (row)
        await tx.objectStore('entities').put({
          ...row,
          revision: Math.max(row.revision, result.revision),
          ...(row.lastMutation === result.mutation_id ? { lastMutation: undefined } : {}),
        });
    }
    await tx.done;
  }
  async block(id: string, reason: string): Promise<void> {
    const tx = this.db.transaction('outbox', 'readwrite');
    const queued = await tx.store.index('mutation').get(id);
    if (queued) await tx.store.put({ ...queued, blocked: reason });
    await tx.done;
  }

  async merge(changes: Change[], anchor: Anchor): Promise<void> {
    if (
      !Number.isSafeInteger(anchor.cursor) ||
      anchor.cursor < 0 ||
      !(anchor.cursor === 0 ? anchor.token === 'root' : /^[a-f\d]{32}$/.test(anchor.token))
    )
      throw new Error('invalid_server_response');
    changes.forEach(validateChange);
    if (changes.some((change) => change.revision > anchor.cursor))
      throw new Error('invalid_server_response');
    const tx = this.db.transaction(['entities', 'outbox', 'meta'], 'readwrite');
    try {
      const previous = (await tx.objectStore('meta').get('anchor')) as Anchor | undefined;
      if (previous && previous.cursor > anchor.cursor) throw new Error('stale_sync_page');
      const pending = new Set(
        (await tx.objectStore('outbox').getAll()).map((row) =>
          entityKey(row.mutation.kind, row.mutation.entity_id),
        ),
      );
      for (const change of changes) {
        const id = assertUUID(change.entity_id);
        const key = entityKey(change.kind, id);
        const prior = await tx.objectStore('entities').get(key);
        if (pending.has(key)) {
          if (prior && (!prior.serverShadow || prior.serverShadow.revision < change.revision))
            await tx.objectStore('entities').put({ ...prior, serverShadow: change });
        } else if (!prior || prior.revision <= change.revision) {
          const value = change.deleted
            ? (change.payload as Payloads[Kind])
            : payload(change.kind, change.payload);
          await tx.objectStore('entities').put({
            key,
            id,
            kind: change.kind,
            revision: change.revision,
            deleted: change.deleted,
            payload: value,
          });
        }
      }
      await tx.objectStore('meta').put(anchor, 'anchor');
      await tx.done;
    } catch (error) {
      try {
        tx.abort();
      } catch {
        /* already aborted */
      }
      await tx.done.catch(() => undefined);
      throw error;
    }
  }
}
