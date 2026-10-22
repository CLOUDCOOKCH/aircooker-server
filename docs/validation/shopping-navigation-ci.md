# Shopping navigation: browser-gate investigation

The navigation change is implemented without API, persistence or native changes. During
main-source CI at c403651, real WebKit layout/themes and all functional image-import
assertions passed, but the image-import harness reported a native fetch diagnostic as an
uncaught page error during the intentionally stopped backend. Attempts 2 and 3 reproduced
this; attempt 1 instead exhausted the 300-second WebKit dependency-download limit.

An isolated trusted-HTTPS diagnostic run passed once, then a repeated run captured the
native identity: name `Fetch API cannot load https`, message containing the fixture's
`/api/v1/sync/state?cursor=0`, and a native diagnostic stack. The exact request also emitted
`requestfailed` with connection refused while the backend was deliberately offline. No
window `error` or `unhandledrejection` event occurred. All functional assertions completed.
See diagnostic runs [39751287844](https://github.com/CLOUDCOOKCH/aircooker-server/actions/runs/39751287844)
and [39751637293](https://github.com/CLOUDCOOKCH/aircooker-server/actions/runs/39751637293).
Playwright 1.62.0's WebKit adapter maps `source=javascript`, `level=error` console messages
to page errors and splits the first colon, which here is the HTTPS URL's scheme separator.

The harness now independently records every real window exception/unhandled rejection;
these always fail. It classifies only the exact observed native message for a matching
failed sync-state request during the explicit HTTPS loopback outage. Other engines,
origins, routes, messages, stacks and online errors remain fatal. Native diagnostics are
counted and reported in browser evidence. Thirteen unit cases cover matching transport,
missing/outside-outage requests, forged/unrelated errors and genuine window failures.
This is an explicit test-oracle correction; no app exception handler, TLS setting, CORS
policy, offline storage behavior or functional assertion has been weakened or replaced.
The dependency installer retains a bounded timeout, increased from 300 to 600 seconds.

Local Chromium image-import/OCR/offline checks and classifier tests pass. Full regression
and repeated WebKit evidence for this correction remain pending until their runs finish.
The temporary diagnostic workflow is isolated on a test branch and is not part of the fix.
No physical iPhone or live-service acceptance is asserted.
