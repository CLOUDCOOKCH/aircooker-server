# Mobile calendar and meal forms

Switch Calendar between **Day**, **3 days** and **Week**. The setting is remembered on
this device, including offline use. Day shows the selected date. Three days shows a
window within the selected Monday–Sunday week, clamped at Friday when necessary. Week
shows Monday–Sunday. Multi-day columns remain at least 160px wide: swipe sideways to
reach the other days rather than compressing meal titles. The selected date stays visible.

Drag a meal using its grip to change its date or breakfast/lunch/dinner category. A
preview follows the pointer, the source fades, and the destination highlights. Holding
near a grid/page edge scrolls. Ordinary card taps still open the recipe and gestures
outside grips still scroll. The original desktop HTML drag/drop path remains available.
There is no new drag library, service or mandatory network call.

Tap the grip or focus it and press Enter/Space to open the existing date/category form.
The meal menu also remains available. Escape, pointer cancellation, lost capture, hiding
or leaving the page, resizing, or changing the view/date cancels the active drag. Releasing
outside a valid slot also cancels. Nothing is saved until a valid drop. Same-slot drops
are no-ops; repeated commits are guarded while the save completes. Failed saves tell
users to check the meal's date before retrying.

Moves use the existing transactional local store/outbox and server sync. They work offline
and survive reopening; this adds no new conflict policy. A recurring occurrence gets an
exception and detached entry, rather than moving its entire series. Recipe, portions,
leftover reference and cooked status are retained. Bring! still reconciles on the backend
after synchronization. Changing the visible calendar range never writes a meal.

## Date and meal alignment

The reported iPhone screenshot showed a native date control extending into its neighbouring
meal control. Rows now use a two-column minmax grid, constrained date/select widths and
consistent 48px paired controls. At 480px and below, paired fields inside dialogs stack.
The date picker remains native, localizable and at least 16px on phones. No control is
cropped or removed to conceal the overlap. Focus indication and browser accessibility
zoom are retained.

## Evidence and limits

Local Chromium checks exercise trusted touch input for an offline date/category move,
offline reload, saved view choice, ordinary horizontal finger scrolling and touch cancel.
Mouse PointerEvents exercise edge scrolling and Escape cancellation; tap and keyboard
activation open the move form. All six viewport/theme/language variants check calendar
counts, document width, mobile fonts and paired date/select bounds. Existing full PWA
offline/sync workflows and accessibility scans pass, alongside 226 backend/39 frontend
tests and lint/type/build/contract/artwork checks. CI runs this same layout script in
Chromium and persistent-profile WebKit; its actual result is recorded in release evidence.

Genuine Chromium captures with synthetic data:

- [Aligned German dark phone dialog](screenshots/mealf-mobile-plan-aligned.png)
- [Three-day calendar](screenshots/mealf-mobile-calendar-three-days.png)
- [Live touch-drag state](screenshots/mealf-mobile-calendar-drag.png)

The interaction image records an actual active gesture; it alone does not prove movement.
The drop, persistence and cancellation assertions provide separate behavioral evidence.
The implementation-agent source/capture review found no required remaining issue in this
scope after confirming the narrow form and interaction states. No independent specialist,
unavailable plugin-schema or full-product acceptance pass is claimed. Linux engine tests
inject notch geometry and cannot establish actual iOS Home Screen, keyboard or finger
behavior. Physical phone confirmation remains necessary. Native iOS code is unchanged.

Published in `poc-20261021.8`: all six exact-source CI jobs and both native image
gates pass. Chromium and WebKit complete the extended script, including tap and Escape
regressions. Public pull, release/config identities and a disposable same-volume upgrade
on internal 5152 pass. See [exact release evidence](validation/github-mobile-calendar-preview.json).
