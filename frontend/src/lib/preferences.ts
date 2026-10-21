import { amount, assertUUID, categories } from './domain.ts';
import type { components } from '../api-schema';
export type PlanningPreferences = Required<
  Omit<components['schemas']['PlanningPreferences-Output'], 'servings'>
> & { servings: string | null };
export type PlanningContext = Omit<components['schemas']['PlanningContext'], 'preferences'> & {
  preferences: PlanningPreferences;
};
export const DEFAULT_PLANNING: PlanningContext = {
  revision: 0,
  preferences: {
    categories: ['dinner'],
    allow_repeats: false,
    servings: null,
    use_leftovers: true,
  },
  accepted_counts: {},
};
export const PLANNING_PATH = '/api/v1/household/planning-preferences';
export function parsePreferences(value: unknown): PlanningPreferences {
  if (!value || typeof value !== 'object') throw new Error('invalid_planning_preferences');
  const raw = value as Record<string, unknown>;
  if (
    !Array.isArray(raw.categories) ||
    !raw.categories.length ||
    raw.categories.length > 3 ||
    new Set(raw.categories).size !== raw.categories.length ||
    raw.categories.some((category) => !categories.includes(category)) ||
    typeof raw.allow_repeats !== 'boolean' ||
    typeof raw.use_leftovers !== 'boolean'
  )
    throw new Error('invalid_planning_preferences');
  return {
    categories: categories.filter((category) => (raw.categories as unknown[]).includes(category)),
    allow_repeats: raw.allow_repeats,
    use_leftovers: raw.use_leftovers,
    servings: raw.servings === null ? null : amount(raw.servings, false, '100'),
  };
}
export function parsePlanningContext(value: unknown): PlanningContext {
  if (!value || typeof value !== 'object') throw new Error('invalid_planning_context');
  const raw = value as Record<string, unknown>;
  if (
    !Number.isSafeInteger(raw.revision) ||
    Number(raw.revision) < 0 ||
    !raw.accepted_counts ||
    typeof raw.accepted_counts !== 'object' ||
    Array.isArray(raw.accepted_counts) ||
    Object.keys(raw.accepted_counts).length > 10000
  )
    throw new Error('invalid_planning_context');
  const counts: Record<string, number> = {};
  for (const [id, count] of Object.entries(raw.accepted_counts)) {
    if (!Number.isInteger(count) || count < 1 || count > 1000000)
      throw new Error('invalid_planning_context');
    counts[assertUUID(id)] = count;
  }
  return {
    revision: Number(raw.revision),
    preferences: parsePreferences(raw.preferences),
    accepted_counts: counts,
  };
}

export type PreferenceDraft = {
  request_id: string;
  base_revision: number;
  preferences: PlanningPreferences;
};
/** Keep incomplete user input (including an empty portions field) while rejecting corrupt metadata. */
export function parsePreferenceDraft(value: unknown): PreferenceDraft | null {
  if (value === null) return null;
  if (!value || typeof value !== 'object') throw new Error('invalid_preference_draft');
  const raw = value as Record<string, unknown>;
  if (
    typeof raw.request_id !== 'string' ||
    !Number.isSafeInteger(raw.base_revision) ||
    Number(raw.base_revision) < 0 ||
    !raw.preferences ||
    typeof raw.preferences !== 'object'
  )
    throw new Error('invalid_preference_draft');
  const prefs = raw.preferences as Record<string, unknown>;
  if (
    !Array.isArray(prefs.categories) ||
    (prefs.servings !== null && (typeof prefs.servings !== 'string' || prefs.servings.length > 100))
  )
    throw new Error('invalid_preference_draft');
  const checked = parsePreferences({
    ...prefs,
    categories: prefs.categories.length ? prefs.categories : ['dinner'],
    servings: null,
  });
  return {
    request_id: assertUUID(raw.request_id),
    base_revision: Number(raw.base_revision),
    preferences: {
      ...checked,
      categories: prefs.categories.length ? checked.categories : [],
      servings: prefs.servings as string | null,
    },
  };
}
