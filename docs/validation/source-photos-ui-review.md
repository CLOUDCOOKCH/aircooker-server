# Source recipe photos UI finish review

Date: 2026-10-22. Scope: the shared recipe-photo fallback and source pictures in the PWA's existing AI URL-import review/save flow. This is a local extension of the established Operate surface. It introduces no new visual world, approved comp, seed, design card or QUALITY BAR round.

## Disposition and finish contract

**Ship within the reviewed photo UI scope.** The supplied fresh independent `source_photo_finish_reviewer` returned persistence **pass**, TYPE/MATERIAL/GROUND **match**, thesis/story/form **match**, quality ceiling **reached**, and **no material UI fixes**. The shipped specialist definition was unavailable; this was an explicitly disclosed manual fallback review, not a pass by the unavailable specialist or automated design tooling. This documentation handoff independently opened all five genuine captures and inspected the sources and browser evidence below without rerunning tests or browser checks.

The later source-only consolidation of duplicate `.photo-placeholder` CSS rules preserves computed styles and the capture bytes. The independent reviewer was notified of that consolidation. No further polish or verification round is required by the bounded finish verdict. This verdict does not establish whole-product readiness, a security audit, physical-device acceptance or publication.

## Authority and inspected sources

[PRODUCT.md](../../PRODUCT.md), [DESIGN.md](../../DESIGN.md), the [project-owned design snapshot](../../.impeccable/design.json) and the [PWA surface brief](../../.impeccable/surfaces/pwa.md) remain the context. Preserve system typography, solid reading/editing surfaces, glass navigation, original peach/wordmark artwork and shared Flo/After Dark/Sunday semantic themes. Historical selected-day-only mobile Calendar and system-only appearance descriptions are superseded by the later mobile-calendar and theme-library entries. This review records that drift without regenerating or repairing the design artifacts.

Direct inspection covered `frontend/src/components.tsx`, `frontend/src/Recipes.tsx`, `frontend/src/styles.css`, `frontend/src/lib/sync.ts`, `frontend/src/lib/imports.ts`, `scripts/source_photo_browser_smoke.py` and `build/source-photo-browser.log`, alongside README and implementation guidance. The inspected checkout's parent HEAD was `2a2fcc600acb5f3093c380ed2d891a1c0d4e88d8`; feature work was uncommitted, so the hashes below identify reviewed bytes more precisely than that parent commit.

| Source | SHA-256 |
| --- | --- |
| `frontend/src/components.tsx` | `34d2971add80dedac64de125115d21627de2548e0f63ec087ffc8df8aa52f3e9` |
| `frontend/src/Recipes.tsx` | `2ceaba1f74dc6f66b6f6b99da06e14a2719d74fff092ebcd0b1b14d2f0cea989` |
| `frontend/src/styles.css` | `c6a33ce3603a0a5704ae3e993ca34b7054d46d85360953f42179411dbd9f62af` |
| `frontend/src/lib/sync.ts` | `3dfffd2a60bdb8658480df6f6fc53f79bea8a88e6cb254e2bcbe4d69219c03dd` |
| `frontend/src/lib/imports.ts` | `a11374706ab9263d37b54df67c8cd7fcd4e779b6bbd5e954ff3a9c1a73972ed2` |
| `scripts/source_photo_browser_smoke.py` | `e388e995a7da6c6ce5e22c3e3503d90097998e91d3a55be357a1af4acf9077d5` |
| `build/source-photo-browser.log` (local build evidence) | `e59026183931b1ab907603f02cd7bab79609d08f68c4dbb3bf5e8e4f71c52bd6` |

Preserved context hashes are `PRODUCT.md` = `45643c4a6046e91586444b1cb39fd07df3006862d2cd03ca525c2288dd693484`, `DESIGN.md` = `88f6ea00dc1ed1dcfb41ec622fa33891fab864c847bf318691fc086ee139b00c`, and `.impeccable/design.json` = `e1f321a7f0098a28c3233665cf66305ae12b52b9b5dbf4a2e105435ec28f50d9`. The fallback reuses existing `frontend/public/brand/peach-v1.png` (`4e3f12762a25330d51d415fdcb42dffd7a7e36289f925f47bb4d5becbfd1be1d`). Original artwork remains in `assets/brand/originals/`: peach `a3384ae38b80af70aa63400af2f8fc1525e4e5a11370daca3ffc67d0c82aa69e`, wordmark `dfbba3ebedca96dbc76d7baef7bafad75228f0c90ffdafde234c2ccc02b9d3fb`.

## Genuine captures and asset provenance

All five captures in `docs/screenshots/source-photos/` were opened with `view_image`; `.impeccable/review/source-photos/` contains byte-identical copies, verified by SHA-256. They are real Chromium renders with synthetic household data. Desktop viewport was 1440×1000 and phone viewport 390×844. Full-document capture explains the 3256px review image and 914px phone images. Fixed phone navigation remains at its viewport position over one document band; that alone does not establish permanent content obstruction. Static captures do not establish motion quality.

