import Decimal from 'decimal.js';
import { addDays, categories, civil, distance, emptyRecipe, monday, uuid } from './domain.ts';
import type { Category, Entity, Meal, Recipe, Template } from './domain.ts';
import type { Edit } from './store.ts';

export type Occurrence = { entity: Entity<'meal'>; day: string; key: string };
export function occurrences(meals: Entity<'meal'>[], start: string, end: string): Occurrence[] {
  const span = distance(start, end);
  if (span < 0 || span > 366) throw new Error('invalid_calendar_window');
  const result: Occurrence[] = [];
  for (const entity of meals) {
    const meal = entity.payload;
    const step = 7 * (meal.recurrence?.interval_weeks ?? 1);
    let day = meal.date;
    if (meal.recurrence)
      day = addDays(day, Math.max(0, Math.ceil(distance(day, start) / step)) * step);
    const until = meal.recurrence
      ? meal.recurrence.until < end
        ? meal.recurrence.until
        : end
      : day;
    while (day <= until) {
      if (day >= start && day <= end && !meal.recurrence?.exceptions?.includes(day))
        result.push({ entity, day, key: `${entity.id}:${day}` });
      if (!meal.recurrence) break;
      day = addDays(day, step);
    }
  }
  return result.sort(
    (a, b) =>
      a.day.localeCompare(b.day) ||
      categories.indexOf(a.entity.payload.category) -
        categories.indexOf(b.entity.payload.category) ||
      a.entity.payload.order - b.entity.payload.order ||
      a.key.localeCompare(b.key),
  );
}
export function mealEdit(recipe: Entity<'recipe'>, date: string, category: Category): Edit<'meal'> {
  return {
    kind: 'meal',
    id: uuid(),
    value: {
      recipe_id: recipe.id,
      date,
      category,
      servings: recipe.payload.servings,
      order: 0,
      cooked: false,
      leftover_id: null,
      recurrence: null,
    },
  };
}
/** An occurrence edit adds an exception and a detached record, never expands an infinite series. */
export function changeOccurrence(item: Occurrence, changes: Partial<Meal> | null): Edit<'meal'>[] {
  const { entity, day } = item;
  const meal = entity.payload;
  if (!meal.recurrence)
    return [
      { kind: 'meal', id: entity.id, value: { ...meal, ...changes }, deleted: changes === null },
    ];
  const excluded: Edit<'meal'> = {
    kind: 'meal',
    id: entity.id,
    value: {
      ...meal,
      recurrence: {
        ...meal.recurrence,
        exceptions: [...new Set([...(meal.recurrence.exceptions ?? []), day])],
      },
    },
  };
  return changes === null
    ? [excluded]
    : [
        excluded,
        { kind: 'meal', id: uuid(), value: { ...meal, date: day, recurrence: null, ...changes } },
      ];
}
export function copyMeals(items: Occurrence[], offset: number): Edit<'meal'>[] {
  if (!Number.isInteger(offset) || offset === 0) throw new Error('invalid_copy_date');
  if (items.some((item) => item.entity.payload.leftover_id))
    throw new Error('copy_contains_leftovers');
  return items.map(({ entity, day }) => ({
    kind: 'meal',
    id: uuid(),
    value: { ...entity.payload, date: addDays(day, offset), cooked: false, recurrence: null },
  }));
}
export function makeTemplate(items: Occurrence[], name: string): Template {
  if (items.some((item) => item.entity.payload.leftover_id))
    throw new Error('template_contains_leftovers');
  return {
    name,
    meals: items.map(({ entity, day }) => ({
      weekday: (civil(day).getUTCDay() + 6) % 7,
      category: entity.payload.category,
      recipe_id: entity.payload.recipe_id,
      servings: entity.payload.servings,
    })),
  };
}
export function applyTemplate(
  template: Template,
  week: string,
  recipes: Entity<'recipe'>[],
): Edit<'meal'>[] {
  const available = new Set(recipes.map((row) => row.id));
  if (template.meals.some((meal) => !available.has(meal.recipe_id)))
    throw new Error('recipe_unavailable');
  return template.meals.map((slot) => ({
    kind: 'meal',
    id: uuid(),
    value: {
      recipe_id: slot.recipe_id,
      category: slot.category,
      date: addDays(monday(week), slot.weekday),
      servings: slot.servings,
      order: 0,
      cooked: false,
      recurrence: null,
      leftover_id: null,
    },
  }));
}
export function scale(recipe: Recipe, servings: string): Recipe['ingredients'] {
  const ratio = new Decimal(servings).div(recipe.servings);
  return recipe.ingredients.map((item) => ({
    ...item,
    quantity: item.quantity === null ? null : new Decimal(item.quantity).mul(ratio).toFixed(),
    quantity_max:
      item.quantity_max === null ? null : new Decimal(item.quantity_max).mul(ratio).toFixed(),
  }));
}
/** Conservative editor parsing: explicit fractions/decimals/ranges, never a numeric prefix. */
export function parseQuantity(raw: string): {
  quantity: string | null;
  quantity_max: string | null;
} {
  const input = raw
    .trim()
    .replaceAll(',', '.')
    .replaceAll('½', ' 1/2')
    .replaceAll('¼', ' 1/4')
    .replaceAll('¾', ' 3/4')
    .replaceAll('⅓', ' 1/3')
    .replaceAll('⅔', ' 2/3');
  if (!input) return { quantity: null, quantity_max: null };
  const parse = (part: string) => {
    const match = part.trim().match(/^(?:(\d+)\s+)?(\d+)\/(\d+)$/);
    let value: Decimal;
    if (match) {
      if (Number(match[3]) === 0) throw new Error('invalid_quantity');
      value = new Decimal(match[1] ?? 0).plus(new Decimal(match[2]).div(match[3]));
    } else {
      if (!/^\d+(?:\.\d+)?$/.test(part.trim())) throw new Error('invalid_quantity');
      value = new Decimal(part.trim());
    }
    if (value.lt(0) || value.gt(1_000_000)) throw new Error('invalid_quantity');
    return value.toFixed();
  };
  const parts = input.split(/\s*[–-]\s*/);
  if (parts.length > 2) throw new Error('invalid_quantity');
  const quantity = parse(parts[0]);
  const upper = parts.length === 2 ? parse(parts[1]) : null;
  if (upper !== null && new Decimal(upper).lt(quantity)) throw new Error('invalid_quantity');
  return { quantity, quantity_max: upper };
}
export function availablePortions(leftover: Entity<'leftover'>, meals: Entity<'meal'>[]): string {
  return meals
    .filter((row) => row.payload.leftover_id === leftover.id)
    .reduce((n, row) => n.minus(row.payload.servings), new Decimal(leftover.payload.portions))
    .toFixed();
}
export type Suggestion = {
  recipeID: string;
  date: string;
  category: Category;
  servings: string;
  leftoverID: string | null;
  reason: 'leftovers' | 'new' | 'rated' | 'variety';
};
/** Pure local ranking. Fixed seed makes a preview repeatable; approval is a separate edit. */
export function suggestWeek(rows: Entity[], week: string, seed = 0): Suggestion[] {
  const recipes = rows.filter((row) => row.kind === 'recipe' && !row.deleted) as Entity<'recipe'>[];
  const meals = rows.filter((row) => row.kind === 'meal' && !row.deleted) as Entity<'meal'>[];
  const leftovers = rows.filter(
    (row) => row.kind === 'leftover' && !row.deleted,
  ) as Entity<'leftover'>[];
  const start = monday(week);
  const scheduled = occurrences(meals, start, addDays(start, 6));
  const history = occurrences(meals, addDays(start, -180), addDays(start, -1));
  const used = new Set(scheduled.map((item) => item.entity.payload.recipe_id));
  const result: Suggestion[] = [];
  for (let index = 0; index < 7; index++) {
    const day = addDays(start, index);
    if (scheduled.some((item) => item.day === day && item.entity.payload.category === 'dinner'))
      continue;
    const leftover = leftovers.find(
      (row) =>
        !row.payload.discarded &&
        row.payload.produced_on <= day &&
        recipes.some((recipe) => recipe.id === row.payload.recipe_id) &&
        new Decimal(availablePortions(row, meals)).gt(0) &&
        !result.some((suggestion) => suggestion.leftoverID === row.id),
    );
    if (leftover) {
      result.push({
        recipeID: leftover.payload.recipe_id,
        date: day,
        category: 'dinner',
        servings: availablePortions(leftover, meals),
        leftoverID: leftover.id,
        reason: 'leftovers',
      });
      used.add(leftover.payload.recipe_id);
      continue;
    }
    const ranked = recipes
      .map((recipe, order) => {
        const cooked = history.filter(
          (item) => item.entity.payload.recipe_id === recipe.id && item.entity.payload.cooked,
        );
        const recent = cooked.length
          ? Math.max(...cooked.map((item) => 40 - Math.min(40, distance(item.day, day))))
          : 0;
        return {
          recipe,
          cooked,
          score:
            (recipe.payload.rating ?? 3) * 4 -
            recent -
            cooked.length * 2 -
            (used.has(recipe.id) ? 1000 : 0) +
            ((order + seed) % Math.max(1, recipes.length)) / recipes.length,
        };
      })
      .sort((a, b) => b.score - a.score || a.recipe.id.localeCompare(b.recipe.id));
    const choice = ranked[0];
    if (!choice || used.has(choice.recipe.id)) continue;
    used.add(choice.recipe.id);
    result.push({
      recipeID: choice.recipe.id,
      date: day,
      category: 'dinner',
      servings: choice.recipe.payload.servings,
      leftoverID: null,
      reason: !choice.cooked.length
        ? 'new'
        : (choice.recipe.payload.rating ?? 0) >= 4
          ? 'rated'
          : 'variety',
    });
  }
  return result;
}
export function cloneRecipe(recipe: Recipe): Recipe {
  const provenance = { ...recipe.provenance };
  if (provenance.import_job_id) provenance.original_import_job_id = provenance.import_job_id;
  delete provenance.import_job_id;
  delete provenance.reviewed_by_user;
  return {
    ...emptyRecipe(),
    ...structuredClone(recipe),
    provenance,
    ingredients: recipe.ingredients.map((item) => ({ ...item, id: uuid() })),
  };
}
