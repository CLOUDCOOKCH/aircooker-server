import type { components } from '../api-schema';
import { emptyRecipe, uuid } from './domain.ts';
import type { Recipe } from './domain.ts';

export type Extraction = components['schemas']['ExtractionResult'];
export function sourceKind(type: string): string | null {
  if (['image/jpeg', 'image/png', 'image/webp'].includes(type)) return 'image';
  if (type === 'application/pdf') return 'pdf';
  if (['video/mp4', 'video/webm'].includes(type)) return 'video';
  return null;
}

/** Incomplete facts stay blank in the editor; canonical validation runs on explicit save. */
export function extractionPreview(result: Extraction, sourceURL?: string | null): Recipe {
  const r = result.recipe;
  return {
    ...emptyRecipe(),
    schema_version: result.schemaVersion,
    title: r.title ?? '',
    description: r.description ?? '',
    servings: r.servings == null ? '' : String(r.servings),
    ingredients: r.ingredients.map((i) => ({
      id: uuid(),
      name: i.name ?? '',
      quantity: i.quantity.value == null ? null : String(i.quantity.value),
      quantity_max: i.quantity.maxValue == null ? null : String(i.quantity.maxValue),
      unit: i.quantity.unit ?? '',
      preparation: i.preparation ?? '',
      original_text: i.originalText ?? '',
      quantity_text: i.quantity.rawText ?? '',
      notes: i.notes ?? '',
      optional: i.optional,
      group: i.group,
    })),
    steps: r.instructions.map((i) => i.text),
    instruction_details: r.instructions.map(({ text: _text, ...detail }) => detail),
    times: r.times,
    language: r.language,
    yield_info: r.yield,
    category: r.category,
    cuisine: r.cuisine,
    tags: r.tags,
    notes: r.notes ?? '',
    source_url: sourceURL ?? null,
    source_platform: 'ai-import',
    provenance: { extractor: 'ai', review: 'required' },
  };
}
