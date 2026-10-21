import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  addDays,
  amount,
  civil,
  distance,
  emptyRecipe,
  monday,
  payload,
  today,
  uuid,
} from './domain.ts';

test('civil dates survive DST, travel, leap days and year boundaries', () => {
  assert.equal(addDays('2026-10-24', 2), '2026-10-26');
  assert.equal(monday('2027-01-01'), '2026-12-28');
  assert.equal(addDays('2028-02-28', 1), '2028-02-29');
  assert.equal(distance('2026-03-28', '2026-03-30'), 2);
  assert.equal(today('America/Los_Angeles', new Date('2026-10-21T01:00:00Z')), '2026-10-20');
  for (const input of ['2026-02-29', '2026-1-01', '0000-01-01']) assert.throws(() => civil(input));
});
test('quantities stay exact and invalid numeric prefixes never reach the outbox', () => {
  assert.equal(amount('0.1'), '0.1');
  assert.equal(amount('1e-3'), '0.001');
  for (const input of ['2kg', '1/0', 'NaN', '-1', '1000001', '0'])
    assert.throws(() => amount(input));
  assert.equal(amount('0', true), '0');
});
test('full recipe snapshots retain attribution and validate ranges and identities', () => {
  const ingredient = { id: uuid(), name: 'Flour', quantity: '0.5', quantity_max: '0.75' };
  const recipe = payload('recipe', {
    ...emptyRecipe(),
    title: 'Pancakes',
    ingredients: [ingredient],
    source_url: 'https://example.invalid/recipe',
    nutrition: { calories: 'As supplied' },
  });
  assert.equal(recipe.ingredients[0].quantity, '0.5');
  assert.equal(recipe.nutrition?.calories, 'As supplied');
  assert.equal(recipe.source_url, 'https://example.invalid/recipe');
  assert.throws(() =>
    payload('recipe', { ...recipe, ingredients: [{ ...ingredient, quantity_max: '0.2' }] }),
  );
  assert.throws(() => payload('recipe', { ...recipe, ingredients: [ingredient, ingredient] }));
  assert.throws(() =>
    payload('leftover', { recipe_id: uuid(), portions: '0', produced_on: '2026-10-21' }),
  );
});
