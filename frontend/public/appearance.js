(() => {
  'use strict';
  const key = 'mealf.appearance.v1';
  const ids = ['flo', 'after-dark', 'sunday'];
  const validate = (value) => (ids.includes(value) ? value : 'flo');
  const device = matchMedia('(prefers-color-scheme: dark)');
  let current = 'flo';
  try {
    current = validate(localStorage.getItem(key));
  } catch {
    // Appearance is still usable when browser storage is unavailable.
  }
  function apply(value) {
    current = validate(value);
    document.documentElement.dataset.theme = current;
    const dark = current === 'after-dark' || (current === 'flo' && device.matches);
    const scheme = dark ? 'dark' : 'light';
    document.querySelectorAll('meta[name="color-scheme"]').forEach((meta) => {
      meta.content = scheme;
    });
    const canvas = getComputedStyle(document.documentElement).getPropertyValue('--canvas').trim();
    if (canvas)
      document.querySelectorAll('meta[name="theme-color"]').forEach((meta) => {
        meta.removeAttribute('media');
        meta.content = canvas;
      });
    window.dispatchEvent(new Event('mealf:appearance'));
  }
  window.mealfAppearance = Object.freeze({
    get: () => current,
    set: (value) => {
      const next = validate(value);
      let saved = true;
      try {
        localStorage.setItem(key, next);
      } catch {
        saved = false;
      }
      apply(next);
      return saved;
    },
  });
  window.addEventListener('storage', (event) => {
    if (event.key === key || event.key === null) apply(event.newValue);
  });
  device.addEventListener('change', () => apply(current));
  apply(current);
  document.addEventListener('DOMContentLoaded', () => apply(current), { once: true });
})();
