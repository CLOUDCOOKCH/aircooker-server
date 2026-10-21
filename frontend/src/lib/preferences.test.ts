import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DEFAULT_PLANNING,
  parsePlanningContext,
  parsePreferences,
  parsePreferenceDraft,
} from './preferences.ts';
import { emptyRecipe, entityKey, uuid } from './domain.ts';
import type { Entity } from './domain.ts';
import { suggestWeek } from './planning.ts';

test('untrusted shared preference snapshots reject unsafe categories, portions and acceptance metadata', () => {
  const prefs = DEFAULT_PLANNING.preferences;
  assert.deepEqual(
    parsePreferences({ ...prefs, categories: ['dinner', 'breakfast'], servings: '3.50' }),
    { ...prefs, categories: ['breakfast', 'dinner'], servings: '3.5' },
  );
  for (const invalid of [
    { categories: [] },
    { categories: ['dinner', 'dinner'] },
    { categories: ['unknown'] },
    { servings: '1e999' },
    { servings: '0' },
    { servings: '101' },
    { servings: '2xyz' },
  ])
    assert.throws(() => parsePreferences({ ...prefs, ...invalid }));
  assert.throws(() =>
    parsePlanningContext({ ...DEFAULT_PLANNING, accepted_counts: { [uuid()]: -1 } }),
  );
  assert.throws(() =>
    parsePlanningContext({ ...DEFAULT_PLANNING, accepted_counts: { invalid: 1 } }),
  );
  assert.throws(() => parsePlanningContext({ ...DEFAULT_PLANNING, revision: 0.5 }));
});

test('shared category and portion defaults stay local and learned preference cannot defeat variety', () => {
  const recipes = Array.from({ length: 3 }, () => {
    const id = uuid();
    return {
      id,
      key: entityKey('recipe', id),
      kind: 'recipe',
      payload: { ...emptyRecipe(), title: 'Household recipe' },
      deleted: false,
      revision: 1,
    } as Entity<'recipe'>;
  });
  const context = {
    ...DEFAULT_PLANNING,
    preferences: {
      ...DEFAULT_PLANNING.preferences,
      categories: ['breakfast', 'lunch'] as ('breakfast' | 'lunch')[],
      allow_repeats: true,
      servings: '3.5',
    },
    accepted_counts: { [recipes[0].id]: 1000000 },
  };
  const preview = suggestWeek(recipes, '2026-10-19', 0, context);
  assert.equal(preview.length, 14);
  assert.deepEqual(new Set(preview.map((item) => item.category)), new Set(['breakfast', 'lunch']));
  assert.ok(preview.every((item) => item.servings === '3.5'));
  assert.equal(preview[0].recipeID, recipes[0].id);
  assert.equal(preview[0].reason, 'accepted');
  for (let offset = 0; offset + 3 <= preview.length; offset += 3)
    assert.equal(new Set(preview.slice(offset, offset + 3).map((item) => item.recipeID)).size, 3);
  const unique = suggestWeek(recipes, '2026-10-19', 0, {
    ...context,
    preferences: { ...context.preferences, allow_repeats: false },
  });
  assert.equal(unique.length, 3);
});

test('fixed suggestion portions reserve leftovers across multiple categories and the opt-out is respected', () => {
  const rid = uuid(),
    lid = uuid();
  const recipe: Entity<'recipe'> = {
    id: rid,
    key: entityKey('recipe', rid),
    kind: 'recipe',
    payload: { ...emptyRecipe(), title: 'Rice' },
    deleted: false,
    revision: 1,
  };
  const leftover: Entity<'leftover'> = {
    id: lid,
    key: entityKey('leftover', lid),
    kind: 'leftover',
    payload: { recipe_id: rid, portions: '5', produced_on: '2026-10-19', discarded: false },
    deleted: false,
    revision: 2,
  };
  const context = {
    ...DEFAULT_PLANNING,
    preferences: {
      ...DEFAULT_PLANNING.preferences,
      categories: ['breakfast', 'lunch'] as ('breakfast' | 'lunch')[],
      servings: '2',
    },
  };
  const suggested = suggestWeek([recipe, leftover], '2026-10-19', 0, context);
  assert.equal(suggested.filter((item) => item.leftoverID === lid).length, 2);
  assert.equal(
    suggested
      .filter((item) => item.leftoverID === lid)
      .reduce((sum, item) => sum + Number(item.servings), 0),
    4,
  );
  assert.ok(
    suggestWeek([recipe, leftover], '2026-10-19', 0, {
      ...context,
      preferences: { ...context.preferences, use_leftovers: false },
    }).every((item) => item.leftoverID === null),
  );
});

test('an incomplete offline settings draft stays editable while corrupt identities are rejected', () => {
  const draft = {
    request_id: uuid(),
    base_revision: 1,
    preferences: { ...DEFAULT_PLANNING.preferences, categories: [], servings: '' },
  };
  assert.deepEqual(parsePreferenceDraft(draft), draft);
  assert.throws(() => parsePreferenceDraft({ ...draft, request_id: 'invalid' }));
  assert.throws(() =>
    parsePreferenceDraft({
      ...draft,
      preferences: { ...draft.preferences, categories: ['unknown'] },
    }),
  );
});
