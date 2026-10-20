# Validation evidence — 2026-10-20

This report describes a development implementation, not completed product acceptance.
No real household, Bring account, cloud AI credential or Apple signing credential was used.

| Check | Executed result | Limit |
| --- | --- | --- |
| Backend tests against hashed runtime dependencies | **60 passed** | One upstream Starlette TestClient/httpx deprecation warning; no failure |
| Ruff lint and format | Passed | Python source/tests/scripts only |
| mypy | Passed across 19 application modules | `check_untyped_defs`, not exhaustive strict typing |
| OpenAPI regeneration/drift | Passed | Version 0.1.0, API-major/sync-protocol 1/1 |
| iOS vendored contract checksum / fields / paths | Passed | Does not replace Apple SDK or semantic integration tests |
| Swift core compile and tests | **24 passed**, Swift 6.2.1 Linux | No SwiftUI/UIKit/WidgetKit/Keychain/Face ID runtime validation |
| Swift source formatting and native syntax parse | Passed | Syntax parsing is not Apple framework type checking |
| Localisation parity | 146 EN/DE keys and static localised error lookups passed | Human translation/a11y audit outstanding |
| Docker build | Passed, linux/amd64 | ARM64 publication/runtime not executed |
| Docker E2E | Passed | Real HTTP + SQLite; synthetic household, no Bring service |
| Chromium administration console | Passed | Loopback development origin; production TLS ingress not validated |
| Source Gitleaks 8.28.0 scans | No findings in both repositories | Build outputs/installed tooling excluded, source tests included |
| pip-audit 2.9.0 on runtime lock | 34 packages, no known advisories reported | Advisory database coverage is finite |
| Trivy 0.67.2 | **Gate fails: 44 HIGH package matches across 8 unique advisories; 0 CRITICAL** | Remaining matches have no fixed version listed; exploitability not adjudicated |
| Workflow YAML / scanner TOML / export plist | Parsed | No GitHub/macOS workflow executed |

Docker E2E verifies non-root/read-only startup, token-protected setup, HTTP authentication,
idempotent mutation replay, recipe/meal persistence and scaling projection, server restart,
replayed offline edit, immutable photo upload/replay, exact photo bytes after restart,
JSON v2 and streamed ZIP restore into independently configured clean containers. It does not substitute for a physical two-device iOS workflow.

Earlier browser checks exercised first-run setup, login, dashboard, EN/DE switching, mobile width,
CSRF logout and absence of JavaScript errors. Screenshots are genuine Chromium output with
a synthetic household: [desktop](screenshots/admin-desktop.png),
[German mobile](screenshots/admin-mobile-de.png). No fabricated iOS screenshots exist.

## Container security result

The initial Python 3.12.12/Debian 12 image had 9 critical and 91 high package/advisory
matches. It was replaced with the verified multi-architecture Python 3.12.14/Debian 13 image
pinned by digest. Published PCRE2/OpenSSL package fixes were installed at exact versions.
The resulting candidate has no critical matches and no remaining matches with published
fixes in the scanner's data, but still fails the configured HIGH/CRITICAL gate.

See [machine-readable container findings](validation/container-security.json) and
[dependency audit](validation/dependency-audit.json). Forty-four matches represent eight
unique advisory IDs repeated across binary packages, not 44 independently validated
application vulnerabilities. They must be triaged against actual runtime paths and tracked
until remediated or explicitly resolved with evidence. No scanner suppression was added.
The first Trivy mirror was unavailable; the supported GHCR database repository succeeded.

## Not verified / incomplete

Native Xcode 27 build, iOS 26/27 simulator/device, UI tests, share/widget lifecycle,
notifications, native photo-picker/cache UI, accessibility, macOS signing and TestFlight upload remain
unverified or incomplete. No live Bring compatibility report was generated. No live AI
provider was contacted. Social source-specific captions/transcripts are incomplete.
GitHub repository creation/publishing was not possible through the shell (`Forbidden`);
remote workflows and releases do not exist yet.

Media tests additionally cover metadata stripping, file/pixel/quota limits, immutable
identity, archive traversal/corruption, duplicate rollback, historical deletion/provenance
restore, CSRF and chunked upload bounds. Swift tests cover photo/outbox restart and failed
transaction rollback, lost response replay, local schema upgrades, bounded recurrence,
exceptions, civil-date arithmetic, detached moves, template recipe references and atomic
copy batches. Native photo/calendar UI sources were formatted and syntax parsed only.

See IMPLEMENTATION.md for remaining independent work: leftover/recommendation interfaces,
complete admin settings, destructive restore, cleanup and sync conflict recovery UI. External credential gaps do not excuse these missing features.
