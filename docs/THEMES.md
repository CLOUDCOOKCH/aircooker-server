# Mealf themes

Open **Settings → Theme library** (Deutsch: **Einstellungen → Design-Bibliothek**).
Select a row; appearance changes immediately, without a save button or page reload.
The selected radio and outline show the current choice without relying on colour.
Tab and arrow keys work with the native radio group. Each choice describes its mode.

| Theme | Appearance | Palette |
| --- | --- | --- |
| Flo | Follows the device | Existing cream/coral/peach light and cocoa/peach dark |
| After Dark | Always dark | Midnight ink, oxblood surfaces, dusty rose actions and muted gold details |
| Sunday | Always light | Linen white, sage and deep green actions |

The administration header offers the same choices, including before login. Original
supplied peach and wordmark are preserved. Navigation retains glass, forms stay solid,
and system typography/food photography stay intact. No palette crossfade obscures text.

## Device preference and offline use

The allowlisted `mealf.appearance.v1` preference is browser/origin-local, shared across
PWA and console tabs on that origin. It is not household data, sent to the server or
synchronised between devices. An installed PWA can have separate browser storage on
some platforms; select its theme inside that installation if necessary. No account or
API/database migration is involved. New/existing browsers default to Flo. Unknown saved
values fall back safely to Flo. Clearing browser data can remove this preference **and
unsynchronised work**, so it is not an upgrade or theme troubleshooting step.

The public controller runs in the document head after the shared stylesheet, before
the application bundle. It updates browser theme-colour metadata and native form colour
scheme. Flo responds to device changes; explicit dark/light choices override them.
The controller, palette and UI are part of the offline service-worker shell. Storage
write failures apply the choice to the current tab and show a localised warning rather
than claim it was saved. Read failures use Flo. Cross-tab storage events update both
surfaces. No external theme URLs, arbitrary styles or executable theme imports exist.

The manifest's baseline launch/splash colour remains Flo light. Browser/OS status bars,
launch screens and installed windows can retain their own colours or caches; dynamic
page metadata is a hint, not guaranteed OS control. Physical iPhone confirmation remains
unverified. Save edits and accept an offered PWA update; no reinstall is required.

## Implementation and checks

`frontend/src/tokens.css` is the sole palette source. The build prepares an exact public
copy before Vite and exports exact bytes as `/app/theme.css`. Both documents load the
same `/app/appearance.js`. Explicit root selectors win over Flo's system media query.
Preview miniatures use the same token sets and are decorative, not actual screenshots.

`python scripts/theme_browser_smoke.py` exercises actual controls and IndexedDB-backed
demo work with a disposable real backend/profile. It checks radio arrow navigation,
three themes under light and dark device modes, metadata/native controls, offline
selection/reload, cross-tab console reuse, selection before React loads, invalid stored
IDs, read/write storage failures, 320px overflow and EN/DE strings. Settings fieldsets
and phone grid tracks explicitly shrink below native intrinsic minima, including long
German labels in WebKit. Computed foreground/
background pairs meet 4.5:1 and focus/control boundaries 3:1; Axe covers WCAG AA checks.
CI runs the flow in Chromium and persistent-profile WebKit. Chromium uses browser
offline emulation; WebKit stops the actual test backend and restores it after two
cache-backed reloads. The automation offline flag on the CI WebKit build reports an
internal engine error for service-worker navigation. Neither test substitutes a worker
or cache implementation. Run `MEALF_THEME_NETWORK_OUTAGE=1 python scripts/theme_browser_smoke.py`
to exercise the real-outage path locally in Chromium as well. These engines do not
prove physical iOS Home Screen, software keyboard or complete manual accessibility.

Existing recipe/sync/planning/import, mobile calendar/layout and console/push tests
remain in the normal CI matrix. Native iOS and external integrations are unchanged.
Release status and exact evidence live in `IMPLEMENTATION.md` and `validation/`.