| Capture | Image pixels | Visible evidence |
| --- | --- | --- |
| [recipe-fallback-desktop.png](../screenshots/source-photos/recipe-fallback-desktop.png) | 1440×1000 | Missing and unreadable photos both use the centered original peach on a quiet soft surface; titles and servings remain readable. |
| [recipe-fallback-detail-desktop.png](../screenshots/source-photos/recipe-fallback-detail-desktop.png) | 1440×1000 | Large detail fallback preserves the existing photo frame, recipe hierarchy and meal action. |
| [source-image-review-desktop.png](../screenshots/source-photos/source-image-review-desktop.png) | 1440×3256 | Editable import, incomplete-servings warnings, attached source-picture fixture, remove-photo control, retained recipe text and explicit Save. |
| [recipe-photos-phone-de-dark.png](../screenshots/source-photos/recipe-photos-phone-de-dark.png) | 390×914 | German After Dark compact rows retain one saved image and two peach fallbacks; long synthetic title wraps. |
| [recipe-photos-offline-phone-de-dark.png](../screenshots/source-photos/recipe-photos-offline-phone-de-dark.png) | 390×914 | Offline reload retains the cached image, both fallbacks and literal offline/local-save status. |

SHA-256 of the reviewed capture bytes:

```text
recipe-fallback-desktop.png           3fae1d09f805198c3253bdf353f6fda2f0c715addd1411d9e6029ebd266af9a7
recipe-fallback-detail-desktop.png    eea8bb76001bbbd23291c5a86c5496199b4fb691c4a24a0a55ef76887ae19c3a
source-image-review-desktop.png       5f605ec3babb64a5ff64b4306f28257c275288e66040438d5cad1a67be70b6cf
recipe-photos-phone-de-dark.png       f41f99b88207d852dab23e28238bf8936b315c3515a228df3813a8d8c33da5fa
recipe-photos-offline-phone-de-dark.png e7db4b1513f025a5ff5bbad4aee92acdb9dd63f8d979a243a6e8133ca1080958
```

The source-picture fixture is the existing illustrative `frontend/public/art/lemon-chicken.png`, SHA-256 `c4b3022806d16e9402b51597d07e095d9d7c00db997d1736d4d53c68db360b12`. It stands in for a remotely fetched picture in this isolated test; it is neither a new asset nor proof of a live publisher's photograph. The deliberately mixed recipe-text/picture fixture does not establish semantic photo matching. Source page, image transport and AI-provider outputs are explicit doubles at `source.example.invalid`; no real household gains sample content.

## Behavior and visual continuity

- **Fallback:** the shared `Photo` component shows the existing peach on `--soft` when an image is absent, unavailable or fails browser decoding. The decorative fallback is hidden from assistive technology and cannot be dragged. The mark uses proportional 56% bounds capped at 104px, preserving its silhouette at thumbnail and detail sizes. Existing recipe titles supply row names; recipe detail images retain their contextual alternative text. There is no invented dish image for missing content.
- **Source-picture preview:** sync accepts optional `source_photo` alongside a canonical recipe or an incomplete AI extraction. It assigns the media ID and records `image_source` plus `image_extractor: source-metadata-v1` in provenance. `extractionPreview` keeps unknown servings blank, so a useful image can accompany an editable draft whose facts still need review. The existing recipe editor renders that image, permits removal or replacement, and presents literal review/warning copy. Missing source-picture warnings have their own localized mapping. Not every warning or failure branch is captured.
- **Explicit save and persistence:** preparing/reviewing an import does not add a recipe. The normal editor draft chain preserves changes locally, and explicit Save performs canonical validation and calls the existing durable save path. Source attribution remains part of recipe provenance, exposed by the existing source disclosure. The supplied browser script checks two recipes before Save, three after the corrected serving count, and exact original image attribution. `Photo` reads local media first, fetches server media when online and caches it for subsequent use; failed caching still permits the downloaded image to display. The supplied offline reload retains the cached picture and both fallbacks.
- **Material and form:** warm desktop fields, system type, solid editor surfaces and glass navigation stay within the established interface. The peach adds recognizable brand presence without replacing the recipe title or action hierarchy. Phone rows adapt to 84px thumbnails; German labels and source-language recipe titles wrap acceptably in After Dark. The retained native repository is intentionally unchanged. Optional additive API `source_photo` leaves the existing protocol behavior available to older clients; this document does not independently certify backend or native compatibility.

## Supplied verification and limits

The inspected browser log reports **PASS** for the real PWA/server/worker AI-source-image review, explicit Save, original attribution, missing/unreadable-photo peach fallbacks, English desktop/German dark phone checks with Axe, and cached offline reload. The script verifies an incomplete-servings AI URL import, an attached picture before Save, retained attribution after Save, no page errors and no horizontal document overflow. Axe runs against `main` for WCAG 2 A/AA and 2.1 AA tags. The implementation handoff separately reports 383 backend and 55 frontend tests passing; this documentation pass did not rerun them.

The context launcher and automated detector were attempted but absent; no launcher, detector, design-hook or plugin-schema validation pass is claimed. The independent manual finish review is separate supplied evidence. Scoped Axe checks and static captures do not establish full keyboard, screen-reader, text-enlargement, motion or accessibility acceptance. No live source/provider, physical iPhone/Safari, exact-source CI or publication result is claimed here. Those remain separate from this bounded photo UI disposition.
