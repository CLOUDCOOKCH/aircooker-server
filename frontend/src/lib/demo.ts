import { emptyIngredient, emptyRecipe, today, addDays, monday } from './domain.ts';
import { LocalStore } from './store.ts';
import type { Edit } from './store.ts';
export const DEMO_ID = '00000000-0000-4000-8000-000000000001';
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`;
export async function openDemo(): Promise<LocalStore> {
  const store = await LocalStore.open(DEMO_ID);
  if (await store.setting('demo', false)) return store;
  const date = today(Intl.DateTimeFormat().resolvedOptions().timeZone);
  const entries: Edit[] = [
    {
      kind: 'recipe',
      id: id(2),
      value: {
        ...emptyRecipe(),
        title: 'Lemon & herb chicken',
        description:
          'Golden chicken, roasted potatoes and a little lemon. A simple dinner to come home to.',
        servings: '2',
        rating: 5,
        image_id: id(20),
        ingredients: [
          { ...emptyIngredient(), name: 'Chicken thighs', quantity: '4', unit: 'piece' },
          { ...emptyIngredient(), name: 'Potatoes', quantity: '500', unit: 'g' },
          { ...emptyIngredient(), name: 'Lemon', quantity: '1', unit: 'piece' },
          { ...emptyIngredient(), name: 'Olive oil', quantity: '2', unit: 'tbsp' },
          { ...emptyIngredient(), name: 'Rosemary', preparation: 'a few sprigs' },
        ],
        steps: [
          'Heat the oven to 200°C. Cut the potatoes into even pieces and place in a roasting dish.',
          'Toss the chicken and potatoes with olive oil, lemon juice and rosemary. Season to taste.',
          'Roast for 40–45 minutes, until the potatoes are golden and the chicken reaches a safe internal temperature. Rest briefly before serving.',
        ],
        provenance: {
          content: 'Original illustrative demo recipe',
          image:
            'AI-generated original food illustration; not a photograph of this recipe being cooked',
        },
      },
    },
    {
      kind: 'recipe',
      id: id(3),
      value: {
        ...emptyRecipe(),
        title: 'Creamy tomato pasta',
        description: 'Your weeknight cupboard favourite.',
        rating: 4,
        ingredients: [
          { ...emptyIngredient(), name: 'Pasta', quantity: '200', unit: 'g' },
          { ...emptyIngredient(), name: 'Tomatoes', quantity: '400', unit: 'g' },
        ],
        steps: [
          'Cook the pasta according to the packet instructions.',
          'Simmer the tomatoes, season and toss with the drained pasta.',
        ],
        provenance: { content: 'Original illustrative demo recipe' },
      },
    },
    {
      kind: 'recipe',
      id: id(4),
      value: {
        ...emptyRecipe(),
        title: 'Overnight oats',
        servings: '1',
        ingredients: [
          { ...emptyIngredient(), name: 'Oats', quantity: '50', unit: 'g' },
          { ...emptyIngredient(), name: 'Milk', quantity: '150', unit: 'ml' },
        ],
        steps: ['Combine the oats and milk in a covered jar. Refrigerate overnight.'],
        provenance: { content: 'Original illustrative demo recipe' },
      },
    },
    {
      kind: 'pantry',
      id: id(5),
      value: { name: 'Olive oil', available: true, include_this_week: false },
    },
    {
      kind: 'pantry',
      id: id(6),
      value: { name: 'Salt', available: true, include_this_week: false },
    },
    {
      kind: 'meal',
      id: id(7),
      value: {
        recipe_id: id(2),
        date,
        category: 'dinner',
        servings: '2',
        order: 0,
        cooked: false,
        leftover_id: null,
        recurrence: null,
      },
    },
    {
      kind: 'meal',
      id: id(8),
      value: {
        recipe_id: id(4),
        date,
        category: 'breakfast',
        servings: '1',
        order: 0,
        cooked: false,
        leftover_id: null,
        recurrence: null,
      },
    },
    {
      kind: 'meal',
      id: id(9),
      value: {
        recipe_id: id(3),
        date: addDays(monday(date), 6),
        category: 'dinner',
        servings: '2',
        order: 0,
        cooked: false,
        leftover_id: null,
        recurrence: null,
      },
    },
  ];
  let photos: Parameters<LocalStore['seedDemo']>[1] = [];
  try {
    const response = await fetch('/app/art/lemon-chicken.png');
    if (response.ok) photos = [{ id: id(20), blob: await response.blob(), pending: false }];
  } catch {
    /* demo still works without its optional image */
  }
  await store.seedDemo(entries, photos);
  await store.setSetting('household', {
    name: 'Demo kitchen',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: 'en',
  });
  return store;
}
