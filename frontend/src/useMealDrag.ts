import { useEffect, useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent, RefObject } from 'react';
import { categories } from './lib/domain';
import type { Category } from './lib/domain';

export type MealDragSource = { id: string; day: string; key: string; title: string };
type Destination = { date: string; category: Category };
type Drag = { source: MealDragSource; x: number; y: number; target: Destination | null };
type Session = Drag & {
  pointer: number;
  startX: number;
  startY: number;
  active: boolean;
  handle: HTMLElement;
  tap: () => void;
};

/** Drag only from an explicit grip; ordinary cards and page gestures keep scrolling. */
export function useMealDrag(
  grid: RefObject<HTMLDivElement | null>,
  move: (source: MealDragSource, target: Destination) => Promise<void>,
  disabled = false,
) {
  const [drag, setDrag] = useState<Drag | null>(null);
  const session = useRef<Session | null>(null);
  const frame = useRef(0);
  const consume = useRef<string | null>(null);
  const commit = useRef(move);
  commit.current = move;
  const stop = () => {
    cancelAnimationFrame(frame.current);
    const current = session.current;
    session.current = null;
    if (current?.handle.hasPointerCapture(current.pointer))
      current.handle.releasePointerCapture(current.pointer);
    document.documentElement.classList.remove('meal-is-dragging');
    setDrag(null);
  };
  const destination = (x: number, y: number): Destination | null => {
    const element = document.elementFromPoint(x, y)?.closest<HTMLElement>('[data-meal-slot]');
    const date = element?.dataset.date;
    const category = element?.dataset.category as Category;
    return date && categories.includes(category) && grid.current?.contains(element!)
      ? { date, category }
      : null;
  };
  useEffect(() => {
    let previous = 0;
    const tick = (time: number) => {
      const current = session.current;
      if (!current?.active) return;
      const step = Math.min(24, time - (previous || time)) / 16;
      previous = time;
      const region = grid.current;
      if (region) {
        const bounds = region.getBoundingClientRect();
        if (current.y > bounds.top && current.y < bounds.bottom) {
          if (current.x < bounds.left + 36) region.scrollLeft -= 9 * step;
          else if (current.x > bounds.right - 36) region.scrollLeft += 9 * step;
        }
      }
      if (current.y < 80) window.scrollBy(0, -9 * step);
      else if (current.y > innerHeight - 100) window.scrollBy(0, 9 * step);
      current.target = destination(current.x, current.y);
      setDrag((old) =>
        old?.x === current.x &&
        old?.y === current.y &&
        old?.target?.date === current.target?.date &&
        old?.target?.category === current.target?.category
          ? old
          : { source: current.source, x: current.x, y: current.y, target: current.target },
      );
      frame.current = requestAnimationFrame(tick);
    };
    const pointerMove = (event: PointerEvent) => {
      const current = session.current;
      if (!current || current.pointer !== event.pointerId) return;
      current.x = event.clientX;
      current.y = event.clientY;
      if (
        !current.active &&
        Math.hypot(current.x - current.startX, current.y - current.startY) >= 8
      ) {
        current.active = true;
        document.documentElement.classList.add('meal-is-dragging');
        previous = 0;
        frame.current = requestAnimationFrame(tick);
      }
      if (current.active) event.preventDefault();
    };
    const pointerUp = (event: PointerEvent) => {
      const current = session.current;
      if (!current || current.pointer !== event.pointerId) return;
      const target = destination(event.clientX, event.clientY);
      consume.current = current.source.key;
      const tapped =
        !current.active &&
        Math.hypot(event.clientX - current.startX, event.clientY - current.startY) < 8;
      stop();
      if (current.active && target) void commit.current(current.source, target);
      else if (tapped) current.tap();
    };
    const cancel = () => {
      consume.current = null;
      stop();
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && session.current) {
        event.preventDefault();
        cancel();
      }
    };
    const hidden = () => {
      if (document.hidden) cancel();
    };
    const lostCapture = (event: PointerEvent) => {
      if (session.current?.pointer === event.pointerId) cancel();
    };
    window.addEventListener('pointermove', pointerMove, { passive: false });
    window.addEventListener('pointerup', pointerUp);
    window.addEventListener('pointercancel', cancel);
    window.addEventListener('lostpointercapture', lostCapture);
    window.addEventListener('blur', cancel);
    window.addEventListener('resize', cancel);
    window.addEventListener('keydown', escape);
    document.addEventListener('visibilitychange', hidden);
    return () => {
      cancel();
      window.removeEventListener('pointermove', pointerMove);
      window.removeEventListener('pointerup', pointerUp);
      window.removeEventListener('pointercancel', cancel);
      window.removeEventListener('lostpointercapture', lostCapture);
      window.removeEventListener('blur', cancel);
      window.removeEventListener('resize', cancel);
      window.removeEventListener('keydown', escape);
      document.removeEventListener('visibilitychange', hidden);
    };
  }, [grid]);
  const begin = (
    event: ReactPointerEvent<HTMLButtonElement>,
    source: MealDragSource,
    tap: () => void,
  ) => {
    if (disabled || !event.isPrimary || event.button !== 0) return;
    stop();
    consume.current = null;
    event.preventDefault();
    event.currentTarget.focus({ preventScroll: true });
    event.currentTarget.setPointerCapture(event.pointerId);
    session.current = {
      source,
      x: event.clientX,
      y: event.clientY,
      startX: event.clientX,
      startY: event.clientY,
      pointer: event.pointerId,
      handle: event.currentTarget,
      active: false,
      target: null,
      tap,
    };
  };
  const consumeClick = (key: string, detail: number) => {
    const ignored = detail > 0 && consume.current === key;
    consume.current = null;
    return ignored;
  };
  return { drag, begin, consumeClick, cancel: stop, disabled };
}
