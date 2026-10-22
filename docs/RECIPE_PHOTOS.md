# Recipe photos and missing-image fallback

Recipes without a usable photo display Mealf's original peach on a theme-aware surface.
The same fallback is used in the library, recipe detail/editor and existing meal/suggestion
thumbnails. Missing, unavailable, uncached-offline and unreadable images do not leave a
broken-image icon. It is a decorative placeholder, not a generated photo of the dish.
Existing recipes receive this display change without editing their stored data.

## Photos from imported sources

URL imports, including household-AI-assisted imports, try the source's Schema.org Recipe
image first, then Open Graph or Twitter image metadata. ImageObject URLs, image arrays and
relative URLs are supported. Relative images use the fetched page's final redirect URL.
The original recipe source and image origin remain in attribution/provenance.

The photo appears in the editable preview. You can remove or replace it before Save.
An incomplete AI draft retains the photo while missing servings or other facts are corrected.
Nothing creates a recipe automatically. After Save, the image uses the existing authenticated
media endpoint and is cached in IndexedDB when viewed; cached images remain available offline.
Uncached images use the peach until they can be downloaded.

If the source has no usable image, requires login, rejects access, exceeds a limit or its
photo fails validation/storage, the recipe still reaches review with an explanation and a
placeholder. Restricted social sources are not bypassed. Existing photo-less AI recipes are
not silently revisited: re-import their source to attempt a new extraction, or add a photo
in the editor. Camera/OCR inputs retain their existing image and text-only optional-AI policy.
Text-only personal ChatGPT imports have no source URL and use the fallback unless a photo
is added. Upload-only PDFs/video do not invent a food image.

## Privacy and safety

Image URLs come from source-page metadata, not model-generated URLs or a stock-photo search.
The backend fetches them; the browser never hotlinks the source and no AI image-generation
request is added. A page preview may depict the page rather than the exact dish: review it.
Importing does not grant rights to third-party recipe photos; respect the source's terms.

Only public HTTPS destinations on port 443 are allowed. DNS is validated and pinned for
TLS, every redirect is checked, credentials/cookies are not forwarded, URL/download size
and redirect counts are limited, and compressed or unexpected responses are rejected.
At most three image candidates are tried. A separate bounded process limits wall time,
CPU, address space and file descriptors; invalid images fail without failing recipe review.
JPEG/PNG/WebP inputs must decode as their stated type, be a single frame and satisfy the
existing 8 MiB/16-million-pixel limits. The stored JPEG is resized and stripped of EXIF/GPS
and other metadata; existing 1 MiB/image and 256 MiB/household quotas apply.

Migration 014 adds the draft-to-image `import_source_photo` relation. Image insertion,
provenance and draft publication are transactional; cancellation cannot publish a photo.
A replay reuses the saved canonical photo rather than downloading it again. Terminal draft
photo references expire with preview content after 30 days; immutable saved media remains
under the existing conservative retention policy so offline/history references stay valid.
Portable ZIP exports include saved recipes and their images, not pending import drafts.
Keep the entire data volume for disaster recovery. Back up before upgrading; do not downgrade
an upgraded database in place to a version that does not understand migration 014.

## API and validation

`GET /api/v1/imports/{id}` adds optional `source_photo: {image_id, source_url}`. This lets
clients attach a source image even when the AI extraction is incomplete and `recipe` is
null. Existing recipe `image_id` and provenance fields remain unchanged. API major/sync
protocol are unchanged. The PWA consumes regenerated types; the retained native repository
and contract pin deliberately remain unchanged by this additive PWA feature.

Local coverage includes deterministic and AI/incomplete drafts, explicit confirmation,
private redirect rejection, metadata/type/encoding/size limits, retry/cancellation, quota
fallback and terminal retention. The real Chromium PWA/server/worker flow covers editable
image preview, explicit Save, missing/broken-image fallbacks, EN desktop/DE dark phone/Axe
and cached offline reload. Source/AI network responses are explicit doubles, with the existing
illustrative demo food asset used as a synthetic source picture. Live-site/provider and
physical-iPhone behavior remain unverified. See [bounded UI review](validation/source-photos-ui-review.md).
