import catalog from '../../../src/mealf/food_catalog.json' with { type: 'json' };
import { assertUUID, uuid } from './domain.ts';

export const FOOD_PATH = '/api/v1/household/food-profile';
export const FOOD_STATE = 'food:state:v1';
export const FOODS = catalog.items;
export const TASTE_FOODS = FOODS.filter((item) => item.taste);
export const PANTRY_FOODS = FOODS.filter((item) => item.pantry_group !== null);
export type FoodProfile = {
  likes: string[];
  dislikes: string[];
  pantry_setup_done: boolean;
  taste_setup_done: boolean;
};
export type FoodPatch = Partial<FoodProfile>;
export type FoodContext = { revision: number; profile: FoodProfile };
export type FoodWrite = { request_id: string; base_revision: number; patch: FoodPatch };
export type FoodState = { context: FoodContext | null; queue: FoodWrite[] };
export const EMPTY_FOOD: FoodState = { context: null, queue: [] };
export const DEFAULT_FOOD: FoodProfile = {
  likes: [],
  dislikes: [],
  pantry_setup_done: false,
  taste_setup_done: false,
};
const keys = Object.keys(DEFAULT_FOOD);
const isRevision = (value: unknown): value is number =>
  Number.isSafeInteger(value) && Number(value) >= 0;
export function parseFoodPatch(value: unknown): FoodPatch {
  if (!value || typeof value !== 'object' || Array.isArray(value))
    throw Error('invalid_food_profile');
  const raw = value as Record<string, unknown>;
  if (!Object.keys(raw).length || Object.keys(raw).some((key) => !keys.includes(key)))
    throw Error('invalid_food_profile');
  const result: FoodPatch = {};
  for (const key of ['likes', 'dislikes'] as const) {
    if (!Object.hasOwn(raw, key)) continue;
    const choices = raw[key];
    if (
      !Array.isArray(choices) ||
      choices.length > 12 ||
      new Set(choices).size !== choices.length ||
      choices.some((id) => !TASTE_FOODS.some((food) => food.id === id))
    )
      throw Error('invalid_food_profile');
    result[key] = [...choices].sort();
  }
  for (const key of ['pantry_setup_done', 'taste_setup_done'] as const) {
    if (!Object.hasOwn(raw, key)) continue;
    if (typeof raw[key] !== 'boolean') throw Error('invalid_food_profile');
    result[key] = raw[key];
  }
  if (result.likes?.some((id) => result.dislikes?.includes(id)))
    throw Error('invalid_food_profile');
  return result;
}
export function parseFoodProfile(value: unknown): FoodProfile {
  const patch = parseFoodPatch(value);
  if (keys.some((key) => !Object.hasOwn(patch, key))) throw Error('invalid_food_profile');
  return patch as FoodProfile;
}
export function parseFoodContext(value: unknown): FoodContext {
  if (!value || typeof value !== 'object') throw Error('invalid_food_profile');
  const raw = value as FoodContext;
  if (!isRevision(raw.revision)) throw Error('invalid_food_profile');
  return { revision: raw.revision, profile: parseFoodProfile(raw.profile) };
}
export function parseFoodState(value: unknown): FoodState {
  if (!value || typeof value !== 'object') throw Error('invalid_food_profile');
  const raw = value as FoodState;
  if (!Array.isArray(raw.queue) || raw.queue.length > 100) throw Error('invalid_food_profile');
  const result = {
    context: raw.context === null ? null : parseFoodContext(raw.context),
    queue: raw.queue.map((write) => {
      if (!write || !isRevision(write.base_revision)) throw Error('invalid_food_profile');
      return {
        request_id: assertUUID(write.request_id),
        base_revision: write.base_revision,
        patch: parseFoodPatch(write.patch),
      };
    }),
  };
  foodProfile(result);
  return result;
}
export function foodProfile(state: FoodState): FoodProfile {
  return state.queue.reduce(
    (profile, row) => parseFoodProfile({ ...profile, ...row.patch }),
    state.context?.profile ?? DEFAULT_FOOD,
  );
}
export function queueFood(state: FoodState, patch: FoodPatch, local = false): FoodState {
  if (state.queue.length >= 100) throw Error('food_queue_full');
  const result = {
    ...state,
    queue: [
      ...state.queue,
      {
        request_id: uuid(),
        base_revision: state.context?.revision ?? 0,
        patch: parseFoodPatch(patch),
      },
    ],
  };
  const profile = foodProfile(result);
  if (local)
    return { context: { revision: (state.context?.revision ?? 0) + 1, profile }, queue: [] };
  return result;
}
export function pantryKey(name: string): string {
  const key = name.normalize('NFKC').toLocaleLowerCase('en').trim().replace(/\s+/g, ' ');
  const food = PANTRY_FOODS.find((row) =>
    [...row.aliases, ...Object.values(row.name)].some(
      (alias) =>
        alias.normalize('NFKC').toLocaleLowerCase('en').trim().replace(/\s+/g, ' ') === key,
    ),
  );
  return food ? 'catalog:' + food.id : 'name:' + key;
}
