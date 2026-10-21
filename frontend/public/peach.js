/* Silent, local-only easter egg shared by the PWA and administration console. */
(() => {
  'use strict';
  const lines = {
    en: [
      'Oh, fork me.',
      'Harder. The dough, you menace.',
      'Dinner first. Spanking later.',
      'Tenderise the peach. Respect the chef.',
    ],
    de: [
      'Oh, leck mich. Den Löffel natürlich.',
      'Fester. Den Teig, du Ferkel.',
      'Erst Abendessen. Dann versohlen.',
      'Erst kneten. Dann vernaschen.',
    ],
  };
  const counts = new WeakMap();
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let motions = [],
    active = null,
    timer;
  const feedback = document.getElementById('peach-reaction');
  function cancelMotion() {
    motions.forEach((animation) => animation.cancel());
    motions = [];
  }
  function clear() {
    cancelMotion();
    clearTimeout(timer);
    active?.removeAttribute('data-slapped');
    active = null;
    if (feedback) feedback.textContent = '';
  }
  document.addEventListener('click', (event) => {
    const button =
      event.target instanceof Element ? event.target.closest('button[data-peach]') : null;
    if (!button || !feedback) return;
    clear();
    active = button;
    const language = (button.dataset.peachLanguage || document.documentElement.lang).startsWith(
      'de',
    )
      ? 'de'
      : 'en';
    const count = counts.get(button) || 0;
    counts.set(button, (count + 1) % lines[language].length);
    button.setAttribute('data-slapped', '');
    feedback.style.left = '16px';
    feedback.style.top = '0px';
    feedback.lang = language;
    feedback.textContent = lines[language][count];
    const box = button.getBoundingClientRect(),
      bubble = feedback.getBoundingClientRect();
    feedback.style.left =
      Math.max(
        16,
        Math.min(innerWidth - bubble.width - 16, box.left + box.width / 2 - bubble.width / 2),
      ) + 'px';
    const above = box.top - bubble.height - 10;
    feedback.style.top =
      Math.max(8, Math.min(innerHeight - bubble.height - 8, above >= 8 ? above : box.bottom + 10)) +
      'px';
    const peach = button.querySelector('img'),
      hand = button.querySelector('.peach-hand');
    if (!reduced.matches && peach?.animate && hand?.animate) {
      motions = [
        peach.animate(
          [
            { transform: 'none', offset: 0 },
            { transform: 'none', offset: 0.15 },
            { transform: 'translateX(-5px) rotate(-12deg) scale(.86,1.1)', offset: 0.3 },
            { transform: 'translateX(3px) rotate(8deg) scale(1.04,.97)', offset: 0.55 },
            { transform: 'rotate(-3deg)', offset: 0.8 },
            { transform: 'none', offset: 1 },
          ],
          { duration: 560, easing: 'cubic-bezier(0.16,1,0.3,1)' },
        ),
        hand.animate(
          [
            { transform: 'translate(65%,-35%) rotate(-35deg)', opacity: 0, offset: 0 },
            { transform: 'translate(15%,-10%) rotate(-10deg)', opacity: 1, offset: 0.18 },
            { transform: 'translate(-45%,5%) rotate(-28deg)', opacity: 1, offset: 0.3 },
            { transform: 'translate(-65%,10%) rotate(-38deg)', opacity: 0, offset: 0.65 },
            { transform: 'translate(-65%,10%) rotate(-38deg)', opacity: 0, offset: 1 },
          ],
          { duration: 560, easing: 'ease-out' },
        ),
      ];
    }
    timer = setTimeout(clear, 2200);
  });
  reduced.addEventListener('change', () => {
    if (reduced.matches) cancelMotion();
  });
  addEventListener('pagehide', clear);
  addEventListener('resize', clear);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) clear();
  });
})();
