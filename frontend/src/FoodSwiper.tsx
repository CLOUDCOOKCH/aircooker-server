import { useEffect, useRef, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Bean,
  Beef,
  Carrot,
  Check,
  CookingPot,
  Fish,
  Flame,
  Heart,
  Milk,
  Salad,
  Soup,
  Sprout,
  Wheat,
  X,
} from 'lucide-react';
import { useApp } from './model';
import { PageHeader } from './components';
import { TASTE_FOODS, parseFoodPatch } from './lib/food';

const DRAFT = 'food:taste-draft:v1';
type Draft = { index: number; likes: string[]; dislikes: string[] };
const icons: Record<string, typeof CookingPot> = {
  bean: Bean,
  beef: Beef,
  carrot: Carrot,
  fish: Fish,
  flame: Flame,
  milk: Milk,
  salad: Salad,
  soup: Soup,
  sprout: Sprout,
  wheat: Wheat,
  chicken: CookingPot,
  'cooking-pot': CookingPot,
};
export function FoodSwiper({ back, done }: { back: () => void; done: () => void }) {
  const app = useApp(),
    { t } = app;
  const [draft, setDraft] = useState<Draft>({
      index: 0,
      likes: app.food.likes,
      dislikes: app.food.dislikes,
    }),
    [ready, setReady] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(false),
    [offset, setOffset] = useState(0);
  const lock = useRef(false),
    gesture = useRef<{ id: number; x: number; y: number } | null>(null);
  useEffect(() => {
    let alive = true;
    void app.store
      .setting<Draft | null>(DRAFT, null)
      .then((stored) => {
        if (stored) {
          parseFoodPatch({ likes: stored.likes, dislikes: stored.dislikes });
          if (
            !Number.isInteger(stored.index) ||
            stored.index < 0 ||
            stored.index > TASTE_FOODS.length
          )
            throw Error('invalid');
        }
        if (alive) {
          if (stored) setDraft(stored);
          setReady(true);
        }
      })
      .catch(() => {
        if (alive) setError(true);
      });
    return () => {
      alive = false;
    };
  }, [app.store]);
  const persist = async (next: Draft) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      await app.store.setSetting(DRAFT, next);
      setDraft(next);
      setError(false);
    } catch {
      setError(true);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const choose = (choice: 'like' | 'dislike' | 'skip') => {
    const food = TASTE_FOODS[draft.index];
    if (!food || !ready || lock.current) return;
    void persist({
      index: draft.index + 1,
      likes: [
        ...draft.likes.filter((id) => id !== food.id),
        ...(choice === 'like' ? [food.id] : []),
      ],
      dislikes: [
        ...draft.dislikes.filter((id) => id !== food.id),
        ...(choice === 'dislike' ? [food.id] : []),
      ],
    });
  };
  const finish = async (skip = false) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(false);
    try {
      await app.saveFood(
        skip
          ? { taste_setup_done: true }
          : { likes: draft.likes, dislikes: draft.dislikes, taste_setup_done: true },
      );
      if (!skip) await app.store.setSetting(DRAFT, null);
      done();
    } catch {
      setError(true);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const food = TASTE_FOODS[draft.index],
    Icon = icons[food?.icon] ?? CookingPot;
  return (
    <div className="taste-onboarding">
      <PageHeader title={t('tasteTitle')} subtitle={t('tasteIntro')} back={back} />
      <div className="taste-progress">
        <progress aria-label={t('tasteProgress')} max={TASTE_FOODS.length} value={draft.index} />
        <span>
          {Math.min(draft.index + 1, TASTE_FOODS.length)} / {TASTE_FOODS.length}
        </span>
      </div>
      {food ? (
        <>
          <div
            className="taste-card"
            style={{ transform: `translateX(${offset}px) rotate(${offset / 24}deg)` }}
            onPointerDown={(event) => {
              if (!ready || busy || event.button !== 0) return;
              gesture.current = { id: event.pointerId, x: event.clientX, y: event.clientY };
              event.currentTarget.setPointerCapture(event.pointerId);
            }}
            onPointerMove={(event) => {
              const start = gesture.current;
              if (!start || start.id !== event.pointerId) return;
              const x = event.clientX - start.x,
                y = event.clientY - start.y;
              if (Math.abs(y) > Math.abs(x) && Math.abs(y) > 20) {
                gesture.current = null;
                setOffset(0);
                return;
              }
              setOffset(Math.max(-100, Math.min(100, x)));
            }}
            onPointerUp={(event) => {
              const start = gesture.current;
              gesture.current = null;
              setOffset(0);
              if (
                start &&
                start.id === event.pointerId &&
                Math.abs(event.clientX - start.x) >= 70 &&
                Math.abs(event.clientY - start.y) < 60
              )
                choose(event.clientX > start.x ? 'like' : 'dislike');
            }}
            onPointerCancel={() => {
              gesture.current = null;
              setOffset(0);
            }}
          >
            <Icon size={76} strokeWidth={1.4} aria-hidden="true" />
            <h2 aria-live="polite">{food.name[app.language]}</h2>
            <p className="muted">
              {t(
                draft.likes.includes(food.id)
                  ? 'tasteAlreadyLiked'
                  : draft.dislikes.includes(food.id)
                    ? 'tasteAlreadyDisliked'
                    : 'tasteCardHint',
              )}
            </p>
          </div>
          <div className="taste-actions" role="group" aria-label={t('tasteChoose')}>
            <button
              className="secondary"
              disabled={!ready || busy}
              onClick={() => choose('dislike')}
            >
              <X size={19} />
              {t('tasteDislike')}
            </button>
            <button className="primary" disabled={!ready || busy} onClick={() => choose('like')}>
              <Heart size={19} />
              {t('tasteLike')}
            </button>
          </div>
          <div className="taste-skip-row">
            <button
              className="text-button"
              disabled={!ready || busy || draft.index === 0}
              onClick={() => void persist({ ...draft, index: draft.index - 1 })}
            >
              <ArrowLeft size={16} />
              {t('back')}
            </button>
            <button
              className="text-button"
              disabled={!ready || busy}
              onClick={() => choose('skip')}
            >
              {t('tasteSkipFood')}
              <ArrowRight size={16} />
            </button>
          </div>
        </>
      ) : (
        <section className="taste-summary">
          <Check size={32} aria-hidden="true" />
          <h2>{t('tasteReady')}</h2>
          <p>{t('tasteSummaryHint')}</p>
          <h3>{t('tasteLiked')}</h3>
          <p>
            {draft.likes
              .map((id) => TASTE_FOODS.find((food) => food.id === id)!.name[app.language])
              .join(', ') || t('tasteNone')}
          </p>
          <h3>{t('tasteAvoid')}</h3>
          <p>
            {draft.dislikes
              .map((id) => TASTE_FOODS.find((food) => food.id === id)!.name[app.language])
              .join(', ') || t('tasteNone')}
          </p>
          <button
            className="secondary"
            disabled={busy}
            onClick={() => void persist({ ...draft, index: 0 })}
          >
            {t('tasteReview')}
          </button>
        </section>
      )}
      <div className="onboarding-finish">
        <button
          type="button"
          className="primary"
          disabled={!ready || busy}
          onClick={() => void finish()}
        >
          {t('tasteSave')}
          <Check size={18} />
        </button>
        <button
          type="button"
          className="text-button"
          disabled={busy}
          onClick={() => void finish(true)}
        >
          {t('setupNotNow')}
        </button>
      </div>
      <p className="muted taste-footnote">{t('tasteShared')}</p>
      {error && (
        <p className="error-note" role="alert">
          {t('foodSaveError')}
        </p>
      )}
    </div>
  );
}
