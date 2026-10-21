import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { useApp } from './model';
import { IconButton, Sheet } from './components';
import { addDays, amount, categories, displayDate, payload, uuid } from './lib/domain';
import type { Category, Entity, Template } from './lib/domain';

type Slot = Template['meals'][number] & { key: string };
export function TemplateEditor({
  template,
  onClose,
}: {
  template: Entity<'template'>;
  onClose: () => void;
}) {
  const app = useApp(),
    { t } = app;
  const recipes = app.entities('recipe');
  const [name, setName] = useState(template.payload.name);
  const [slots, setSlots] = useState<Slot[]>(() =>
    template.payload.meals.map((slot) => ({ ...slot, key: uuid() })),
  );
  const [saving, setSaving] = useState(false),
    [error, setError] = useState<string | null>(null);
  const update = (key: string, changes: Partial<Slot>) => {
    setError(null);
    setSlots((rows) => rows.map((row) => (row.key === key ? { ...row, ...changes } : row)));
  };
  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    if (saving) return;
    setError(null);
    if (slots.some((slot) => !recipes.some((recipe) => recipe.id === slot.recipe_id))) {
      setError(t('templateMissingRecipe'));
      return;
    }
    let value: Template;
    try {
      value = payload('template', {
        name,
        meals: slots.map(({ key: _key, ...slot }) => ({
          ...slot,
          servings: amount(slot.servings.trim().replace(',', '.')),
        })),
      });
    } catch {
      setError(t('invalidTemplate'));
      return;
    }
    setSaving(true);
    try {
      await app.save([{ kind: 'template', id: template.id, value }]);
      onClose();
    } catch {
      setError(t('storageError'));
    } finally {
      setSaving(false);
    }
  };
  return (
    <Sheet title={t('editTemplate')} onClose={onClose}>
      <p className="muted template-hint">{t('templateEditHint')}</p>
      <form onSubmit={(event) => void save(event)}>
        <fieldset disabled={saving} className="template-fields">
          <label>
            {t('templateName')}
            <input
              required
              maxLength={100}
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError(null);
              }}
            />
          </label>
          {slots.map((slot, index) => (
            <fieldset className="template-slot" key={slot.key}>
              <legend>
                {t('templateMeal')} {index + 1}
              </legend>
              <div className="template-slot-grid">
                <label>
                  {t('weekday')}
                  <select
                    value={slot.weekday}
                    onChange={(e) => update(slot.key, { weekday: Number(e.target.value) })}
                  >
                    {Array.from({ length: 7 }, (_, i) => (
                      <option key={i} value={i}>
                        {displayDate(addDays('2000-01-03', i), app.language, { weekday: 'long' })}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  {t('mealCategory')}
                  <select
                    value={slot.category}
                    onChange={(e) => update(slot.key, { category: e.target.value as Category })}
                  >
                    {categories.map((category) => (
                      <option key={category} value={category}>
                        {t(category)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <label>
                {t('templateRecipe')}
                <select
                  required
                  value={slot.recipe_id}
                  onChange={(e) => {
                    const recipe = recipes.find((row) => row.id === e.target.value);
                    if (recipe)
                      update(slot.key, { recipe_id: recipe.id, servings: recipe.payload.servings });
                  }}
                >
                  {!recipes.some((recipe) => recipe.id === slot.recipe_id) && (
                    <option value={slot.recipe_id} disabled>
                      {t('unavailableRecipe')}
                    </option>
                  )}
                  {recipes.map((recipe) => (
                    <option key={recipe.id} value={recipe.id}>
                      {recipe.payload.title}
                    </option>
                  ))}
                </select>
              </label>
              <div className="template-slot-grid">
                <label>
                  {t('servings')}
                  <input
                    required
                    maxLength={30}
                    inputMode="decimal"
                    value={slot.servings}
                    onChange={(e) => update(slot.key, { servings: e.target.value })}
                  />
                </label>
                <IconButton
                  label={`${t('removeTemplateMeal')} ${index + 1}`}
                  onClick={() => setSlots((rows) => rows.filter((row) => row.key !== slot.key))}
                >
                  <Trash2 size={18} />
                </IconButton>
              </div>
            </fieldset>
          ))}
          <button
            type="button"
            className="add-button"
            disabled={!recipes.length || slots.length >= 100}
            onClick={() => {
              const recipe = recipes[0];
              if (recipe)
                setSlots((rows) => [
                  ...rows,
                  {
                    key: uuid(),
                    weekday: 0,
                    category: 'dinner',
                    recipe_id: recipe.id,
                    servings: recipe.payload.servings,
                  },
                ]);
            }}
          >
            <Plus size={18} />
            {t('addTemplateMeal')}
          </button>
          {error && (
            <p role="alert" className="error-note">
              {error}
            </p>
          )}
          <div className="form-actions">
            <button type="button" className="secondary" onClick={onClose}>
              {t('cancel')}
            </button>
            <button className="primary" disabled={!name.trim()}>
              {t('save')}
            </button>
          </div>
        </fieldset>
      </form>
    </Sheet>
  );
}
