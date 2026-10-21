# Deterministic recipe import and review

Website imports first use Schema.org/JSON-LD. Supported social host names identify the
source but do not grant access to private captions, videos or transcripts. Public retrieval
retains HTTPS, DNS/address pinning, redirect bounds, timeouts and size limits. User-supplied
structured text follows the same preview path. Optional AI remains separately configured
and requires explicit content-transfer consent; no AI is needed for the parser below.

The `metric-en-de-v1` parser recognises explicit amounts, numeric ranges, ordinary and mixed
fractions, common Unicode fractions, metric units and a bounded set of English/German
tablespoon/teaspoon/piece aliases. Decimal commas are accepted when unambiguous. For example,
`1½ EL Olivenöl` becomes 1.5 tbsp of Olivenöl; `½–¾ TL Salz` retains both ends of its range.
`salt to taste` and `Salz nach Geschmack` keep an unknown quantity and their preparation note.
Original text is retained within the documented 500-character field limit.

Do not infer ingredient translation, density, nutrition or package weight. Ambiguous
thousands/decimal separators (`1,000` or `1.000`), unsupported imperial/packaging measures,
invalid fractions and reversed ranges remain unparsed for correction. Non-terminating
fractions use the API's bounded decimal precision; their original text remains available.
Simple comma-separated preparation notes are retained; complex linguistic parsing is not
claimed. Units such as cups/spoons are not guessed into grams or millilitres. Shopping
normalisation combines only compatible metric dimensions and known aliases.

Import provenance records deterministic parsing and required review. The draft always
includes quantity/serving/image notices; malformed/omitted entries and shortened content
receive additional explicit warnings. The iOS editor presents translated review notices
within its scrollable form. Native rendering still requires Apple verification.

An import job producing `preview` does not create a library recipe. Only the explicit
confirmation mutation saves it. Tests cover parsing, preserved uncertainty, decimal serving
scaling, compatible-unit aggregation, pantry exclusions and this confirmation boundary.
The Docker smoke workflow exercises the durable worker, fraction preview and confirmation
through real HTTP before backup/restore.

## Terminal source retention

Confirmed/cancelled imports retain minimal replay/provenance metadata. After a 30-day
completion grace period, maintenance can clear their extraction previews and concluded source
job payloads while preserving identical-request/confirmation replay and the saved recipe.
Unreviewed/failed-input drafts and unknown legacy receipts remain intact. A late worker cannot
downgrade confirmation. Internal receipt/retention fields stay server-side; see RETENTION.md.
