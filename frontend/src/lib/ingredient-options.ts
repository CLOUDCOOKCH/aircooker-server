import catalog from '../../../src/mealf/food_catalog.json' with { type: 'json' };

// These are stored unit identities, not conversions between unlike ingredients.
export const RECIPE_UNITS = [
  ['', 'No unit', 'Ohne Einheit'],
  ['g', 'Gram (g)', 'Gramm (g)'],
  ['kg', 'Kilogram (kg)', 'Kilogramm (kg)'],
  ['mg', 'Milligram (mg)', 'Milligramm (mg)'],
  ['ml', 'Millilitre (ml)', 'Milliliter (ml)'],
  ['cl', 'Centilitre (cl)', 'Zentiliter (cl)'],
  ['dl', 'Decilitre (dl)', 'Deziliter (dl)'],
  ['l', 'Litre (l)', 'Liter (l)'],
  ['tsp', 'Teaspoon', 'Teelöffel'],
  ['tbsp', 'Tablespoon', 'Esslöffel'],
  ['piece', 'Piece', 'Stück'],
  ['cup', 'Cup', 'Tasse'],
  ['pinch', 'Pinch', 'Prise'],
  ['clove', 'Clove', 'Zehe'],
  ['slice', 'Slice', 'Scheibe'],
  ['can', 'Can', 'Dose'],
  ['pack', 'Pack', 'Packung'],
  ['bunch', 'Bunch', 'Bund'],
] as const;

export type IngredientOption = {
  name: string;
  pantry: boolean;
  uses: number;
  aliases: string[];
};
const key = (name: string) =>
  name.normalize('NFKC').toLocaleLowerCase('en').trim().replace(/\s+/g, ' ');
const searchKey = (name: string) =>
  key(name).normalize('NFD').replace(/\p{M}/gu, '').replace(/ß/g, 'ss');

/** Suggestions only. Never use fuzzy matches as shopping or ownership identities. */
export function ingredientOptions(pantry: string[], recipes: string[][]): IngredientOption[] {
  const options = new Map<string, IngredientOption>();
  const add = (name: string, inPantry: boolean, uses: number) => {
    name = name.trim();
    if (!name) return;
    const id = key(name),
      existing = options.get(id);
    if (existing) {
      existing.pantry ||= inPantry;
      existing.uses += uses;
      return;
    }
    const food = catalog.items.find((food) =>
      [...Object.values(food.name), ...food.aliases].some((alias) => key(alias) === id),
    );
    options.set(id, {
      name,
      pantry: inPantry,
      uses,
      aliases: [
        ...new Set([name, ...(food ? [...Object.values(food.name), ...food.aliases] : [])]),
      ],
    });
  };
  pantry.forEach((name) => add(name, true, 0));
  recipes.forEach((names) =>
    [...new Set(names.map((name) => name.trim()))].forEach((name) => add(name, false, 1)),
  );
  return [...options.values()];
}

function editDistance(left: string, right: string): number {
  let row = Array.from({ length: right.length + 1 }, (_, i) => i);
  for (let i = 0; i < left.length; i++) {
    const next = [i + 1];
    for (let j = 0; j < right.length; j++)
      next.push(Math.min(next[j] + 1, row[j + 1] + 1, row[j] + Number(left[i] !== right[j])));
    row = next;
  }
  return row[right.length];
}

export function suggestIngredients(options: IngredientOption[], query: string): IngredientOption[] {
  const needle = searchKey(query);
  if (!needle || needle.length > 200) return [];
  const score = (option: IngredientOption) =>
    Math.min(
      ...option.aliases.map((alias) => {
        const text = searchKey(alias);
        if (text === needle) return 0;
        if (text.startsWith(needle)) return 1;
        if (needle.length >= 2 && text.includes(needle)) return 2;
        if (needle.length >= 4 && Math.abs(text.length - needle.length) <= 2) {
          const distance = editDistance(text, needle);
          if (distance <= (needle.length >= 6 ? 2 : 1)) return 3 + distance;
        }
        return Infinity;
      }),
    );
  return options
    .map((option) => ({ option, score: score(option) }))
    .filter((row) => Number.isFinite(row.score))
    .sort(
      (a, b) =>
        a.score - b.score ||
        Number(b.option.pantry) - Number(a.option.pantry) ||
        b.option.uses - a.option.uses ||
        a.option.name.localeCompare(b.option.name),
    )
    .slice(0, 6)
    .map((row) => row.option);
}

const EMOJI: Record<string, string> = {
  salt: '🧂',
  pepper: '🧂',
  'olive-oil': '🫒',
  'rapeseed-oil': '🌻',
  vinegar: '🍶',
  stock: '🥣',
  'soy-sauce': '🍶',
  flour: '🌾',
  sugar: '🍬',
  rice: '🍚',
  pasta: '🍝',
  oats: '🌾',
  'canned-tomatoes': '🍅',
  'tomato-paste': '🍅',
  chickpeas: '🫘',
  lentils: '🫘',
  beans: '🫘',
  honey: '🍯',
  'baking-powder': '🥄',
  milk: '🥛',
  eggs: '🥚',
  butter: '🧈',
  onions: '🧅',
  garlic: '🧄',
  chicken: '🍗',
  beef: '🥩',
  fish: '🐟',
  tofu: '🫘',
  potatoes: '🥔',
  mushrooms: '🍄',
  broccoli: '🥦',
  cheese: '🧀',
};
const EXTRA_EMOJI: Record<string, string> = {
  tomato: '🍅',
  tomatoes: '🍅',
  tomate: '🍅',
  tomaten: '🍅',
  bread: '🍞',
  brot: '🍞',
  apple: '🍎',
  apples: '🍎',
  apfel: '🍎',
  carrot: '🥕',
  carrots: '🥕',
  karotte: '🥕',
  karotten: '🥕',
  ruebli: '🥕',
  rubli: '🥕',
  lemon: '🍋',
  zitrone: '🍋',
};
export function foodEmoji(name: string): string {
  const id = key(name);
  const food = catalog.items.find((food) =>
    [...Object.values(food.name), ...food.aliases].some((alias) => key(alias) === id),
  );
  return (food && EMOJI[food.id]) || EXTRA_EMOJI[searchKey(name)] || '🥣';
}
