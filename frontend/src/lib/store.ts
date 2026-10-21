import { openDB } from 'idb';
import type { DBSchema, IDBPDatabase } from 'idb';
import Decimal from 'decimal.js';
import type { components } from '../api-schema';
import { assertUUID, entityKey, payload, uuid, validateChange } from './domain.ts';
import type { Change, Entity, Kind, Leftover, Meal, Mutation, Payloads } from './domain.ts';

export type Edit<K extends Kind = Kind> = {
  kind: K;
  id: string;
  value: Payloads[K];
  deleted?: boolean;
};
export type Queued = { sequence?: number; mutation: Mutation; blocked?: string; importID?: string };
export type Photo = { id: string; blob: Blob; pending: boolean };
export type ImportTask = {
  id: string;
  body: components['schemas']['ImportRequest'];
  state: 'queued' | 'processing' | 'preview' | 'needs_input' | 'confirmed' | 'cancelled';
  recipe?: Payloads['recipe'];
  warnings?: string[];
  error?: string;
  attempts?: number;
  nextAttempt?: number;
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
    assertUUID(instanceID);
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
  async saveImport(task: ImportTask): Promise<void> {
    await this.db.put('imports', task);
  }

  async saveBatch(
    edits: Edit[],
    options: { photos?: Photo[]; draft?: string; importID?: string } = {},
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
    const tx = this.db.transaction(['entities', 'outbox', 'photos', 'drafts'], 'readwrite');
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
      for (const photo of options.photos ?? []) await tx.objectStore('photos').put(photo);
      for (const { row, mutation } of changes) {
        await tx.objectStore('entities').put(row);
        await tx
          .objectStore('outbox')
          .add({ mutation, ...(options.importID ? { importID: options.importID } : {}) });
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
        } else if (!prior || prior.revision < change.revision) {
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
