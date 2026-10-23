import { useEffect, useId, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { ArrowLeft, ChevronLeft, ChevronRight, CookingPot, Plus, X } from 'lucide-react';
import { useApp } from './model';
import { addDays, displayDate, monday, today } from './lib/domain';
import { occurrences } from './lib/planning';
export function IconButton({
  label,
  children,
  onClick,
  disabled = false,
}: {
  label: string;
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      className="icon-button"
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
    >
      {children}
    </button>
  );
}
export function PageHeader({
  title,
  subtitle,
  children,
  back,
}: {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  back?: () => void;
}) {
  const { t } = useApp();
  return (
    <header className="page-header">
      <div>
        {back && (
          <button className="back-link" onClick={back}>
            <ArrowLeft size={18} />
            {t('back')}
          </button>
        )}
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {children && <div className="header-actions">{children}</div>}
    </header>
  );
}
export function Empty({
  title,
  body,
  children,
}: {
  title: string;
  body?: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <CookingPot size={30} strokeWidth={1.4} aria-hidden="true" />
      <h2>{title}</h2>
      {body && <p>{body}</p>}
      {children}
    </div>
  );
}
export function Photo({
  id,
  className = '',
  alt = '',
  placeholder = true,
}: {
  id: string | null | undefined;
  className?: string;
  alt?: string;
  placeholder?: boolean;
}) {
  const { store, api } = useApp();
  const [url, setURL] = useState<string | null>(null);
  useEffect(() => {
    let alive = true,
      objectURL: string | null = null;
    setURL(null);
    if (id)
      void (async () => {
        let photo = await store.photo(id);
        if (!photo && api && navigator.onLine) {
          try {
            photo = { id, blob: await api.media(id), pending: false };
            try {
              await store.cachePhoto(photo);
            } catch {
              /* Display the downloaded image even when browser caching is full. */
            }
          } catch {
            return;
          }
        }
        if (photo && alive) {
          objectURL = URL.createObjectURL(photo.blob);
          setURL(objectURL);
        }
      })().catch(() => undefined);
    return () => {
      alive = false;
      if (objectURL) URL.revokeObjectURL(objectURL);
    };
  }, [id, store, api]);
  return url ? (
    <img
      className={'food-photo ' + className}
      src={url}
      alt={alt}
      loading="lazy"
      onError={() => setURL(null)}
    />
  ) : placeholder ? (
    <div className={'photo-placeholder ' + className} aria-hidden="true">
      <img
        className="recipe-placeholder-mark"
        src="/app/brand/peach-v1.png"
        alt=""
        draggable={false}
      />
    </div>
  ) : null;
}
export function WeekStrip({ day, onChange }: { day: string; onChange: (day: string) => void }) {
  const { t, language, household, entities } = useApp();
  const week = monday(day);
  const planned = new Set(
    occurrences(entities('meal'), week, addDays(week, 6)).map((item) => item.day),
  );
  return (
    <div className="week-control">
      <div className="week-heading">
        <IconButton label={t('weekBefore')} onClick={() => onChange(addDays(day, -7))}>
          <ChevronLeft size={20} />
        </IconButton>
        <span>{displayDate(week, language, { month: 'long', year: 'numeric' })}</span>
        <button
          className="text-button week-today"
          onClick={() => onChange(today(household.timezone))}
        >
          {t('goToday')}
        </button>
        <IconButton label={t('weekAfter')} onClick={() => onChange(addDays(day, 7))}>
          <ChevronRight size={20} />
        </IconButton>
      </div>
      <div className="week-strip" role="group" aria-label={t('calendar')}>
        {Array.from({ length: 7 }, (_, i) => addDays(week, i)).map((date) => (
          <button
            key={date}
            onClick={() => onChange(date)}
            aria-pressed={date === day}
            aria-label={
              displayDate(date, language, {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
              }) +
              ' · ' +
              t(planned.has(date) ? 'plannedDay' : 'unplannedDay')
            }
            className={date === day ? 'selected' : ''}
          >
            <span>{displayDate(date, language, { weekday: 'short' })}</span>
            <strong>{date.slice(8)}</strong>
            <span
              className={'day-dot' + (planned.has(date) ? ' is-planned' : '')}
              aria-hidden="true"
            />
          </button>
        ))}
      </div>
    </div>
  );
}
export function Sheet({
  title,
  children,
  onClose,
  busy = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  busy?: boolean;
}) {
  const { t } = useApp();
  const ref = useRef<HTMLDialogElement>(null);
  const titleID = useId();
  useEffect(() => {
    const el = ref.current;
    const opener = document.activeElement as HTMLElement | null;
    el?.showModal();
    return () => {
      el?.close();
      if (opener?.isConnected) opener.focus();
    };
  }, []);
  return (
    <dialog
      aria-labelledby={titleID}
      aria-busy={busy || undefined}
      ref={ref}
      className="sheet"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className="sheet-heading">
        <h2 id={titleID}>{title}</h2>
        <IconButton label={t('close')} onClick={onClose} disabled={busy}>
          <X size={20} />
        </IconButton>
      </div>
      {children}
    </dialog>
  );
}
export function AddButton({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return (
    <button className="add-button" onClick={onClick}>
      <Plus size={18} />
      {children}
    </button>
  );
}
export function safeURL(value: string | null | undefined): string | undefined {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}
