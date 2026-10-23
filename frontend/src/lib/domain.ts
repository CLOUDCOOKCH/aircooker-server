import Decimal from 'decimal.js';
import type { components } from '../api-schema';

type Wire = components['schemas'];
export type Kind = Wire['Mutation']['kind'];
export type Ingredient = Omit<Wire['Ingredient-Input'], 'quantity' | 'quantity_max'> & {
  quantity: string | null;
  quantity_max: string | null;
};
export type Recipe = Omit<
  Wire['Recipe-Input'],
  'ingredients' | 'steps' | 'servings' | 'provenance'
> & {
  ingredients: Ingredient[];
  steps: string[];
  servings: string;
  provenance: Record<string, string>;
};
export type Meal = Omit<Wire['Meal'], 'servings'> & { servings: string };
export type Pantry = Wire['Pantry'];
export type Leftover = Omit<Wire['Leftover'], 'portions'> & { portions: string };
export type Template = Omit<Wire['Template'], 'meals'> & {
  meals: (Omit<Wire['TemplateSlot'], 'servings'> & { servings: string })[];
};
export type Payloads = {
  recipe: Recipe;
  meal: Meal;
  pantry: Pantry;
  leftover: Leftover;
  template: Template;
};
export type Entity<K extends Kind = Kind> = {
  key: string;
  kind: K;
  id: string;
  revision: number;
  deleted: boolean;
  payload: Payloads[K];
  lastMutation?: string;
  serverShadow?: Omit<Wire['Change'], 'updated_at'> & { updated_at?: string };
};
export type Mutation = Wire['Mutation'];
export type Change = Wire['Change'];
export const kinds: Kind[] = ['recipe', 'meal', 'pantry', 'leftover', 'template'];
export const categories = ['breakfast', 'lunch', 'dinner'] as const;
export type Category = (typeof categories)[number];
export const entityKey = (kind: Kind, id: string) => kind + ':' + id.toLowerCase();
export const uuid = () => crypto.randomUUID();
export function assertUUID(value: string): string {
  if (!/^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i.test(value))
    throw new Error('invalid_identity');
  return value.toLowerCase();
}
export function amount(value: unknown, zero = false, maximum = '1000000'): string {
  if (typeof value !== 'string' && typeof value !== 'number') throw new Error('invalid_quantity');
  const input = String(value);
  if (input.length > 100 || !/^\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(input))
    throw new Error('invalid_quantity');
  const number = new Decimal(input);
  if (
    !number.isFinite() ||
    number.lt(0) ||
    (!zero && number.eq(0)) ||
    (number.eq(0) && /[1-9]/.test(input.split(/[eE]/)[0])) ||
    number.gt(maximum)
  )
    throw new Error('invalid_quantity');
  return fixedAmount(number, 100);
}
/** Check the rendered size before allocating; calculated serving/unit results get extra room. */
export function fixedAmount(value: Decimal, maximum = 512): string {
  const places = value.decimalPlaces();
  const length =
    (value.isNegative() ? 1 : 0) + Math.max(1, value.e + 1) + (places ? places + 1 : 0);
  if (!value.isFinite() || length > maximum) throw new Error('invalid_quantity');
  return value.toFixed();
}
export function emptyRecipe(): Recipe {
  return {
    schema_version: '1.0.0',
    title: '',
    description: '',
    servings: '2',
    ingredients: [],
    steps: [],
    notes: '',
    source_url: null,
    source_platform: 'manual',
    image_id: null,
    rating: null,
    nutrition: null,
    nutrition_source: null,
    provenance: {},
  };
}
export function emptyIngredient(): Ingredient {
  return {
    id: uuid(),
    name: '',
    quantity: null,
    quantity_max: null,
    unit: '',
    preparation: '',
    original_text: '',
    quantity_text: '',
    notes: '',
    optional: false,
  };
}
export function civil(value: string): Date {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith('0000'))
    throw new Error('invalid_date');
  const date = new Date(value + 'T12:00:00Z');
  if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== value)
    throw new Error('invalid_date');
  return date;
}
export function addDays(value: string, days: number): string {
  const date = civil(value);
  date.setUTCDate(date.getUTCDate() + days);
  const result = date.toISOString().slice(0, 10);
  civil(result);
  return result;
}
export const distance = (from: string, to: string) =>
  (civil(to).getTime() - civil(from).getTime()) / 86400000;
