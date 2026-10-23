import { useId, useState } from 'react';
import { useApp } from './model';
import { RECIPE_UNITS, suggestIngredients } from './lib/ingredient-options';
import type { IngredientOption } from './lib/ingredient-options';

export function IngredientName({
  value,
  onChange,
  label,
  options,
}: {
  value: string;
  onChange: (name: string) => void;
  label: string;
  options: IngredientOption[];
}) {
  const { t } = useApp();
  const id = useId();
  const [focused, setFocused] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [active, setActive] = useState(-1);
  const matches = suggestIngredients(options, value);
  const open = focused && !dismissed && matches.length > 0;
  const choose = (name: string) => {
    onChange(name);
    setDismissed(true);
    setActive(-1);
  };
  return (
    <div
      className="ingredient-name-field"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setFocused(false);
          setActive(-1);
        }
      }}
    >
      <input
        role="combobox"
        aria-label={label}
        aria-autocomplete="list"
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        aria-activedescendant={open && active >= 0 ? `${id}-${active}` : undefined}
        autoComplete="off"
        required
        maxLength={200}
        placeholder={t('ingredient')}
        value={value}
        onFocus={() => {
          setFocused(true);
          setDismissed(false);
        }}
        onChange={(event) => {
          onChange(event.target.value);
          setActive(-1);
          setDismissed(false);
        }}
        onKeyDown={(event) => {
          if (event.key === 'Escape' && open) {
            event.preventDefault();
            event.stopPropagation();
            setDismissed(true);
          } else if (matches.length && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
            event.preventDefault();
            setDismissed(false);
            setActive((current) =>
              event.key === 'ArrowDown'
                ? (current + 1) % matches.length
                : current <= 0
                  ? matches.length - 1
                  : current - 1,
            );
          } else if (event.key === 'Enter' && open && active >= 0) {
            event.preventDefault();
            choose(matches[active].name);
          }
        }}
      />
      {open && (
        <div
          id={id}
          role="listbox"
          aria-label={t('ingredientSuggestions')}
          className="ingredient-suggestions"
        >
          {matches.map((option, index) => (
            <button
              type="button"
              role="option"
              aria-selected={index === active}
              id={`${id}-${index}`}
              key={option.name}
              tabIndex={-1}
              onPointerDown={(event) => event.preventDefault()}
              onClick={() => choose(option.name)}
            >
              <span>{option.name}</span>
              <small>{t(option.pantry ? 'pantry' : 'recipes')}</small>
            </button>
          ))}
        </div>
      )}
      {focused && !dismissed && value.trim() && !matches.length && (
        <p className="ingredient-new-hint" role="status">
          {t('ingredientNewName')}
        </p>
      )}
    </div>
  );
}

export function IngredientUnit({
  value,
  onChange,
}: {
  value: string;
  onChange: (unit: string) => void;
}) {
  const { t, language } = useApp();
  const known = RECIPE_UNITS.some(([unit]) => unit === value);
  const [custom, setCustom] = useState(!known);
  return (
    <div className="ingredient-unit-field">
      <label>
        {t('unit')}
        <select
          aria-label={t('unit')}
          value={custom || !known ? '__custom' : value}
          onChange={(event) => {
            const next = event.target.value;
            setCustom(next === '__custom');
            if (next !== '__custom') onChange(next);
          }}
        >
          {RECIPE_UNITS.map(([unit, en, de]) => (
            <option key={unit} value={unit}>
              {language === 'de' ? de : en}
            </option>
          ))}
          <option value="__custom">{t('unitCustom')}</option>
        </select>
      </label>
      {(custom || !known) && (
        <label>
          {t('unitCustomName')}
          <input maxLength={30} value={value} onChange={(event) => onChange(event.target.value)} />
        </label>
      )}
    </div>
  );
}
