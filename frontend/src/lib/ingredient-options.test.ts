import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  foodEmoji,
  ingredientOptions,
  RECIPE_UNITS,
  suggestIngredients,
} from './ingredient-options.ts';

test('household suggestions deduplicate spelling case and whitespace, with pantry names first', () => {
  const pantry = [' Zwiebeln ', 'Salt'];
  const recipes = [
    ['zwiebeln', 'salt', 'Salsa'],
    ['SALSA', 'Red onion'],
  ];
  const before = JSON.stringify({ pantry, recipes });
  const options = ingredientOptions(pantry, recipes);
  assert.equal(options.length, 4);
  assert.equal(options.find((row) => row.name === 'Zwiebeln')?.uses, 1);
  assert.equal(options.find((row) => row.name === 'Salsa')?.uses, 2);
  assert.equal(suggestIngredients(options, 'sa')[0].name, 'Salt');
  assert.equal(JSON.stringify({ pantry, recipes }), before);
});

test('an imported typo, singular or other catalogue language suggests the existing household name', () => {
  const options = ingredientOptions(['Zwiebeln', 'Olivenöl'], [['Mehl', 'Weizenmehl']]);
  for (const query of ['zwibel', 'Zwiebel', 'onion', 'onions'])
    assert.equal(suggestIngredients(options, query)[0]?.name, 'Zwiebeln', query);
  assert.equal(suggestIngredients(options, 'olive oil')[0].name, 'Olivenöl');
  assert.equal(suggestIngredients(options, 'olivenol')[0].name, 'Olivenöl');
  // Similar results remain explicit alternatives, never one merged ingredient identity.
  assert.deepEqual(
    suggestIngredients(options, 'Mehl').map((row) => row.name),
    ['Mehl', 'Weizenmehl'],
  );
  assert.equal(
    suggestIngredients(options, 'Almond flour').some((row) => row.name === 'Mehl'),
    false,
  );
});

test('new names are permitted without suggestions and matches are bounded', () => {
  const options = ingredientOptions([], [['Saffron'], ['Salt']]);
  assert.deepEqual(suggestIngredients(options, 'Dragon fruit'), []);
  assert.deepEqual(suggestIngredients(options, ''), []);
  assert.deepEqual(suggestIngredients(options, 'x'.repeat(201)), []);
  assert.equal(
    suggestIngredients(
      ingredientOptions(
        Array.from({ length: 30 }, (_, i) => 'Apple ' + i),
        [],
      ),
      'apple',
    ).length,
    6,
  );
  assert.equal(options.length, 2);
});

test('units have distinct stored identities without guessed weight/volume conversions', () => {
  const units = RECIPE_UNITS.map(([unit]) => unit);
  assert.equal(new Set(units).size, units.length);
  for (const unit of ['g', 'kg', 'ml', 'l', 'tbsp', 'tsp', 'piece', 'cup', 'pinch'])
    assert.ok(units.includes(unit as (typeof units)[number]));
});

test('pantry emoji lookup recognises known names and safely falls back for custom ingredients', () => {
  assert.equal(foodEmoji('Zwiebeln'), '🧅');
  assert.equal(foodEmoji('Onions'), '🧅');
  assert.equal(foodEmoji('Olivenöl'), '🫒');
  assert.equal(foodEmoji('Tomaten'), '🍅');
  assert.equal(foodEmoji('unknown household staple'), '🥣');
  assert.equal(foodEmoji('<script>alert(1)</script>'), '🥣');
  assert.equal(foodEmoji('__proto__'), '🥣');
  assert.equal(foodEmoji('constructor'), '🥣');
});
