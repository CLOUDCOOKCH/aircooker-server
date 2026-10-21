# ADR 014: Local OCR and reviewed image recipe imports

Status: accepted for development, 2026-10-21.

Reuse the immutable authenticated media path, persistent import jobs and existing explicit
confirmation protocol. The PWA normalises browser-decodable camera/screenshot files and
atomically stores image bytes plus request in IndexedDB. Upload the image before submitting
the import UUID. An optional `image_id` extends v1 compatibly; unchanged URL/text requests
keep their exact historical replay fingerprints. The server owns the typed import response
and its `recognized_text`; iOS deliberately pins this version without adding native UI.

Choose local Tesseract with English/German tessdata_fast over mandatory cloud vision or a
new OCR service. It runs as the container's existing non-root user, fixed argument list,
validated canonical JPEG on stdin, one thread, no inherited integration credentials and a
20-second timeout. No shell command, downloaded executable, web fetch or user-controlled
path is accepted. Both language models must be present for capability advertisement.
Native AMD64/ARM64 Docker gates exercise actual OCR before publication. Image/CPU limits
bound ordinary work; the single durable worker serialises OCR with other jobs, so a hard
photo can delay other queued work up to the timeout. This is a measured-household design,
not a claim of arbitrary image-parser isolation or concurrent OCR capacity.

Conservative EN/DE section recognition parses recipe facts and marks uncertain fields for
review. Unreadable or unfamiliar layouts retain source text/image and require correction,
optional configured text AI or manual entry. Optional AI receives only recognized/corrected
text after consent, uses the existing bounded schema-validating adapters, and never receives
image bytes. No vision model capability or live provider validation is implied.

A prepared draft does not create a recipe. Explicit Save reuses the durable offline
confirmation mutation. Cancellation cannot be overwritten by a stale poll or late worker;
retries reuse image/request identities. Terminal history is filtered before active import
batch limits so old receipts cannot starve new work. Import-only images survive crashes
and existing local recovery exports. No automatic orphan-media deletion is added: a future
offline edit may still refer to an uploaded image. Existing media quota and terminal-source
retention apply, with the unused-media management limitation documented to operators.

Alternatives: browser OCR adds a large worker/model cache and complicates installed offline
updates; cloud vision would require credentials and external image disclosure; mandatory
AI conflicts with optional self-hosting. Local OCR plus explicit review provides a useful
no-AI path while keeping external adapters replaceable. Handwriting, multi-page layouts,
camera hardware and real-world OCR accuracy need separate validation.