export const monday = (day: string) => addDays(day, -((civil(day).getUTCDay() + 6) % 7));
export function today(timeZone: string, now = new Date()): string {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(now);
  const part = (type: string) => parts.find((value) => value.type === type)?.value ?? '';
  return `${part('year')}-${part('month')}-${part('day')}`;
}
export function displayDate(
  day: string,
  locale: string,
  options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'long' },
): string {
  return new Intl.DateTimeFormat(locale, { ...options, timeZone: 'UTC' }).format(civil(day));
}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value))
    throw new Error('invalid_payload');
  return value as Record<string, unknown>;
}
function text(value: unknown, maximum: number, fallback?: string): string {
  const string = value === undefined && fallback !== undefined ? fallback : value;
  if (typeof string !== 'string' || string.length > maximum) throw new Error('invalid_payload');
  return string.trim();
}
function required(value: unknown, maximum: number): string {
  const string = text(value, maximum);
  if (!string) throw new Error('invalid_payload');
  return string;
}
function list(value: unknown, maximum: number): unknown[] {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.length > maximum) throw new Error('invalid_payload');
  return value;
}
function optionalText(value: unknown, maximum: number): string | null {
  return value == null ? null : text(value, maximum);
}
function dictionary(value: unknown, maximum: number): Record<string, string> {
  if (value === undefined) return {};
  const record = object(value);
  if (Object.keys(record).length > maximum) throw new Error('invalid_payload');
  return Object.fromEntries(Object.entries(record).map(([key, item]) => [key, text(item, 10_000)]));
}

function minutes(value: unknown): number | null {
  if (value == null) return null;
  if (!Number.isInteger(value) || Number(value) < 0 || Number(value) > 525600)
    throw new Error('invalid_duration');
  return Number(value);
}

function stepDetail(value: unknown): NonNullable<Recipe['instruction_details']>[number] {
  const row = object(value);
  const temperature = row.temperature == null ? null : object(row.temperature);
  if (
    temperature &&
    (typeof temperature.value !== 'number' ||
      !Number.isFinite(temperature.value) ||
      temperature.value < -273.15 ||
      temperature.value > 2000 ||
      !['C', 'F'].includes(String(temperature.unit)))
  )
    throw new Error('invalid_temperature');
  return {
    group: optionalText(row.group, 5000),
    durationMinutes: minutes(row.durationMinutes ?? row.duration_minutes),
    temperature: temperature
      ? { value: Number(temperature.value), unit: temperature.unit as 'C' | 'F' }
      : null,
  };
}

