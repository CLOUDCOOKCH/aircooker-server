import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyIngredient, emptyRecipe, entityKey, uuid } from './domain.ts';
import type { Entity, Meal } from './domain.ts';
import {
  applyTemplate,
  availablePortions,
  changeOccurrence,
  copyMeals,
  makeTemplate,
  occurrences,
  parseQuantity,
  scale,
  suggestWeek,
} from './planning.ts';
test('legacy quantities cannot bypass bounds through scaling, parsing or leftovers', () => {
  const r = recipe().payload;
  r.ingredients = [
    {
      ...emptyIngredient(),
      id: uuid(),
      name: 'Flour',
      quantity: '1e-1000000',
      quantity_max: null,
      unit: 'g',
      preparation: '',
      original_text: '',
    },
  ];
  assert.throws(() => scale(r, '2'), /invalid_quantity/);
  r.ingredients[0].quantity = '1e-98';
  assert.equal(scale(r, '1e-98')[0].quantity?.length, 199);
  assert.throws(() => scale(r, '1e-1000000'), /invalid_quantity/);
  assert.throws(() => scale({ ...r, servings: '1e-1000000' }, '2'), /invalid_quantity/);
  assert.throws(() => parseQuantity('0.' + '0'.repeat(1000) + '1'), /invalid_quantity/);
  assert.equal(parseQuantity('⅓').quantity, '0.33333333333333333333');
  const id = uuid();
  const leftover: Entity<'leftover'> = {
    key: entityKey('leftover', id),
    id,
    kind: 'leftover',
    revision: 0,
    deleted: false,
    payload: {
      recipe_id: uuid(),
      portions: '1e-1000000',
      produced_on: '2026-10-19',
      discarded: false,
    },
  };
  assert.throws(() => availablePortions(leftover, []), /invalid_quantity/);
  leftover.payload.portions = '2';
  const m = meal(leftover.payload.recipe_id);
  m.payload.leftover_id = id;
  m.payload.servings = '1e-1000000';
  assert.throws(() => availablePortions(leftover, [m]), /invalid_quantity/);
  m.payload.servings = '0.5';
  assert.equal(availablePortions(leftover, [m]), '1.5');
});
const recipe = (title = 'Soup'): Entity<'recipe'> => {
  const id = uuid();
  return {
    id,
    key: entityKey('recipe', id),
    kind: 'recipe',
    payload: { ...emptyRecipe(), title },
    deleted: false,
    revision: 0,
  };
};
const meal = (id: string, changes: Partial<Meal> = {}): Entity<'meal'> => {
  const key = uuid();
  return {
    id: key,
    key: entityKey('meal', key),
    kind: 'meal',
    revision: 0,
    deleted: false,
    payload: {
      recipe_id: id,
      date: '2026-10-19',
      category: 'dinner',
      servings: '2',
      cooked: false,
      order: 0,
      leftover_id: null,
      recurrence: null,
      ...changes,
    },
  };
};
test('recurrences are bounded inclusive civil dates with exceptions and detached edits', () => {
  const r = recipe();
  const m = meal(r.id, {
    recurrence: { interval_weeks: 1, until: '2026-11-02', exceptions: ['2026-10-26'] },
  });
  const items = occurrences([m], '2026-10-19', '2026-11-02');
  assert.deepEqual(
    items.map((x) => x.day),
    ['2026-10-19', '2026-11-02'],
  );
  const edits = changeOccurrence(items[1], { date: '2026-11-03' });
  assert.equal(edits.length, 2);
  assert.equal(edits[1].value.recurrence, null);
  assert.equal(edits[1].value.date, '2026-11-03');
  assert.ok(edits[0].value.recurrence?.exceptions?.includes('2026-11-02'));
  assert.throws(() => occurrences([m], '2026-01-01', '2028-01-01'));
});
test('copies and templates detach recurrence and reject copying existing leftovers', () => {
  const r = recipe();
  const items = occurrences([meal(r.id)], '2026-10-19', '2026-10-25');
  assert.equal(copyMeals(items, 7)[0].value.date, '2026-10-26');
  const template = makeTemplate(items, 'Week');
  assert.equal(applyTemplate(template, '2026-10-29', [r])[0].value.date, '2026-10-26');
  assert.throws(() => applyTemplate(template, '2026-10-29', []));
  const leftovers = occurrences([meal(r.id, { leftover_id: uuid() })], '2026-10-19', '2026-10-25');
  assert.throws(() => copyMeals(leftovers, 7));
  assert.throws(() => makeTemplate(leftovers, 'No'));
});
test('fractions and ranges scale exactly and non numeric quantities remain unquantified', () => {
  assert.deepEqual(parseQuantity('1½ – 2'), { quantity: '1.5', quantity_max: '2' });
  assert.equal(parseQuantity('0,25').quantity, '0.25');
  assert.throws(() => parseQuantity('1/0'));
  assert.throws(() => parseQuantity('2 onions'));
  assert.throws(() => parseQuantity('3–2'));
  const r = recipe().payload;
  r.ingredients = [
    {
      id: uuid(),
      name: 'Salt',
      quantity: null,
      quantity_max: null,
      unit: '',
      preparation: 'to taste',
      original_text: 'Salt to taste',
      quantity_text: '',
      notes: '',
      optional: false,
    },
    {
      id: uuid(),
      name: 'Flour',
      quantity: '0.25',
      quantity_max: '0.5',
      unit: 'kg',
      preparation: '',
      original_text: '',
      quantity_text: '',
      notes: '',
      optional: false,
    },
  ];
  assert.equal(scale(r, '3')[0].quantity, null);
  assert.equal(scale(r, '3')[1].quantity_max, '0.75');
});
test('suggestions preserve occupied slots and avoid repeated recipes and oversubscribed leftovers', () => {
  const a = recipe('A'),
    b = recipe('B'),
    c = recipe('C');
  const m = meal(a.id);
  const id = uuid();
  const l: Entity<'leftover'> = {
    id,
    key: entityKey('leftover', id),
    kind: 'leftover',
    revision: 0,
    deleted: false,
    payload: { recipe_id: b.id, portions: '1', produced_on: '2026-10-19', discarded: false },
  };
  const suggestions = suggestWeek([a, b, c, m, l], '2026-10-19');
  assert.equal(suggestions.length, 2);
  assert.equal(suggestions[0].reason, 'leftovers');
  assert.equal(suggestions.filter((x) => x.leftoverID === id).length, 1);
  assert.ok(suggestions.every((x) => x.date !== '2026-10-19'));
  assert.ok(suggestions.every((x) => x.recipeID !== a.id));
});
