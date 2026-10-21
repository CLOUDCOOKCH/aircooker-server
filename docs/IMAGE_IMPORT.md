# Import a recipe from a photo or screenshot

Open **Import recipe → Photo or screenshot**, then choose **Take photo** or **Choose
image**. On supported phones, Take photo requests the rear camera; the browser and
operating system decide which camera or picker interface appears. Choosing a screenshot
from Photos or Files works without camera access. On desktop, pasting an image into the
photo import form also selects it.

1. Use one clear, straight-on image containing the recipe title, ingredients and method.
   Crop unrelated page furniture before choosing it. Printed English and German work
   best. A picture of the finished dish alone does not contain a written recipe.
2. Check the selected image, then choose **Prepare preview**. Text recognition runs on
   your self-hosted server; a cloud AI account is not required.
3. Open **Review** when the preview is ready. Compare ingredients, amounts, units,
   servings and steps against the image. **Recognized text** shows the OCR source.
   Everything in the recipe editor remains editable. The image becomes the recipe photo;
   remove or replace it there if you prefer a different cover.
4. Choose **Save** to add the reviewed recipe to the library. Preparing or opening a
   preview never saves a library recipe automatically.

If recognition needs help, the import remains in the list with a useful error. **Correct
recognized text** lets you correct extracted text and prepare another preview with the
same image. Give the corrected text a title and explicit Ingredients/Instructions or
Zutaten/Zubereitung headings. You can instead create a recipe manually using the retained
source. A manually created fallback does not confirm its original import; cancel that
request separately when finished.

## Recognition and image limits

Local Tesseract OCR includes English and German language data. The deterministic parser
recognises explicit ingredient and instruction sections, preserves original ingredient
text and uses the existing conservative metric/EN/DE quantity parser. It does not infer a
recipe from food appearance, invent nutritional values or translate the source. A missing
serving count uses an explicitly flagged editable default of two. Even a successful preview
needs review: OCR can confuse digits, fractions, units and line order.

Handwriting, multi-column book pages, skewed photographs, low contrast and obscured or
very small text may need correction or manual entry. This version imports one image per
request; it does not combine several pages or accept PDFs. Supported file signatures are
JPEG, PNG, WebP and browser-decodable HEIC/HEIF. HEIC support depends on the browser: if
the chooser reports an unsupported image, export it as JPEG or use a screenshot. The
browser picker may offer other formats, but unsupported contents are rejected.

The chosen file must be at most 25 MiB and decode to at most 32 million pixels. The
browser creates a metadata-free JPEG with a longest edge of 2048 pixels, flattens
transparency onto white and limits the upload to 8 MiB. The backend validates and
normalises it again through the existing recipe-media path, with a 1 MiB stored-image
limit and a 256 MiB total media quota. OCR uses a fixed command, one processing thread
and a 20-second timeout; recognised text is limited to 100,000 bytes.

## Privacy and optional AI

The image goes to your own authenticated backend, where local OCR reads it. It is not sent
to an external OCR service. Image metadata is removed during normalisation. The source
photo and recognised text are private household content; avoid including unrelated personal
information in the chosen image.

**Use configured AI** is optional. The administrator must first configure a supported
text provider. The separate consent checkbox explains that recognised text is sent to
that provider. The image bytes are never supplied to the AI adapters. No vision-provider
support is implied. AI output passes the existing recipe schema validation and still
requires explicit review/save. Keep AI disabled to use only your server's OCR and parser.
No live provider verification is claimed by the synthetic adapter tests.

On the server, confirmed/cancelled imports retain recognised text and previews for the existing 30-day
terminal grace period, then maintenance clears those fields while preserving replay
receipts. Pending and needs-input imports are not automatically expired. Uploaded media,
including unused or cancelled source images, remains subject to the media quota. Removing
a cover or cancelling a request does not reclaim the stored bytes. Deleting apparently
unreferenced uploads could lose a disconnected device's pending work, so automatic media
compaction is not implemented; see [retention](RETENTION.md).

## Offline work, backup and updates

Selecting an image and choosing Prepare preview stores the normalised image and import
request together in this browser's IndexedDB. An offline request remains queued across
reloads. Text extraction requires a connection to your server; reopening the app and
syncing uploads the image and submits the same import identity safely after an interrupted
response. Once accepted, the server's durable job continues even if the app closes.

An extracted recipe can be reviewed and saved offline; its confirmation remains in the
normal persistent outgoing queue. Keep the app open online to complete foreground sync.
Server backups cannot include an image or edit that is still only on a disconnected
device. **Settings → Export unsynchronised work** includes queued import requests and
their image bytes in the existing browser recovery format. This is a private manual
recovery export, not an automatically restorable household archive. A portable household
export includes saved recipes and their referenced images; it is not an export of pending
browser imports. See [PWA recovery](PWA.md#offline-operation-and-recovery) and
[backup/restore](BACKUP.md).

Keep your existing Docker volume, port mapping, command and healthcheck when updating,
including an existing `5152:5152` configuration. Save active edits and accept the PWA
update. Do not clear browser storage or reinstall while queued work is pending.

## Development and evidence

The Docker image includes Tesseract and both language models. For source development and
tests, install Tesseract with `eng` and `deu` data on the host as well. On Debian/Ubuntu:

```sh
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu
python scripts/image_import_browser_smoke.py
```

`GET /api/v1/system/capabilities` reports `image_recipe_import` and
`image_import_languages` from the installed OCR engine/models. API import requests use
the existing validated media upload followed by `POST /api/v1/imports` with `image_id`;
the import response exposes the bounded `recognized_text` alongside its editable recipe.
The migration adds that source-text field without changing household or sync identities.

Local evidence covers real English/German OCR, native chooser/capture semantics in
Chromium, queued-image and edited-recipe offline reloads, explicit-save boundaries,
metadata-safe uploads, narrow German dark layouts and Axe checks using synthetic recipes.
File-chooser automation does not verify physical camera hardware. WebKit, published-image
and release evidence are recorded separately as those checks complete; physical iPhone,
camera permissions, real handwriting and live AI remain unverified. See the current
[implementation checklist](IMPLEMENTATION.md) for publication status.

Authenticated WebKit CI uses a disposable one-day loopback certificate chain trusted by
the runner OS, generated by `scripts/browser_test_tls.py`. It sets
`MEALF_BROWSER_TEST_TLS` to that directory; no certificate verification bypass or
production cookie change is used. HTTP loopback remains a Chromium test convenience,
not a deployment recommendation.

The headless WebKit image-flow test explicitly models native push as unavailable; its
Linux runner has no OS push service. Authentication, media, OCR, local persistence,
backend outages and recipe confirmation remain real. Push has separate explicit
subscription/vendor fixture coverage; no live push claim follows from the photo tests.
Settings now avoids reading native subscriptions before notification permission is granted.