/** Validate/normalise complete snapshots before persistence; server validation remains authoritative. */
export function payload<K extends Kind>(kind: K, value: unknown): Payloads[K] {
  const row = object(value);
  let result: Payloads[Kind];
  if (kind === 'recipe') {
    const ingredients = list(row.ingredients, 300).map((value) => {
      const item = object(value);
      const lower = item.quantity == null ? null : amount(item.quantity, true);
      const upper = item.quantity_max == null ? null : amount(item.quantity_max, true);
      if (upper !== null && (lower === null || new Decimal(upper).lt(lower)))
        throw new Error('invalid_quantity');
      return {
        id: assertUUID(text(item.id, 36)),
        name: required(item.name, 200),
        quantity: lower,
        quantity_max: upper,
        unit: text(item.unit, 30, ''),
        preparation: text(item.preparation, 300, ''),
        original_text: text(item.original_text, 500, ''),
        quantity_text: text(item.quantity_text, 500, ''),
        notes: text(item.notes, 5000, ''),
        optional:
          item.optional === undefined
            ? false
            : typeof item.optional === 'boolean'
              ? item.optional
              : (() => {
                  throw new Error('invalid_payload');
                })(),
        group: optionalText(item.group, 5000),
      };
    });
    if (new Set(ingredients.map((item) => item.id)).size !== ingredients.length)
      throw new Error('duplicate_ingredient');
    if (
      row.rating != null &&
      (!Number.isInteger(row.rating) || Number(row.rating) < 1 || Number(row.rating) > 5)
    )
      throw new Error('invalid_rating');
    result = {
      title: required(row.title, 200),
      description: text(row.description, 5000, ''),
      servings: amount(row.servings ?? '2'),
      ingredients,
      steps: list(row.steps, 200).map((value) => required(value, 5000)),
      notes: text(row.notes, 10000, ''),
      source_url: optionalText(row.source_url, 2048),
      source_platform: text(row.source_platform, 50, 'manual'),
      image_id: row.image_id == null ? null : assertUUID(text(row.image_id, 36)),
      nutrition: row.nutrition == null ? null : dictionary(row.nutrition, 100),
      nutrition_source: optionalText(row.nutrition_source, 2048),
      rating: row.rating == null ? null : Number(row.rating),
      provenance: dictionary(row.provenance, 50),
      schema_version: '1.0.0',
      times:
        row.times == null
          ? {}
          : (() => {
              const value = object(row.times);
              return {
                prepMinutes: minutes(value.prepMinutes ?? value.prep_minutes),
                cookMinutes: minutes(value.cookMinutes ?? value.cook_minutes),
                totalMinutes: minutes(value.totalMinutes ?? value.total_minutes),
              };
            })(),
      language: optionalText(row.language, 50),
      category: optionalText(row.category, 5000),
      cuisine: optionalText(row.cuisine, 5000),
      tags: list(row.tags, 50).map((tag) => required(tag, 100)),
      yield_info:
        row.yield_info == null
          ? null
          : (() => {
              const value = object(row.yield_info);
              return {
                quantity: value.quantity == null ? null : Number(amount(value.quantity)),
                unit: optionalText(value.unit, 100),
                rawText: optionalText(value.rawText ?? value.raw_text, 5000),
              };
            })(),
      instruction_details: list(row.instruction_details, 200).map(stepDetail),
    };
    if (row.schema_version !== undefined && row.schema_version !== '1.0.0')
      throw new Error('invalid_schema_version');
  } else if (kind === 'meal') {
    const date = text(row.date, 10);
    civil(date);
    const category = text(row.category, 20) as Category;
    if (
      !categories.includes(category) ||
      (row.cooked !== undefined && typeof row.cooked !== 'boolean')
    )
      throw new Error('invalid_meal');
    const order = row.order ?? 0;
    if (!Number.isInteger(order) || Number(order) < 0 || Number(order) > 100)
      throw new Error('invalid_meal');
    const recurrence = row.recurrence == null ? null : object(row.recurrence);
    let rule: Meal['recurrence'] = null;
    if (recurrence) {
      const until = text(recurrence.until, 10);
      civil(until);
      const interval = recurrence.interval_weeks ?? 1;
      if (
        !Number.isInteger(interval) ||
        Number(interval) < 1 ||
        Number(interval) > 52 ||
        distance(date, until) < 0 ||
        distance(date, until) > 3660 ||
        row.leftover_id
      )
        throw new Error('invalid_recurrence');
      const exceptions = list(recurrence.exceptions, 520).map((value) => {
        const day = text(value, 10);
        civil(day);
        return day;
      });
      rule = { interval_weeks: Number(interval), until, exceptions };
    }
    result = {
      recipe_id: assertUUID(text(row.recipe_id, 36)),
      date,
      category,
      servings: amount(row.servings ?? '2'),
      order: Number(order),
      cooked: row.cooked === true,
      leftover_id: row.leftover_id == null ? null : assertUUID(text(row.leftover_id, 36)),
      recurrence: rule,
    };
  } else if (kind === 'pantry') {
    const period = row.include_week_start == null ? null : text(row.include_week_start, 10);
    if (period !== null && monday(period) !== period) throw new Error('invalid_pantry_period');
    if (
      (row.available !== undefined && typeof row.available !== 'boolean') ||
      (row.include_this_week !== undefined && typeof row.include_this_week !== 'boolean')
    )
      throw new Error('invalid_pantry');
    result = {
      name: required(row.name, 200),
      available: row.available !== false,
      include_this_week: row.include_this_week === true,
      include_week_start: period,
    };
  } else if (kind === 'leftover') {
    const produced = text(row.produced_on, 10);
    civil(produced);
    if (row.discarded !== undefined && typeof row.discarded !== 'boolean')
      throw new Error('invalid_leftover');
    result = {
      recipe_id: assertUUID(text(row.recipe_id, 36)),
      portions: amount(row.portions),
      produced_on: produced,
      discarded: row.discarded === true,
    };
  } else if (kind === 'template') {
    const meals = list(row.meals, 100).map((value) => {
      const slot = object(value);
      const weekday = slot.weekday;
      const category = text(slot.category, 20) as Category;
      if (
        !Number.isInteger(weekday) ||
        Number(weekday) < 0 ||
        Number(weekday) > 6 ||
        !categories.includes(category)
      )
        throw new Error('invalid_template');
      return {
        weekday: Number(weekday),
        category,
        recipe_id: assertUUID(text(slot.recipe_id, 36)),
        servings: amount(slot.servings),
      };
    });
    result = { name: required(row.name, 100), meals };
  } else {
    throw new Error('invalid_kind');
  }
  return result as Payloads[K];
}

export function pantryIncludedThisWeek(item: Pantry, day: string): boolean {
  return item.include_this_week && item.include_week_start === monday(day);
}

export function validateChange(input: Change): Change {
  if (
    !input ||
    !kinds.includes(input.kind) ||
    !Number.isSafeInteger(input.revision) ||
    input.revision < 1 ||
    typeof input.deleted !== 'boolean'
  )
    throw new Error('invalid_server_response');
  assertUUID(input.entity_id);
  if (!input.deleted) payload(input.kind, input.payload);
  return input;
}
