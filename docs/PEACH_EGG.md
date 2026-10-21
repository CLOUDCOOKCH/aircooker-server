# Slap the peach

Click or tap a peach in the PWA or administration console for a silent hand-swipe,
quick squash/wobble and one of four English or German food comebacks. Enter and Space
work on the native button too. The wordmark remains a separate navigation link; tapping
the peach does not submit a form, navigate or change household data.

The shared `/app/peach.js` and `/app/peach.css` are included in the installed offline
shell. Each activation restarts the 560ms Web Animations effect; repeated taps cancel
previous motion. The caption lasts 2.2 seconds and is announced through a polite status
region. Reduced motion removes spatial movement and retains the caption and subtle
background feedback. Hiding the page or resizing clears feedback. No sound, network
request, persistent counter, telemetry or dependency was added. Original artwork bytes
remain unchanged. The hand is the existing Lucide Hand icon (ISC).

Additional localized jokes appear in login, Home and recipe/calendar empty states.
Security, help, consent, setup and error instructions remain literal.

## Verification

Chromium checks cover click, repeated activation, Enter, Space, reduced motion, localized
feedback, mobile caption bounds, resize cleanup and offline PWA activation. Existing
PWA workflows, administration workflows and accessibility scans pass with synthetic data.
Physical iPhone/Safari and screen-reader delivery have not been verified.

Genuine captures: [desktop contact frame](screenshots/mealf-peach-contact-desktop.png),
[German dark reduced-motion phone](screenshots/mealf-peach-reduced-phone-de-dark.png),
[admin phone layout](screenshots/mealf-peach-admin-phone-de-dark.png) and
[Home](screenshots/mealf-peach-home-desktop.png). The contact capture pauses the actual
browser animation at 168ms for inspection. A still frame is not proof of movement;
automated interaction/keyframe checks provide the separate behavioral evidence.

The implementation-agent manual review found and corrected caption placement after
viewport changes. The final confirmation reviewed artwork, caption bounds, heading
clearance and unchanged page composition. No required findings remain within this
small interaction scope. This is not an independent specialist, detector, plugin-schema,
physical-device or full-product acceptance review.
