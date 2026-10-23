import { useEffect, useRef, useState } from 'react';
import {
  ArrowRight,
  Check,
  ChevronRight,
  ChevronLeft,
  Copy,
  Ellipsis,
  Leaf,
  Plus,
  Repeat2,
  Sparkles,
  Trash2,
  Upload,
  ShoppingBag,
  Pencil,
  GripVertical,
  Search,
  SlidersHorizontal,
} from 'lucide-react';
import Decimal from 'decimal.js';
import { useApp } from './model';
import { TemplateEditor } from './TemplateEditor';
import { Empty, IconButton, PageHeader, Photo, Sheet, WeekStrip } from './components';
import {
  addDays,
  amount,
  categories,
  displayDate,
  distance,
  monday,
  today,
  uuid,
} from './lib/domain';
import type { Category, Entity, Meal } from './lib/domain';
import {
  applyTemplate,
  availablePortions,
  changeOccurrence,
  copyMeals,
  makeTemplate,
  mealEdit,
  occurrences,
  suggestWeek,
} from './lib/planning';
import type { Occurrence, Suggestion } from './lib/planning';
import type { Edit } from './lib/store';
import { useMealDrag } from './useMealDrag';
import type { MealDragSource } from './useMealDrag';
export type PlanningTarget = {
  day: string;
  category: Category;
  recipeID?: string;
  leftoverID?: string;
};
export function MealRow({
  item,
  open,
  manage,
  drag,
}: {
  item: Occurrence;
  open: (id: string) => void;
  manage: (item: Occurrence) => void;
  drag?: ReturnType<typeof useMealDrag>;
}) {
  const { entities, t } = useApp();
  const meal = item.entity.payload;
  const recipe = entities('recipe').find((row) => row.id === meal.recipe_id);
  return (
    <div
      className={'meal-row' + (drag?.drag?.source.key === item.key ? ' is-drag-source' : '')}
      data-meal-id={item.entity.id}
      draggable={!drag?.disabled}
      onDragStart={(e) => {
        if ((e.target as Element).closest('.meal-drag-handle')) {
          e.preventDefault();
          return;
        }
        e.dataTransfer.setData(
          'application/mealf-meal',
          JSON.stringify({ id: item.entity.id, day: item.day }),
        );
        e.dataTransfer.effectAllowed = 'move';
      }}
    >
      <button className="meal-open" onClick={() => open(meal.recipe_id)}>
        <Photo id={recipe?.payload.image_id} />
        <span>
          <strong>{recipe?.payload.title ?? t('unavailableRecipe')}</strong>
          <small>
            {meal.servings} {t(Number(meal.servings) === 1 ? 'serving' : 'servingsText')}
            {meal.leftover_id && <> · {t('leftovers')}</>}
            {meal.recurrence && <Repeat2 size={12} />} {meal.cooked && <Check size={13} />}
          </small>
        </span>
      </button>
      {drag && (
        <button
          type="button"
          className="meal-drag-handle icon-button"
          aria-label={`${t('moveMeal')} · ${recipe?.payload.title ?? t('meals')}`}
          title={t('calendarDragHint')}
          disabled={drag.disabled}
          onContextMenu={(event) => event.preventDefault()}
          onPointerDown={(event) =>
            drag.begin(
              event,
              {
                id: item.entity.id,
                day: item.day,
                key: item.key,
                title: recipe?.payload.title ?? t('meals'),
              },
              () => manage(item),
            )
          }
          onClick={(event) => {
            if (!drag.consumeClick(item.key, event.detail)) manage(item);
          }}
        >
          <GripVertical size={19} />
        </button>
      )}
      <IconButton
        label={`${t('edit')} ${recipe?.payload.title ?? t('meals')}`}
        disabled={drag?.disabled}
        onClick={() => manage(item)}
      >
        <Ellipsis size={20} />
      </IconButton>
    </div>
  );
}
function BringStatus({ open }: { open: () => void }) {
  const app = useApp(),
    { t } = app;
  const [state, setState] = useState<string | null>(null);
  useEffect(() => {
    if (app.api)
      void app.api
        .request<{ state: string }>('/api/v1/integrations/bring/status')
        .then((value) => setState(value.state))
        .catch(() => setState('unknown'));
  }, [app.api]);
  const text = app.demo
    ? t('demo')
    : state === 'configured'
      ? t('bringConnected')
      : state === 'compatibility_unverified'
        ? t('bringUnverified')
        : state === 'not_configured'
          ? t('bringUnconfigured')
          : state === null
            ? t('loading')
            : t('notConnected');
  return (
    <button className="bring-status" onClick={open}>
      <ShoppingBag size={16} />
      <span>
        {t('shoppingTitle')} · {text}
      </span>
      <ChevronRight size={14} />
    </button>
  );
}
export function Home({
  pantrySetup,
  day,
  setDay,
  open,
  plan,
  manage,
  create,
  importRecipe,
  ideas,
  suggest,
  shopping,
}: {
  pantrySetup: () => void;
  day: string;
  setDay: (day: string) => void;
  open: (id: string) => void;
  plan: (target: PlanningTarget) => void;
  manage: (item: Occurrence) => void;
  create: () => void;
  importRecipe: () => void;
  ideas: () => void;
  suggest: () => void;
  shopping: () => void;
}) {
  const app = useApp(),
    { t } = app;
  const meals = app.entities('meal'),
    recipes = app.entities('recipe');
  const daily = occurrences(meals, day, day);
  const dinner = daily.find((item) => item.entity.payload.category === 'dinner');
  const featured = dinner && recipes.find((row) => row.id === dinner.entity.payload.recipe_id);
  const weekly = occurrences(meals, monday(day), addDays(monday(day), 6));
  const upcoming = occurrences(meals, addDays(day, 1), addDays(day, 14)).slice(0, 3);
  return (
    <>
      <PageHeader title={t('kitchen')} subtitle={t('homeIntro')}>
        <button
          className="primary compact"
          onClick={() => (recipes.length ? plan({ day, category: 'dinner' }) : create())}
        >
          <Plus size={18} />
          <span>{t(recipes.length ? 'homePlanAction' : 'addRecipe')}</span>
        </button>
      </PageHeader>
      {!app.demo && app.foodLoaded && !app.food.pantry_setup_done && (
        <section className="pantry-welcome" aria-label={t('pantryWelcomeTitle')}>
          <div>
            <h2>{t('pantryWelcomeTitle')}</h2>
            <p>{t('pantryWelcomeHint')}</p>
          </div>
          <button className="secondary" onClick={pantrySetup}>
            {t('pantryChooseBasics')}
            <ChevronRight size={18} />
          </button>
          <button
            className="text-button"
            onClick={() =>
              void app
                .saveFood({ pantry_setup_done: true })
                .catch(() => app.setError('storage_error'))
            }
          >
            {t('setupNotNow')}
          </button>
        </section>
      )}
      <div className="home-date-control" role="group" aria-label={t('date')}>
        <IconButton label={t('previousDay')} onClick={() => setDay(addDays(day, -1))}>
          <ChevronLeft size={20} />
        </IconButton>
        <strong>
          {displayDate(day, app.language, { weekday: 'long', day: 'numeric', month: 'short' })}
        </strong>
        <button
          className="text-button"
          onClick={() => setDay(today(app.household.timezone))}
          disabled={day === today(app.household.timezone)}
        >
          {t('goToday')}
        </button>
        <IconButton label={t('nextDay')} onClick={() => setDay(addDays(day, 1))}>
          <ChevronRight size={20} />
        </IconButton>
      </div>
      <div className="home-columns">
        <section className="today-section">
          <div className="section-heading">
            <h2>
              {day === today(app.household.timezone)
                ? t('todayMeals')
                : displayDate(day, app.language, {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'short',
                  })}
            </h2>
            <span className="muted">
              {daily.length} {t('meals').toLowerCase()}
            </span>
          </div>
          {featured?.payload.image_id && dinner && (
            <article className="featured-meal">
              <button className="featured-photo-button" onClick={() => open(featured.id)}>
                <Photo
                  id={featured.payload.image_id}
                  alt={app.demo ? t('photoIllustration') : featured.payload.title}
                />
              </button>
              <div className="featured-caption">
                <div>
                  <span className="meal-category">{t('dinner')}</span>
                  <h3>{featured.payload.title}</h3>
                  <button className="text-button" onClick={() => open(featured.id)}>
                    {t('viewRecipe')}
                    <ArrowRight size={16} />
                  </button>
                </div>
                <IconButton label={t('edit')} onClick={() => manage(dinner)}>
                  <Ellipsis size={22} />
                </IconButton>
              </div>
            </article>
          )}
          <div className="meal-slots">
            {categories.map((category) => {
              const items = daily.filter(
                (item) =>
                  item.entity.payload.category === category &&
                  !(featured?.payload.image_id && dinner?.key === item.key),
              );
              if (category === 'dinner' && featured?.payload.image_id && !items.length) return null;
              return (
                <div className="meal-slot" key={category}>
                  <div className="slot-heading">
                    <h3>{t(category)}</h3>
                    <IconButton
                      label={`${t('addMeal')} · ${t(category)}`}
                      onClick={() => plan({ day, category })}
                    >
                      <Plus size={19} />
                    </IconButton>
                  </div>
                  {items.map((item) => (
                    <MealRow key={item.key} item={item} open={open} manage={manage} />
                  ))}
                  {!items.length && (
                    <button className="empty-slot" onClick={() => plan({ day, category })}>
                      {t('plannedDayEmpty')}
                      <ChevronRight size={16} />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
          <section className="home-quick-actions" aria-label={t('homeQuickActions')}>
            <button className="secondary" aria-label={t('importRecipe')} onClick={importRecipe}>
              <Upload size={18} />
              {t('quickImport')}
            </button>
            {recipes.length > 0 && (
              <button className="secondary" aria-label={t('addRecipe')} onClick={create}>
                <Plus size={18} />
                {t('quickCreate')}
              </button>
            )}
            <button className="secondary" aria-label={t('recipeIdeas')} onClick={ideas}>
              <Sparkles size={18} />
              {t('quickIdeas')}
            </button>
          </section>
        </section>
        <aside className="home-aside">
          <section className="week-summary">
            <div className="section-heading">
              <h2>{t('yourWeek')}</h2>
              <span className="week-count">{weekly.length}</span>
            </div>
            <p>
              {weekly.length} {t('planned')}
            </p>
            <div
              className="week-progress"
              role="img"
              aria-label={`${weekly.length} ${t('planned')}`}
            >
              {Array.from({ length: 7 }, (_, i) => (
                <span
                  className={
                    weekly.some((item) => item.day === addDays(monday(day), i)) ? 'filled' : ''
                  }
                  key={i}
                />
              ))}
            </div>
            <button className="text-button" onClick={() => app.setTab('calendar')}>
              {t('calendar')}
              <ArrowRight size={16} />
            </button>
            <BringStatus open={shopping} />
          </section>
          <section className="suggestion-panel">
            <div>
              <h2>{t('suggestions')}</h2>
              <p>{t('suggestionsBody')}</p>
            </div>
            <button className="secondary" onClick={suggest}>
              <Sparkles size={18} />
              {t('suggest')}
            </button>
          </section>
          {upcoming.length > 0 && (
            <section className="section-block">
              <h2>{t('nextUp')}</h2>
              {upcoming.map((item) => (
                <div key={item.key}>
                  <p className="date-label">
                    {displayDate(item.day, app.language, {
                      weekday: 'short',
                      day: 'numeric',
                      month: 'short',
                    })}
                  </p>
                  <MealRow item={item} open={open} manage={manage} />
                </div>
              ))}
            </section>
          )}
        </aside>
      </div>
      {recipes.length > 0 && (
        <section className="section-block">
          <div className="section-heading">
            <h2>{t('favorites')}</h2>
            <button className="text-button" onClick={() => app.setTab('recipes')}>
              {t('all')}
              <ArrowRight size={16} />
            </button>
          </div>
          <div className="recipe-preview-list">
            {recipes
              .slice()
              .sort((a, b) => (b.payload.rating ?? 0) - (a.payload.rating ?? 0))
              .slice(0, 3)
              .map((recipe) => (
                <button className="recipe-preview" key={recipe.id} onClick={() => open(recipe.id)}>
                  <Photo id={recipe.payload.image_id} />
                  <span>
                    <strong>{recipe.payload.title}</strong>
                    <small>
                      {recipe.payload.servings}{' '}
                      {t(Number(recipe.payload.servings) === 1 ? 'serving' : 'servingsText')}
                    </small>
                  </span>
                  <ChevronRight size={17} />
                </button>
              ))}
          </div>
        </section>
      )}
    </>
  );
}
export function Calendar({
  day,
  setDay,
  open,
  plan,
  manage,
  suggest,
  shopping,
}: {
  day: string;
  setDay: (day: string) => void;
  open: (id: string) => void;
  plan: (target: PlanningTarget) => void;
  manage: (item: Occurrence) => void;
  suggest: () => void;
  shopping: () => void;
}) {
  const app = useApp(),
    { t } = app;
  const [tools, setTools] = useState(false),
    [error, setError] = useState<string | null>(null),
    [moving, setMoving] = useState(false);
  const [view, setView] = useState<'day' | 'three' | 'week'>(() =>
    matchMedia('(max-width:800px), (hover:none) and (pointer:coarse) and (max-height:500px)')
      .matches
      ? 'day'
      : 'week',
  );
  const grid = useRef<HTMLDivElement>(null);
  const busy = useRef(false);
  const preferenceChanged = useRef(false);
  useEffect(() => {
    let alive = true;
    void app.store
      .setting<string>('calendar:view', '')
      .then((saved) => {
        if (alive && !preferenceChanged.current && ['day', 'three', 'week'].includes(saved))
          setView(saved as typeof view);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [app.store]);
  const meals = app.entities('meal');
  const items = occurrences(meals, monday(day), addDays(monday(day), 6));
  const move = async (
    value: Pick<MealDragSource, 'id' | 'day'>,
    date: string,
    category: Category,
  ) => {
    if (busy.current) return;
    const source = items.find((item) => item.entity.id === value.id && item.day === value.day);
    if (!source) {
      setError(t('calendarMoveFailed'));
      return;
    }
    if (source.day === date && source.entity.payload.category === category) return;
    busy.current = true;
    setMoving(true);
    setError(null);
    try {
      await app.save(changeOccurrence(source, { date, category }));
    } catch {
      setError(t('calendarMoveFailed'));
    } finally {
      busy.current = false;
      setMoving(false);
    }
  };
  const drag = useMealDrag(
    grid,
    (source, target) => move(source, target.date, target.category),
    moving,
  );
  useEffect(() => {
    drag.cancel();
    const region = grid.current;
    const active = region?.querySelector<HTMLElement>('.active-day');
    if (region && active && view !== 'day') {
      const a = active.getBoundingClientRect(),
        b = region.getBoundingClientRect();
      if (a.left < b.left || a.right > b.right) region.scrollLeft += a.left - b.left;
    }
  }, [day, view]);
  const chooseView = (value: typeof view) => {
    preferenceChanged.current = true;
    setView(value);
    void app.store
      .setSetting('calendar:view', value)
      .catch(() => setError(t('calendarViewFailed')));
  };
  const start =
    view === 'day'
      ? day
      : view === 'three'
        ? addDays(monday(day), Math.min(distance(monday(day), day), 4))
        : monday(day);
  const dates = Array.from({ length: view === 'day' ? 1 : view === 'three' ? 3 : 7 }, (_, i) =>
    addDays(start, i),
  );
  const drop = async (e: React.DragEvent, date: string, category: Category) => {
    e.preventDefault();
    try {
      const value = JSON.parse(e.dataTransfer.getData('application/mealf-meal'));
      await move(value, date, category);
    } catch {
      setError(t('invalid'));
    }
  };
  return (
    <>
      <PageHeader title={t('calendar')}>
        <button className="primary compact" onClick={() => plan({ day, category: 'dinner' })}>
          <Plus size={18} />
          {t('homePlanAction')}
        </button>
      </PageHeader>
      <WeekStrip day={day} onChange={setDay} />
      <div className="calendar-toolbar">
        <div className="calendar-view-switch" role="group" aria-label={t('calendarView')}>
          {(['day', 'three', 'week'] as const).map((value) => (
            <button
              type="button"
              key={value}
              aria-pressed={view === value}
              onClick={() => chooseView(value)}
            >
              {t(
                value === 'day'
                  ? 'calendarDay'
                  : value === 'three'
                    ? 'calendarThreeDays'
                    : 'calendarWeek',
              )}
            </button>
          ))}
        </div>
        <button
          className="secondary compact calendar-tools"
          aria-label={t('weekTools')}
          onClick={() => setTools(true)}
        >
          <Ellipsis size={18} />
          {t('calendarToolsShort')}
        </button>
      </div>
      {error && (
        <p role="alert" className="error-note">
          {error}
        </p>
      )}
      <div className="calendar-week" data-view={view} ref={grid} aria-busy={moving}>
        {dates.map((date) => (
          <section className={'calendar-day ' + (date === day ? 'active-day' : '')} key={date}>
            <h2>
              <button onClick={() => setDay(date)}>
                {displayDate(date, app.language, { weekday: 'long' })}
                <span>{displayDate(date, app.language, { day: 'numeric', month: 'short' })}</span>
              </button>
            </h2>
            {categories.map((category) => (
              <div
                key={category}
                className={
                  'calendar-slot' +
                  (drag.drag?.target?.date === date && drag.drag.target.category === category
                    ? ' is-drop-target'
                    : '')
                }
                data-meal-slot=""
                data-date={date}
                data-category={category}
                onDragOver={(e) => {
                  if (e.dataTransfer.types.includes('application/mealf-meal')) e.preventDefault();
                }}
                onDrop={(e) => void drop(e, date, category)}
              >
                <div className="slot-heading">
                  <h3>{t(category)}</h3>
                  {items.some(
                    (item) => item.day === date && item.entity.payload.category === category,
                  ) && (
                    <IconButton
                      label={`${t('addMeal')} ${date} ${t(category)}`}
                      onClick={() => plan({ day: date, category })}
                    >
                      <Plus size={17} />
                    </IconButton>
                  )}
                </div>
                {items
                  .filter((item) => item.day === date && item.entity.payload.category === category)
                  .map((item) => (
                    <MealRow key={item.key} item={item} open={open} manage={manage} drag={drag} />
                  ))}
                {!items.some(
                  (item) => item.day === date && item.entity.payload.category === category,
                ) && (
                  <button className="calendar-add" onClick={() => plan({ day: date, category })}>
                    <Plus size={16} />
                    <span>{t('addMeal')}</span>
                  </button>
                )}
              </div>
            ))}
          </section>
        ))}
      </div>
      <div className="sr-only" role="status" aria-live="polite">
        {drag.drag &&
          `${t('moveMeal')} · ${drag.drag.source.title}${drag.drag.target ? ` · ${displayDate(drag.drag.target.date, app.language)} · ${t(drag.drag.target.category)}` : ''}`}
      </div>
      {drag.drag && (
        <div
          className="meal-drag-preview"
          aria-hidden="true"
          style={{
            left: Math.max(12, Math.min(innerWidth - 192, drag.drag.x - 90)),
            top: Math.max(12, Math.min(innerHeight - 64, drag.drag.y - 70)),
          }}
        >
          <GripVertical size={18} />
          {drag.drag.source.title}
        </div>
      )}
      <div className="calendar-bottom-actions">
        <button className="secondary" aria-label={t('suggest')} onClick={suggest}>
          <Sparkles size={17} />
          {t('suggest')}
        </button>
        <details className="calendar-help">
          <summary>
            {t('calendarDragHelp')}
            <ChevronRight size={16} />
          </summary>
          <p className="calendar-drag-hint">
            {t('calendarDragHint')}
            {view !== 'day' && <> {t('calendarScrollHint')}</>}
          </p>
        </details>
      </div>
      <button className="text-button calendar-shopping" onClick={shopping}>
        <ShoppingBag size={17} />
        {t('shoppingTitle')}
        <ChevronRight size={16} />
      </button>
      <Leftovers plan={plan} />
      {tools && <WeekTools day={day} onClose={() => setTools(false)} />}
    </>
  );
}
export function PlanMeal({ target, onClose }: { target: PlanningTarget; onClose: () => void }) {
  const app = useApp(),
    { t } = app;
  const recipes = app.entities('recipe');
  const [recipeID, setRecipe] = useState(target.recipeID ?? recipes[0]?.id ?? ''),
    [date, setDate] = useState(target.day),
    [category, setCategory] = useState(target.category),
    [servings, setServings] = useState(
      recipes.find((r) => r.id === target.recipeID)?.payload.servings ??
        recipes[0]?.payload.servings ??
        '2',
    );
  const [leftoverID, setLeftover] = useState(target.leftoverID ?? ''),
    [repeat, setRepeat] = useState('0'),
    [until, setUntil] = useState(addDays(target.day, 84)),
    [error, setError] = useState(false),
    [saving, setSaving] = useState(false);
  const [details, setDetails] = useState(Boolean(target.recipeID)),
    [query, setQuery] = useState(''),
    [visible, setVisible] = useState(20);
  const saveLock = useRef(false);
  const leftovers = app.entities('leftover').filter((row) => {
    if (row.payload.discarded) return false;
    try {
      return new Decimal(availablePortions(row, app.entities('meal'))).gt(0);
    } catch {
      return false; // Retain unsafe legacy records; the list below exposes the error.
    }
  });
  const defaultServings = (recipe: Entity<'recipe'>) =>
    app.planning.preferences.servings ?? recipe.payload.servings;
  const chooseDetails = (recipe: Entity<'recipe'>) => {
    setRecipe(recipe.id);
    setServings(defaultServings(recipe));
    setLeftover('');
    setError(false);
    setDetails(true);
  };
  const commit = async (
    id: string,
    portions: string,
    leftover: string | null,
    recurrence: Meal['recurrence'],
  ) => {
    if (saveLock.current) return;
    saveLock.current = true;
    setSaving(true);
    setError(false);
    try {
      const recipe = recipes.find((row) => row.id === id);
      if (!recipe) throw new Error();
      const edit = mealEdit(recipe, date, category);
      edit.value = {
        ...edit.value,
        servings: amount(portions),
        leftover_id: leftover,
        recurrence,
      };
      await app.save([edit]);
      app.setNotice('planAdded');
      onClose();
    } catch {
      setError(true);
    } finally {
      saveLock.current = false;
      setSaving(false);
    }
  };
  const save = (event: React.FormEvent) => {
    event.preventDefault();
    void commit(
      recipeID,
      servings,
      leftoverID || null,
      !leftoverID && repeat !== '0'
        ? { interval_weeks: Number(repeat), until, exceptions: [] }
        : null,
    );
  };
  const matches = recipes
    .filter((row) =>
      row.payload.title
        .toLocaleLowerCase(app.language)
        .includes(query.trim().toLocaleLowerCase(app.language)),
    )
    .sort(
      (a, b) =>
        (b.payload.rating ?? 0) - (a.payload.rating ?? 0) ||
        a.payload.title.localeCompare(b.payload.title, app.language),
    );
  return (
    <Sheet title={t('addMeal')} onClose={onClose} busy={saving}>
      {!recipes.length ? (
        <Empty title={t('emptyRecipes')} body={t('emptyRecipesBody')}>
          <button
            className="primary"
            onClick={() => {
              app.setTab('recipes');
              onClose();
            }}
          >
            {t('recipes')}
          </button>
        </Empty>
      ) : !details ? (
        <div className="meal-picker" aria-busy={saving}>
          <p className="meal-picker-context">
            {displayDate(date, app.language, { weekday: 'long', day: 'numeric', month: 'short' })} ·{' '}
            {t(category)}
          </p>
          <p className="meal-picker-hint">{t('planPickerHint')}</p>
          <label className="search-field">
            <Search size={19} aria-hidden="true" />
            <input
              type="search"
              aria-label={t('search')}
              placeholder={t('search')}
              value={query}
              disabled={saving}
              onChange={(event) => {
                setQuery(event.target.value);
                setVisible(20);
              }}
            />
          </label>
          {!query && leftovers.length > 0 && (
            <section className="meal-picker-leftovers" aria-label={t('planLeftoverList')}>
              <h3>{t('planLeftoverList')}</h3>
              {leftovers.map((row) => {
                const recipe = recipes.find((recipe) => recipe.id === row.payload.recipe_id);
                if (!recipe) return null;
                const remaining = availablePortions(row, app.entities('meal'));
                const portions = Decimal.min(defaultServings(recipe), remaining).toString();
                return (
                  <button
                    type="button"
                    key={row.id}
                    className="meal-leftover-choice"
                    disabled={saving}
                    onClick={() => {
                      setLeftover(row.id);
                      void commit(recipe.id, portions, row.id, null);
                    }}
                  >
                    <Leaf size={18} aria-hidden="true" />
                    <span>
                      <strong>{recipe.payload.title}</strong>
                      <small>
                        {portions} {t('portions')} · {t('leftovers')}
                      </small>
                    </span>
                    <Plus size={18} aria-hidden="true" />
                  </button>
                );
              })}
            </section>
          )}
          <h3>
            {!query && matches.some((row) => (row.payload.rating ?? 0) >= 4)
              ? t('planSuggested')
              : t('planRecipeList')}
          </h3>
          <div className="meal-picker-list">
            {matches.slice(0, visible).map((row) => {
              const minutes = row.payload.times?.totalMinutes;
              return (
                <div className="meal-choice" key={row.id}>
                  <button
                    type="button"
                    className="meal-choice-add"
                    aria-label={`${t('planRecipeAction')} · ${row.payload.title}`}
                    disabled={saving}
                    onClick={() => {
                      setLeftover('');
                      void commit(row.id, defaultServings(row), null, null);
                    }}
                  >
                    <Photo id={row.payload.image_id} />
                    <span>
                      <strong>{row.payload.title}</strong>
                      <small>
                        {defaultServings(row)} {t('servingsText')}
                        {minutes != null && (
                          <>
                            {' '}
                            · {minutes} {t('planMinutes')}
                          </>
                        )}
                      </small>
                    </span>
                    <Plus size={18} aria-hidden="true" />
                  </button>
                  <IconButton
                    label={`${t('planOptions')} · ${row.payload.title}`}
                    disabled={saving}
                    onClick={() => chooseDetails(row)}
                  >
                    <SlidersHorizontal size={19} />
                  </IconButton>
                </div>
              );
            })}
          </div>
          {!matches.length && (
            <p className="muted" role="status">
              {t('planNoMatches')}
            </p>
          )}
          {matches.length > visible && (
            <button
              type="button"
              className="text-button full"
              disabled={saving}
              onClick={() => setVisible((count) => count + 20)}
            >
              {t('planMoreRecipes')}
            </button>
          )}
          {error && (
            <p className="error-note" role="alert">
              {t(leftoverID ? 'insufficientLeftovers' : 'invalid')}
            </p>
          )}
        </div>
      ) : (
        <form onSubmit={(e) => void save(e)}>
          <button
            type="button"
            className="text-button picker-back"
            disabled={saving}
            onClick={() => setDetails(false)}
          >
            <ChevronLeft size={16} />
            {t('planDifferentRecipe')}
          </button>
          <fieldset className="meal-options-fields" disabled={saving}>
            <label>
              {t('chooseRecipe')}
              <select
                value={recipeID}
                onChange={(e) => {
                  setRecipe(e.target.value);
                  setLeftover('');
                  setServings(defaultServings(recipes.find((r) => r.id === e.target.value)!));
                }}
              >
                {recipes.map((row) => (
                  <option value={row.id} key={row.id}>
                    {row.payload.title}
                  </option>
                ))}
              </select>
            </label>
            <div className="form-row">
              <label>
                {t('date')}
                <input
                  type="date"
                  required
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </label>
              <label>
                {t('category')}
                <select value={category} onChange={(e) => setCategory(e.target.value as Category)}>
                  {categories.map((value) => (
                    <option key={value} value={value}>
                      {t(value)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              {t('servings')}
              <input
                type="number"
                required
                min="0.01"
                max="1000000"
                step="any"
                value={servings}
                onChange={(e) => setServings(e.target.value)}
              />
            </label>
            {leftovers.some((row) => row.payload.recipe_id === recipeID) && (
              <label>
                {t('leftovers')}
                <select
                  value={leftoverID}
                  onChange={(e) => {
                    setLeftover(e.target.value);
                    if (e.target.value) {
                      setRepeat('0');
                      setServings(
                        availablePortions(
                          leftovers.find((row) => row.id === e.target.value)!,
                          app.entities('meal'),
                        ),
                      );
                    }
                  }}
                >
                  <option value="">{t('addMeal')}</option>
                  {leftovers
                    .filter((row) => row.payload.recipe_id === recipeID)
                    .map((row) => (
                      <option key={row.id} value={row.id}>
                        {row.payload.produced_on} · {availablePortions(row, app.entities('meal'))}{' '}
                        {t('portions')}
                      </option>
                    ))}
                </select>
                <small>{t('leftoverHint')}</small>
              </label>
            )}
            {!leftoverID && (
              <>
                <label>
                  {t('repeat')}
                  <select value={repeat} onChange={(e) => setRepeat(e.target.value)}>
                    <option value="0">{t('noRepeat')}</option>
                    {[1, 2, 3, 4].map((n) => (
                      <option key={n} value={n}>
                        {n} {t('weeks')}
                      </option>
                    ))}
                  </select>
                </label>
                {repeat !== '0' && (
                  <label>
                    {t('until')}
                    <input
                      type="date"
                      required
                      min={date}
                      max={addDays(date, 3660)}
                      value={until}
                      onChange={(e) => setUntil(e.target.value)}
                    />
                  </label>
                )}
              </>
            )}
            {error && (
              <p className="error-note" role="alert">
                {t(leftoverID ? 'insufficientLeftovers' : 'invalid')}
              </p>
            )}
            <button className="primary full" disabled={saving}>
              {t('save')}
            </button>
          </fieldset>
        </form>
      )}
    </Sheet>
  );
}
export function ManageMeal({ item, onClose }: { item: Occurrence; onClose: () => void }) {
  const app = useApp(),
    { t } = app;
  const meal = item.entity.payload;
  const recipe = app.entities('recipe').find((row) => row.id === meal.recipe_id);
  const [date, setDate] = useState(item.day),
    [category, setCategory] = useState(meal.category),
    [servings, setServings] = useState(meal.servings),
    [portions, setPortions] = useState('2'),
    [leftover, setLeftover] = useState(false),
    [error, setError] = useState(false),
    [busy, setBusy] = useState(false);
  const [interval, setIntervalWeeks] = useState(meal.recurrence?.interval_weeks ?? 1),
    [until, setUntil] = useState(meal.recurrence?.until ?? item.day),
    [deleteSeries, setDeleteSeries] = useState(false);
  const commit = async (edits: Edit[]) => {
    setBusy(true);
    try {
      await app.save(edits);
      onClose();
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };
  const save = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const changes: Partial<Meal> = { date, category, servings: amount(servings) };
      void commit(changeOccurrence(item, changes));
    } catch {
      setError(true);
    }
  };
  return (
    <Sheet title={recipe?.payload.title ?? t('meals')} onClose={onClose}>
      <form onSubmit={save}>
        <div className="form-row">
          <label>
            {t('date')}
            <input type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
          </label>
          <label>
            {t('category')}
            <select value={category} onChange={(e) => setCategory(e.target.value as Category)}>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {t(category)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label>
          {t('servings')}
          <input
            type="number"
            required
            min="0.01"
            step="any"
            max="1000000"
            value={servings}
            onChange={(e) => setServings(e.target.value)}
          />
        </label>
        {meal.recurrence && <p className="muted">{t('recurrenceHint')}</p>}
        <button className="primary full" disabled={busy}>
          {t('save')}
        </button>
      </form>
      <div className="action-list">
        <button
          onClick={() => void commit(changeOccurrence(item, { cooked: !meal.cooked }))}
          disabled={busy}
        >
          <Check size={18} />
          {t(meal.cooked ? 'uncook' : 'cooked')}
        </button>
        {!meal.leftover_id && (
          <button
            onClick={() =>
              void commit([
                {
                  kind: 'meal',
                  id: uuid(),
                  value: { ...meal, date, category, servings, recurrence: null, cooked: false },
                },
              ])
            }
            disabled={busy}
          >
            <Copy size={18} />
            {t('copyMeal')}
          </button>
        )}
        <button onClick={() => setLeftover(!leftover)}>
          <Leaf size={18} />
          {t('addLeftovers')}
        </button>
        <button
          className="danger"
          onClick={() => void commit(changeOccurrence(item, null))}
          disabled={busy}
        >
          <Trash2 size={18} />
          {t('remove')}
        </button>
      </div>
      {meal.recurrence && (
        <details>
          <summary>{t('series')}</summary>
          <label>
            {t('repeat')}
            <input
              type="number"
              min="1"
              max="52"
              value={interval}
              onChange={(e) => setIntervalWeeks(Number(e.target.value))}
            />
          </label>
          <label>
            {t('until')}
            <input
              type="date"
              min={meal.date}
              max={addDays(meal.date, 3660)}
              value={until}
              onChange={(e) => setUntil(e.target.value)}
            />
          </label>
          <button
            className="secondary full"
            disabled={busy}
            onClick={() =>
              void commit([
                {
                  kind: 'meal',
                  id: item.entity.id,
                  value: {
                    ...meal,
                    recurrence: { ...meal.recurrence!, interval_weeks: interval, until },
                  },
                },
              ])
            }
          >
            {t('saveSeries')}
          </button>
          <button className="text-button danger" onClick={() => setDeleteSeries(true)}>
            {t('removeSeries')}
          </button>
          {deleteSeries && (
            <div className="error-note">
              <p>{t('confirmRemoveSeries')}</p>
              <button
                className="text-button danger"
                disabled={busy}
                onClick={() =>
                  void commit([{ kind: 'meal', id: item.entity.id, value: meal, deleted: true }])
                }
              >
                {t('removeSeries')}
              </button>
            </div>
          )}
        </details>
      )}
      {leftover && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            try {
              void commit([
                ...changeOccurrence(item, { cooked: true }),
                {
                  kind: 'leftover',
                  id: uuid(),
                  value: {
                    recipe_id: meal.recipe_id,
                    produced_on: item.day,
                    portions: amount(portions),
                    discarded: false,
                  },
                },
              ]);
            } catch {
              setError(true);
            }
          }}
        >
          <label>
            {t('portions')}
            <input
              type="number"
              min="0.01"
              max="1000000"
              step="any"
              required
              value={portions}
              onChange={(e) => setPortions(e.target.value)}
            />
          </label>
          <button className="secondary full" disabled={busy}>
            {t('addLeftovers')}
          </button>
        </form>
      )}
      {error && (
        <p className="error-note" role="alert">
          {t('invalid')}
        </p>
      )}
    </Sheet>
  );
}
function Leftovers({ plan }: { plan: (target: PlanningTarget) => void }) {
  const app = useApp(),
    { t } = app;
  const meals = app.entities('meal');
  const leftovers = app.entities('leftover').filter((row) => !row.payload.discarded);
  return (
    <section className="section-block leftovers-section">
      <h2>{t('leftovers')}</h2>
      <p className="muted">{t(leftovers.length ? 'leftoverHint' : 'noLeftovers')}</p>
      {leftovers.map((row) => {
        const recipe = app.entities('recipe').find((r) => r.id === row.payload.recipe_id);
        let portions: string;
        try {
          portions = availablePortions(row, meals);
        } catch {
          return (
            <p className="error-note" role="alert" key={row.id}>
              {recipe?.payload.title ?? t('leftovers')}: {t('invalid')}
            </p>
          );
        }
        return (
          <div className="settings-row" key={row.id}>
            <div>
              <strong>{recipe?.payload.title ?? t('unavailableRecipe')}</strong>
              <small>
                {portions} {t('portions')} · {row.payload.produced_on}
              </small>
            </div>
            <button
              className="secondary"
              disabled={new Decimal(portions).lte(0)}
              onClick={() =>
                plan({
                  day: today(app.household.timezone),
                  category: 'dinner',
                  recipeID: row.payload.recipe_id,
                  leftoverID: row.id,
                })
              }
            >
              {t('addMeal')}
            </button>
            {new Decimal(portions).eq(row.payload.portions) && (
              <IconButton
                label={t('discard')}
                onClick={() => {
                  void app
                    .save([
                      { kind: 'leftover', id: row.id, value: { ...row.payload, discarded: true } },
                    ])
                    .catch(() => app.setNotice('invalid'));
                }}
              >
                <Trash2 size={17} />
              </IconButton>
            )}
          </div>
        );
      })}
    </section>
  );
}
function WeekTools({ day, onClose }: { day: string; onClose: () => void }) {
  const app = useApp(),
    { t } = app;
  const [destination, setDestination] = useState(addDays(day, 7)),
    [name, setName] = useState(''),
    [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Entity<'template'> | null>(null);
  const items = occurrences(app.entities('meal'), monday(day), addDays(monday(day), 6));
  const run = async (work: () => Edit[]) => {
    try {
      const edits = work();
      if (!edits.length) return;
      await app.save(edits);
      onClose();
    } catch (e) {
      setError(
        e instanceof Error && /contains_leftovers/.test(e.message)
          ? t('noCopyLeftovers')
          : t('invalid'),
      );
    }
  };
  if (editing) return <TemplateEditor template={editing} onClose={() => setEditing(null)} />;
  return (
    <Sheet title={t('weekTools')} onClose={onClose}>
      <label>
        {t('targetDate')}
        <input
          type="date"
          required
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
        />
      </label>
      <div className="action-list">
        <button
          onClick={() =>
            void run(() =>
              copyMeals(
                items.filter((i) => i.day === day),
                distance(day, destination),
              ),
            )
          }
        >
          <Copy size={17} />
          {t('copyDay')}
        </button>
        <button
          onClick={() =>
            void run(() => copyMeals(items, distance(monday(day), monday(destination))))
          }
        >
          <Copy size={17} />
          {t('copyWeek')}
        </button>
      </div>
      <h3>{t('templates')}</h3>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void run(() => [{ kind: 'template', id: uuid(), value: makeTemplate(items, name) }]);
        }}
      >
        <label>
          {t('templateName')}
          <input required maxLength={100} value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <button className="secondary full" disabled={!items.length}>
          {t('saveTemplate')}
        </button>
      </form>
      {app.entities('template').map((row) => (
        <div className="settings-row template-row" key={row.id}>
          <strong>{row.payload.name}</strong>
          <IconButton
            label={`${t('editTemplate')} ${row.payload.name}`}
            onClick={() => setEditing(row)}
          >
            <Pencil size={16} />
          </IconButton>
          <button
            className="text-button"
            onClick={() => void run(() => applyTemplate(row.payload, day, app.entities('recipe')))}
          >
            {t('applyTemplate')}
          </button>
          <IconButton
            label={t('delete')}
            onClick={() =>
              void run(() => [{ kind: 'template', id: row.id, value: row.payload, deleted: true }])
            }
          >
            <Trash2 size={16} />
          </IconButton>
        </div>
      ))}
      {error && (
        <p role="alert" className="error-note">
          {error}
        </p>
      )}
    </Sheet>
  );
}
export function Suggestions({ day, onClose }: { day: string; onClose: () => void }) {
  const app = useApp(),
    { t } = app;
  const [seed, setSeed] = useState(0),
    [error, setError] = useState(false);
  const approving = useRef(false);
  const [busy, setBusy] = useState(false);
  const [chosen, setChosen] = useState<Set<string> | null>(null);
  const suggestions = suggestWeek(app.rows, day, seed, app.planning);
  const key = (item: Suggestion) => item.date + item.category + item.recipeID;
  const approve = async () => {
    if (approving.current) return;
    approving.current = true;
    setBusy(true);
    try {
      const live = occurrences(
        await app.store.entities('meal'),
        monday(day),
        addDays(monday(day), 6),
      );
      const selected = suggestions.filter((item) => !chosen || chosen.has(key(item)));
      if (
        selected.some((item) =>
          live.some(
            (existing) =>
              existing.day === item.date && existing.entity.payload.category === item.category,
          ),
        )
      )
        throw new Error();
      await app.save(
        selected.map((item) => ({
          kind: 'meal',
          id: uuid(),
          value: {
            recipe_id: item.recipeID,
            date: item.date,
            category: item.category,
            servings: item.servings,
            leftover_id: item.leftoverID,
            cooked: false,
            order: 0,
            recurrence: null,
          },
        })),
        { suggestion: { request_id: uuid(), monday: monday(day), basis: null } },
      );
      onClose();
    } catch {
      setError(true);
    } finally {
      approving.current = false;
      setBusy(false);
    }
  };
  return (
    <Sheet
      title={t('suggestions')}
      busy={busy}
      onClose={() => {
        if (!approving.current) onClose();
      }}
    >
      <p>{t('suggestionsBody')}</p>
      {!suggestions.length ? (
        <p className="empty-inline">{t('noSuggestions')}</p>
      ) : (
        <div className="suggestion-list">
          {suggestions.map((item) => {
            const recipe = app.entities('recipe').find((r) => r.id === item.recipeID);
            return (
              <label className="suggestion-row" key={key(item)}>
                <input
                  type="checkbox"
                  disabled={busy}
                  checked={!chosen || chosen.has(key(item))}
                  onChange={(e) => {
                    const next = new Set(chosen ?? suggestions.map(key));
                    if (e.target.checked) next.add(key(item));
                    else next.delete(key(item));
                    setChosen(next);
                  }}
                />
                <Photo id={recipe?.payload.image_id} />
                <span>
                  <small>
                    {displayDate(item.date, app.language, { weekday: 'long' })} · {t(item.category)}
                  </small>
                  <strong>{recipe?.payload.title}</strong>
                  <small>
                    {item.servings}{' '}
                    {t(new Decimal(item.servings).eq(1) ? 'serving' : 'servingsText')}
                  </small>
                  <small>
                    {t(
                      (
                        {
                          leftovers: 'reasonLeftovers',
                          accepted: 'reasonAccepted',
                          new: 'reasonNew',
                          rated: 'reasonRated',
                          variety: 'reasonVariety',
                        } as const
                      )[item.reason],
                    )}
                  </small>
                </span>
              </label>
            );
          })}
        </div>
      )}
      {error && (
        <p role="alert" className="error-note">
          {t('planningApplyError')}
        </p>
      )}
      <div className="form-actions">
        <button
          className="secondary"
          disabled={busy}
          onClick={() => {
            setSeed(seed + 1);
            setChosen(null);
          }}
        >
          {t('regenerate')}
        </button>
        <button
          className="primary"
          disabled={busy || !suggestions.length || chosen?.size === 0}
          onClick={() => void approve()}
        >
          {t('approve')}
        </button>
      </div>
    </Sheet>
  );
}
