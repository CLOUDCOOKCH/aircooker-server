import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowDown, ArrowUp, Check, Plus, Search, Star, Trash2, Upload, X } from 'lucide-react';
import Decimal from 'decimal.js';
import { useApp } from './model';
import { AddButton, Empty, IconButton, PageHeader, Photo, safeURL, Sheet } from './components';
import { amount, emptyIngredient, emptyRecipe, payload, uuid } from './lib/domain';
import type { Entity, Recipe } from './lib/domain';
import { parseQuantity, scale } from './lib/planning';
import type { ImportTask, Photo as StoredPhoto } from './lib/store';
export function Recipes({
  open,
  create,
  importRecipe,
}: {
  open: (id: string) => void;
  create: () => void;
  importRecipe: () => void;
}) {
  const { entities, t } = useApp();
  const [query, setQuery] = useState('');
  const all = entities('recipe');
  const recipes = all
    .filter((row) =>
      `${row.payload.title} ${row.payload.description} ${row.payload.ingredients.map((i) => i.name).join(' ')}`
        .toLocaleLowerCase()
        .includes(query.toLocaleLowerCase()),
    )
    .sort((a, b) => a.payload.title.localeCompare(b.payload.title));
  return (
    <>
      <PageHeader title={t('recipes')}>
        <IconButton label={t('importRecipe')} onClick={importRecipe}>
          <Upload size={21} />
        </IconButton>
        <IconButton label={t('addRecipe')} onClick={create}>
          <Plus size={23} />
        </IconButton>
      </PageHeader>
      <label className="search-field">
        <Search size={20} />
        <input
          type="search"
          placeholder={t('search')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label={t('search')}
        />
        {query && (
          <IconButton label={t('clearSearch')} onClick={() => setQuery('')}>
            <X size={16} />
          </IconButton>
        )}
      </label>
      {!all.length ? (
        <Empty title={t('emptyRecipes')} body={t('emptyRecipesBody')}>
          <button className="primary" onClick={create}>
            {t('create')}
          </button>
          <button className="text-button" onClick={importRecipe}>
            {t('importRecipe')}
          </button>
        </Empty>
      ) : !recipes.length ? (
        <p className="empty-inline">{t('searchEmpty')}</p>
      ) : (
        <div className="recipe-grid">
          {recipes.map((row) => (
            <button className="recipe-card" key={row.id} onClick={() => open(row.id)}>
              <Photo id={row.payload.image_id} />
              <div>
                <h2>{row.payload.title}</h2>
                <p>
                  {row.payload.servings}{' '}
                  {t(Number(row.payload.servings) === 1 ? 'serving' : 'servingsText')}
                  {row.payload.rating && (
                    <span className="recipe-rating">
                      <Star size={13} fill="currentColor" />
                      {row.payload.rating}
                    </span>
                  )}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}
    </>
  );
}
export function RecipeDetail({
  id,
  back,
  edit,
  plan,
}: {
  id: string;
  back: () => void;
  edit: () => void;
  plan: () => void;
}) {
  const app = useApp();
  const { t } = app;
  const entity = app.entities('recipe').find((row) => row.id === id);
  const [servings, setServings] = useState(entity?.payload.servings ?? '2');
  const [confirm, setConfirm] = useState(false),
    [error, setError] = useState(false);
  if (!entity)
    return (
      <>
        <PageHeader title={t('recipes')} back={back} />
        <p>{t('unavailableRecipe')}</p>
      </>
    );
  const recipe = entity.payload;
  let ingredients = recipe.ingredients;
  try {
    ingredients = scale(recipe, amount(servings));
  } catch {
    /* keep original quantities during intermediate input */
  }
  const scheduled = app.entities('meal').filter((row) => row.payload.recipe_id === id);
  const remove = async () => {
    try {
      await app.save([{ kind: 'recipe', id, value: recipe, deleted: true }]);
      back();
    } catch {
      setError(true);
    }
  };
  const source = safeURL(recipe.source_url),
    nutritionSource = safeURL(recipe.nutrition_source);
  return (
    <div className="recipe-content">
      <PageHeader title={recipe.title} back={back}>
        <button className="secondary" onClick={edit}>
          {t('edit')}
        </button>
      </PageHeader>
      {recipe.image_id && (
        <Photo
          id={recipe.image_id}
          className="detail-photo"
          alt={app.demo ? t('photoIllustration') : recipe.title}
        />
      )}
      <div className="detail-intro">
        <p>{recipe.description}</p>
        <button className="primary" onClick={plan}>
          <Plus size={18} />
          {t('addMeal')}
        </button>
      </div>
      {recipe.times && (
        <div className="recipe-times">
          {(['prepMinutes', 'cookMinutes', 'totalMinutes'] as const).map(
            (name) =>
              recipe.times?.[name] != null && (
                <p key={name}>
                  <strong>{t(name)}</strong>: {recipe.times[name]}
                </p>
              ),
          )}
        </div>
      )}
      {recipe.rating && (
        <p className="rating">
          <Star size={16} fill="currentColor" /> {recipe.rating} / 5
        </p>
      )}
      <div className="recipe-detail-columns">
        <section>
          <div className="section-heading">
            <h2>{t('ingredients')}</h2>
            <label className="servings-control">
              {t('servings')}
              <input
                type="number"
                min="0.01"
                max="1000000"
                step="any"
                value={servings}
                onChange={(e) => setServings(e.target.value)}
              />
            </label>
          </div>
          {ingredients.length ? (
            <ul className="ingredients-list">
              {ingredients.map((item) => (
                <li key={item.id}>
                  <span className="ingredient-amount">
                    {item.quantity === null
                      ? ''
                      : new Decimal(item.quantity).toDecimalPlaces(3).toString()}
                    {item.quantity_max !== null
                      ? '–' + new Decimal(item.quantity_max).toDecimalPlaces(3).toString()
                      : ''}{' '}
                    {item.unit}
                  </span>
                  <span>
                    {item.name}
                    {item.preparation && <small>{item.preparation}</small>}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">{t('noIngredients')}</p>
          )}
        </section>
        <section>
          <h2>{t('instructions')}</h2>
          {recipe.steps.length ? (
            <ol className="method-list">
              {recipe.steps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          ) : (
            <p className="muted">{t('noSteps')}</p>
          )}
        </section>
      </div>
      {recipe.notes && (
        <section className="section-block">
          <h2>{t('notes')}</h2>
          <p className="preserve-lines">{recipe.notes}</p>
        </section>
      )}
      {recipe.nutrition && (
        <section className="section-block">
          <h2>{t('nutrition')}</h2>
          <dl className="nutrition-list">
            {Object.entries(recipe.nutrition).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          {recipe.nutrition_source && (
            <p className="muted">
              {t('nutritionSource')}:{' '}
              {nutritionSource ? (
                <a href={nutritionSource} target="_blank" rel="noreferrer">
                  {recipe.nutrition_source}
                </a>
              ) : (
                recipe.nutrition_source
              )}
            </p>
          )}
        </section>
      )}
      {source && (
        <p className="source-link">
          <a href={source} target="_blank" rel="noreferrer">
            {t('source')} · {new URL(source).hostname}
          </a>
        </p>
      )}
      {Object.keys(recipe.provenance).length > 0 && (
        <details className="section-block">
          <summary>{t('source')}</summary>
          <dl className="provenance-list">
            {Object.entries(recipe.provenance).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </details>
      )}
      {scheduled.length > 0 && (
        <section className="section-block">
          <h2>{t('calendar')}</h2>
          <ul className="simple-list">
            {scheduled.map((row) => (
              <li key={row.id}>
                <span>
                  {row.payload.date} · {t(row.payload.category)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
      <button className="text-button danger" onClick={() => setConfirm(true)}>
        <Trash2 size={16} />
        {t('delete')}
      </button>
      {confirm && (
        <Sheet title={t('deleteRecipe')} onClose={() => setConfirm(false)}>
          <p>{t('deleteRecipeHint')}</p>
          {scheduled.length > 0 && <p role="alert">{t('deleteRecipeHint')}</p>}
          {error && <p role="alert">{t('saveError')}</p>}
          <div className="form-actions">
            <button className="secondary" onClick={() => setConfirm(false)}>
              {t('cancel')}
            </button>
            <button
              className="primary danger-fill"
              disabled={scheduled.length > 0}
              onClick={() => void remove()}
            >
              {t('delete')}
            </button>
          </div>
        </Sheet>
      )}
    </div>
  );
}
type EditorValue = {
  id: string;
  recipe: Recipe;
  quantities: string[];
  nutritionRows?: { name: string; value: string }[];
};
export function RecipeEditor({
  entity,
  task,
  back,
  initialRecipe,
  draftID,
}: {
  initialRecipe?: Recipe;
  draftID?: string;
  entity?: Entity<'recipe'>;
  task?: ImportTask;
  back: () => void;
}) {
  const app = useApp(),
    { t, store } = app;
  const key =
    draftID ?? (task ? 'import:' + task.id : entity ? 'recipe:' + entity.id : 'recipe:new');
  const [value, setValue] = useState<EditorValue | null>(null),
    [photo, setPhoto] = useState<StoredPhoto | undefined>(),
    [error, setError] = useState<string | null>(null),
    [saving, setSaving] = useState(false),
    [draftState, setDraftState] = useState(true);
  const draftChain = useRef(Promise.resolve());
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    void (async () => {
      const draft = await store.draft(key);
      const recipe = structuredClone(
        entity?.payload ?? task?.recipe ?? initialRecipe ?? emptyRecipe(),
      );
      const initial: EditorValue = {
        id: entity?.id ?? uuid(),
        recipe,
        nutritionRows: Object.entries(recipe.nutrition ?? {}).map(([name, value]) => ({
          name,
          value,
        })),
        quantities: recipe.ingredients.map((i) =>
          i.quantity === null
            ? ''
            : i.quantity + (i.quantity_max === null ? '' : '–' + i.quantity_max),
        ),
      };
      if (alive.current) {
        const restored = draft?.value as EditorValue | undefined;
        setValue(
          restored
            ? {
                ...restored,
                nutritionRows:
                  restored.nutritionRows ??
                  Object.entries(restored.recipe.nutrition ?? {}).map(([name, value]) => ({
                    name,
                    value,
                  })),
              }
            : initial,
        );
        if (draft?.photo) {
          const imageID = (draft.value as EditorValue).recipe.image_id;
          if (imageID) setPhoto({ id: imageID, blob: draft.photo, pending: true });
        }
      }
    })().catch(() => setError('saveError'));
    return () => {
      alive.current = false;
    };
  }, [key, store]);
  useEffect(() => {
    if (!value) return;
    setDraftState(false);
    draftChain.current = draftChain.current
      .catch(() => undefined)
      .then(() => store.saveDraft(key, value, photo?.blob))
      .then(() => {
        if (alive.current) setDraftState(true);
      })
      .catch(() => {
        if (alive.current) setError('saveError');
      });
  }, [value, photo, key, store]);
  if (!value) return <div className="loading-state">{t('loading')}</div>;
  const recipe = value.recipe;
  const patch = (changes: Partial<Recipe>) =>
    setValue({ ...value, recipe: { ...recipe, ...changes } });
  const setIngredient = (index: number, changes: Partial<Recipe['ingredients'][number]>) =>
    patch({
      ingredients: recipe.ingredients.map((item, i) =>
        i === index ? { ...item, ...changes } : item,
      ),
    });
  const image = async (file: File | undefined) => {
    if (!file) return;
    try {
      if (!['image/jpeg', 'image/png'].includes(file.type) || file.size > 8 * 1024 * 1024)
        throw new Error();
      const bitmap = await createImageBitmap(file);
      if (bitmap.width * bitmap.height > 16_000_000) {
        bitmap.close();
        throw new Error();
      }
      bitmap.close();
      const id = uuid();
      setPhoto({ id, blob: file, pending: true });
      patch({ image_id: id });
      setError(null);
    } catch {
      setError('photoError');
    }
  };
  const save = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (
        value.nutritionRows &&
        new Set(value.nutritionRows.map((row) => row.name.trim())).size !==
          value.nutritionRows.length
      )
        throw new Error('invalid_nutrition');
      if (task && (!recipe.ingredients.length || !recipe.steps.length))
        throw new Error('incomplete_recipe');
      const normal = payload('recipe', {
        ...recipe,
        nutrition:
          value.nutritionRows === undefined
            ? recipe.nutrition
            : value.nutritionRows.length
              ? Object.fromEntries(
                  value.nutritionRows.map((row) => [row.name.trim(), row.value.trim()]),
                )
              : null,
        ingredients: recipe.ingredients.map((item, i) => ({
          ...item,
          ...parseQuantity(value.quantities[i] ?? ''),
        })),
      });
      await draftChain.current;
      await app.save([{ kind: 'recipe', id: value.id, value: normal }], {
        draft: key,
        photos: photo ? [photo] : [],
        importID: task?.id,
      });
      back();
    } catch (e) {
      setError(
        e instanceof Error && e.message === 'invalid_quantity' ? 'invalidQuantity' : 'saveError',
      );
    } finally {
      setSaving(false);
    }
  };
  const reorder = (from: number, to: number) => {
    const steps = [...recipe.steps];
    [steps[from], steps[to]] = [steps[to], steps[from]];
    const details = recipe.instruction_details ? [...recipe.instruction_details] : [];
    if (details.length) [details[from], details[to]] = [details[to], details[from]];
    patch({ steps, instruction_details: details });
  };
  return (
    <>
      <PageHeader
        title={task ? t('reviewImport') : entity ? t('edit') : t('newRecipe')}
        back={back}
      />
      {task && (
        <div className="info-note">
          <p>{t('reviewHint')}</p>
          {task.extraction?.issues.map((issue, index) => (
            <p key={index} className={issue.severity === 'error' ? 'error-note' : 'muted'}>
              {issue.message}
            </p>
          ))}
          {task.warnings?.map((warning) => (
            <p key={warning} className="muted">
              {t(
                (
                  {
                    review_ingredient_quantities: 'warningQuantities',
                    review_servings: 'warningServings',
                    image_import_not_yet_available: 'warningImage',
                    ingredient_entries_omitted: 'warningOmitted',
                    ingredient_text_truncated: 'warningTruncated',
                    video_first_ten_minutes: 'warningVideoLimit',
                  } as const
                )[warning as 'review_servings'] ?? 'warningUnknown',
              )}
            </p>
          ))}
        </div>
      )}
      <form onSubmit={(event) => void save(event)} className="recipe-editor">
        <div className="editor-main">
          <label>
            {t('title')}
            <input
              required
              maxLength={200}
              aria-invalid={task?.extraction?.recipe.title === null || undefined}
              value={recipe.title}
              onChange={(e) => patch({ title: e.target.value })}
            />
          </label>
          <label>
            {t('description')}
            <textarea
              maxLength={5000}
              rows={2}
              value={recipe.description}
              onChange={(e) => patch({ description: e.target.value })}
            />
          </label>
          <div className="form-row">
            <label>
              {t('servings')}
              <input
                required
                inputMode="decimal"
                type="number"
                min="0.01"
                max="1000000"
                step="any"
                aria-invalid={task?.extraction?.recipe.servings === null || undefined}
                value={recipe.servings}
                onChange={(e) => patch({ servings: e.target.value })}
              />
            </label>
            <label>
              {t('rating')}
              <select
                value={recipe.rating ?? ''}
                onChange={(e) => patch({ rating: e.target.value ? Number(e.target.value) : null })}
              >
                <option value="">{t('unrated')}</option>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n} / 5
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="form-row">
            {(['prepMinutes', 'cookMinutes', 'totalMinutes'] as const).map((name) => (
              <label key={name}>
                {t(name)}
                <input
                  type="number"
                  min={0}
                  max={525600}
                  step={1}
                  value={recipe.times?.[name] ?? ''}
                  onChange={(event) =>
                    patch({
                      times: {
                        ...recipe.times,
                        [name]: event.target.value === '' ? null : Number(event.target.value),
                      },
                    })
                  }
                />
              </label>
            ))}
          </div>
          <div className="form-row">
            <label>
              {t('recipeCategory')}
              <input
                maxLength={5000}
                value={recipe.category ?? ''}
                onChange={(event) => patch({ category: event.target.value || null })}
              />
            </label>
            <label>
              {t('recipeCuisine')}
              <input
                maxLength={5000}
                value={recipe.cuisine ?? ''}
                onChange={(event) => patch({ cuisine: event.target.value || null })}
              />
            </label>
          </div>
          <label>
            {t('photo')}
            <input
              type="file"
              accept="image/jpeg,image/png"
              onChange={(e) => void image(e.target.files?.[0])}
            />
            <small>{t('photoHint')}</small>
          </label>
          {recipe.image_id && !photo && <Photo id={recipe.image_id} className="editor-photo" />}
          {photo && (
            <p className="success-note">
              <Check size={16} />
              {t('photo')}
            </p>
          )}
          {recipe.image_id && (
            <button
              type="button"
              className="text-button"
              onClick={() => {
                setPhoto(undefined);
                patch({ image_id: null });
              }}
            >
              {t('remove')} {t('photo').toLocaleLowerCase()}
            </button>
          )}
          <section>
            <h2>{t('ingredients')}</h2>
            {recipe.ingredients.map((item, index) => (
              <fieldset className="ingredient-editor" key={item.id}>
                <legend className="sr-only">
                  {t('ingredient')} {index + 1}
                </legend>
                <div className="ingredient-editor-top">
                  <input
                    aria-label={`${t('ingredient')} ${index + 1}`}
                    required
                    maxLength={200}
                    placeholder={t('ingredient')}
                    value={item.name}
                    onChange={(e) => setIngredient(index, { name: e.target.value })}
                  />
                  <IconButton
                    label={`${t('remove')} ${t('ingredient')} ${index + 1}`}
                    onClick={() =>
                      setValue({
                        ...value,
                        recipe: {
                          ...recipe,
                          ingredients: recipe.ingredients.filter((_, i) => i !== index),
                        },
                        quantities: value.quantities.filter((_, i) => i !== index),
                      })
                    }
                  >
                    <X size={17} />
                  </IconButton>
                </div>
                <div className="form-row">
                  <label>
                    {t('quantity')}
                    <input
                      inputMode="decimal"
                      placeholder="½ / 200 / 2–3"
                      value={value.quantities[index] ?? ''}
                      onChange={(e) =>
                        setValue({
                          ...value,
                          quantities: value.quantities.map((q, i) =>
                            i === index ? e.target.value : q,
                          ),
                        })
                      }
                    />
                  </label>
                  <label>
                    {t('unit')}
                    <input
                      maxLength={30}
                      value={item.unit}
                      onChange={(e) => setIngredient(index, { unit: e.target.value })}
                    />
                  </label>
                </div>
                <label>
                  {t('preparation')}
                  <input
                    maxLength={300}
                    value={item.preparation}
                    onChange={(e) => setIngredient(index, { preparation: e.target.value })}
                  />
                </label>
                {item.original_text && (
                  <p className="muted">
                    {t('original')}: {item.original_text}
                  </p>
                )}
              </fieldset>
            ))}
            <AddButton
              onClick={() =>
                setValue({
                  ...value,
                  recipe: { ...recipe, ingredients: [...recipe.ingredients, emptyIngredient()] },
                  quantities: [...value.quantities, ''],
                })
              }
            >
              {t('addIngredient')}
            </AddButton>
          </section>
          <section>
            <h2>{t('instructions')}</h2>
            {recipe.steps.map((step, i) => (
              <div key={i} className="step-editor">
                <label>
                  {t('step')} {i + 1}
                  <textarea
                    required
                    maxLength={5000}
                    rows={3}
                    value={step}
                    onChange={(e) =>
                      patch({
                        steps: recipe.steps.map((value, index) =>
                          i === index ? e.target.value : value,
                        ),
                      })
                    }
                  />
                </label>
                <div className="step-actions">
                  <IconButton
                    label={`${t('moveUp')} ${i + 1}`}
                    disabled={i === 0}
                    onClick={() => reorder(i, i - 1)}
                  >
                    <ArrowUp size={17} />
                  </IconButton>
                  <IconButton
                    label={`${t('moveDown')} ${i + 1}`}
                    disabled={i === recipe.steps.length - 1}
                    onClick={() => reorder(i, i + 1)}
                  >
                    <ArrowDown size={17} />
                  </IconButton>
                  <IconButton
                    label={`${t('remove')} ${t('step')} ${i + 1}`}
                    onClick={() =>
                      patch({
                        steps: recipe.steps.filter((_, index) => i !== index),
                        instruction_details: recipe.instruction_details?.filter(
                          (_, index) => i !== index,
                        ),
                      })
                    }
                  >
                    <X size={17} />
                  </IconButton>
                </div>
              </div>
            ))}
            <AddButton
              onClick={() =>
                patch({
                  steps: [...recipe.steps, ''],
                  instruction_details: recipe.instruction_details?.length
                    ? [...recipe.instruction_details, {}]
                    : [],
                })
              }
            >
              {t('addStep')}
            </AddButton>
          </section>
          <label>
            {t('notes')}
            <textarea
              rows={3}
              maxLength={10000}
              value={recipe.notes}
              onChange={(e) => patch({ notes: e.target.value })}
            />
          </label>
          <details>
            <summary>{t('source')}</summary>
            <label>
              {t('sourceURL')}
              <input
                type="url"
                maxLength={2048}
                value={recipe.source_url ?? ''}
                onChange={(e) => patch({ source_url: e.target.value || null })}
              />
            </label>
            <label>
              {t('sourcePlatform')}
              <input
                maxLength={50}
                value={recipe.source_platform}
                onChange={(e) => patch({ source_platform: e.target.value })}
              />
            </label>
          </details>
          <details>
            <summary>{t('nutrition')}</summary>
            {(
              value.nutritionRows ??
              Object.entries(recipe.nutrition ?? {}).map(([name, value]) => ({ name, value }))
            ).map((row, index) => (
              <div className="nutrition-editor" key={index}>
                <div className="form-row">
                  <label>
                    {t('name')}
                    <input
                      required
                      maxLength={100}
                      value={row.name}
                      onChange={(e) =>
                        setValue({
                          ...value,
                          nutritionRows: (value.nutritionRows ?? []).map((r, i) =>
                            i === index ? { ...r, name: e.target.value } : r,
                          ),
                        })
                      }
                    />
                  </label>
                  <label>
                    {t('nutritionValue')}
                    <input
                      required
                      maxLength={10000}
                      value={row.value}
                      onChange={(e) =>
                        setValue({
                          ...value,
                          nutritionRows: (value.nutritionRows ?? []).map((r, i) =>
                            i === index ? { ...r, value: e.target.value } : r,
                          ),
                        })
                      }
                    />
                  </label>
                </div>
                <button
                  type="button"
                  className="text-button danger"
                  onClick={() =>
                    setValue({
                      ...value,
                      nutritionRows: value.nutritionRows?.filter((_, i) => i !== index),
                    })
                  }
                >
                  {t('remove')}
                </button>
              </div>
            ))}
            <AddButton
              onClick={() =>
                setValue({
                  ...value,
                  nutritionRows: [...(value.nutritionRows ?? []), { name: '', value: '' }],
                })
              }
            >
              {t('addNutrition')}
            </AddButton>
            <label>
              {t('nutritionSource')}
              <input
                maxLength={2048}
                value={recipe.nutrition_source ?? ''}
                onChange={(e) => patch({ nutrition_source: e.target.value || null })}
              />
            </label>
          </details>
        </div>
        <footer className="editor-footer">
          <p className="muted" role="status">
            {t(draftState ? 'draftSaved' : 'unsaved')}
          </p>
          {error && (
            <p className="error-note" role="alert">
              {t(error as 'saveError')}
            </p>
          )}
          <button className="primary" type="submit" disabled={saving}>
            {saving ? t('loading') : t('save')}
          </button>
        </footer>
      </form>
    </>
  );
}
