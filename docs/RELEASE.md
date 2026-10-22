# Release process

## POC previews

User-authorised POC distribution uses the separate `Publish mealf POC preview` workflow,
triggered by an immutable `poc-YYYYMMDD.N` tag after all six main-branch CI jobs pass on
that exact commit. It requires no full-product acceptance assertion and cannot publish
`latest-stable`. Both native-architecture images receive fresh unsuppressed security scans
and Docker persistence/restore smoke checks; only those saved image bytes are published.
The resulting manifest has GitHub provenance and a prerelease with scans, SBOMs, Compose
and OpenAPI. See [installation, scope and limits](POC.md). Do not move a published POC tag.
Check the resulting GHCR package visibility and verify an anonymous pull before claiming
public installation works. Repository visibility does not prove package visibility.

### Preview retries and version ownership

New preview workflows check for a completed prerelease before any build or registry write.
A matching completed prerelease with its pinned image digest is a successful no-op on retry;
its images, release assets and notes are not changed. Only a genuine GitHub 404 permits a
new publication. Authentication, rate limits and other API failures stop the workflow.
Draft/stable/mismatched releases and missing immutable image references require inspection.
If an image tag was partially pushed without a completed release, publication refuses to
replace its base or architecture tags; use a fresh version after reviewing the failed run.
If a push event has not started CI, open Actions → Backend checks → Run workflow and select
`main`. This performs the identical full matrix. The preview gate accepts successful `push`
or `workflow_dispatch` runs only for the exact main-branch commit and expected repository/
workflow; unrelated branches, PR runs and incomplete/skipped matrices still fail closed.
Create the fresh release tag only after that exact source passes.

All six exact-source CI checks and both fresh image scans/runtime checks still precede every
new image. The moving `preview` channel alone is intentionally updated.

Rerunning an older workflow uses its historical tagged source and cannot publish newer main
changes. This guard applies to new tags containing it; the existing `.4` tag is never moved.
The historical `.4` rerun at 15:20 UTC rebuilt and pushed digest
`sha256:45df776761e17fbbea13ff5552c0be2b8917bf27b51bd793c4147d4e21bd8e67`
before duplicate release creation failed. The original `.4` release notes still pin digest
`sha256:15cb248de58ed490d0b893b08832451d144f94e357ed2190d963f852a1a0a410`.
Use immutable digests to reproduce either verified build; the old source has neither the new
palette nor the PWA gesture changes. The new release uses a fresh version.

First publication: `poc-20261021.1` from 4deb195 passed source CI 39607765691 and preview
publication 39608095928. Both architecture scans and native Docker checks passed. Anonymous
pull and published-image E2E subsequently passed; exact digest/assets/provenance/evidence
are in validation/github-poc-preview.json. Full stable acceptance remains open.

Bash compatibility update: `poc-20261021.2` from 366e391 passed exact-source CI 39610992728
and preview publication 39611318654. Both native images pass terminal/token/runtime checks
and fresh security scans. Anonymous pull and the published AMD64 .1-to-.2 same-volume
upgrade on internal port 5152 passed; see validation/github-bash-preview.json.

Startup setup-token log update: `poc-20261021.3` from 1282fa4 passed exact-source CI
39612946770 and preview publication 39613320058. Both native architecture checks bootstrap
from Docker logs and exclude further token records after setup. Anonymous pull, same-volume
.2-to-.3 upgrade on internal 5152, token reuse before setup, configured silence and operator
opt-out passed. See validation/github-setup-token-log-preview.json for exact evidence.

Supplied-artwork update: `poc-20261021.4` from 9d73633 passed source CI 39619768791 and
publication 39620210006. Both architectures verify original/derived/packaged assets and
fresh image scans. Anonymous pull and the published AMD64 .3-to-.4 household/session/recipe/
sync-proof upgrade on internal 5152 passed. See validation/github-mealf-artwork.json.

Combined design/gesture/retry update: `poc-20261021.5` from d15b37a passed all six exact-source
CI jobs in 39628446235 (226 backend tests per architecture, 39 web tests). Publication
39629099312 attempt 1 passed fresh native image scans/Docker checks and published both
verified images at digest
`sha256:269302c1e209d2a8d93834450c6a0af7aea242a6005a4240e8683d1475d62d0b`.
Public pull, six asset checksums, report/config identities and a disposable same-volume
original-digest `.4` → `.5` upgrade on internal 5152 passed. An actual gate-job retry
(attempt 2) passed with verify-images/publish skipped; the image digest and release body,
asset IDs and checksums stayed unchanged. This verifies the completed-release no-op path.
See [exact source, images, jobs and limits](validation/github-preview-retry.json).

## Stable releases

### Current candidate/stable policy

The PWA v1 scope is frozen; see [readiness and execution order](V1_READINESS.md) and
[machine-readable acceptance](release/v1-acceptance.json). No gate is marked passed
without concrete evidence. A candidate is not a production claim.

Prepare matching `pyproject.toml` and `src/mealf/__init__.py` versions: PEP 440
`1.0.0rc1` for tag `v1.0.0-rc.1`, or `1.0.0` for `v1.0.0`. Beta/arbitrary suffixes,
leading-zero versions and mismatched API/package versions are rejected. The full six-job
main-branch CI matrix must pass on the exact tagged commit. That CI installs the OCR
language packages before the tests; the release gate does not run an incomplete substitute.

Both native architectures are rebuilt, freshly scanned without HIGH/CRITICAL suppressions,
and exercised with the existing Docker persistence/restore smoke. The verified images are
saved and only those bytes are pushed to `ghcr.io/cloudcookch/mealf-server`; publication
does not rebuild them. SBOMs and provenance accompany the image. `compose.release.yaml`
pins its default to the actual published manifest digest and retains the existing Compose
project/volume settings. Existing operators should update their own image reference while
retaining their volume, ingress and custom port/command/healthcheck (including 5152:5152).

RC publication uses the `release-candidate` GitHub environment and moving `:rc` channel;
GitHub releases remain prereleases. Stable uses the separately protected `release`
environment and `:latest-stable`. Configure required reviewers and restricted tag policy
in repository settings before using it. The stable environment must additionally contain
`RELEASE_ACCEPTANCE_VERIFIED=true`, and all 14 evidence-backed gates must be passed in the
version-matching acceptance JSON. The variable alone cannot bypass open gates.

Completed matching releases are successful no-ops on retry. A partially pushed version
without a completed matching release is never overwritten: inspect the failure and use a
fresh version. Authentication/rate-limit/network errors do not make a release tag free.
These rules have synthetic regression coverage; the first real RC and stable protected
environment rehearsal remains a release gate. Workflow code is not proof of configured
GitHub environment protection or successful live distribution.

The following early release notes are historical; the executable policy above supersedes
their old release-workflow description.

Both repositories and their first CI runs are published. Configure private vulnerability
reporting and a protected `release` environment before publishing. CI runs locked tests,
format/type checks, OpenAPI drift, Docker E2E, pip-audit, redacted Gitleaks and Trivy.
Action references are commit-pinned; Renovate proposes reviewed updates. Scanner databases
need external network access. A configured scanner is not evidence of a clean scan.

Only after every product acceptance gate passes: set independent server version/changelog,
review migration and compatibility notes, create an immutable `vX.Y.Z` tag and approve the
protected publication environment. The release workflow checks version/tests/contract,
builds AMD64/ARM64, emits SBOM/provenance, publishes GHCR tags and an attestation, and creates
a GitHub release with generated notes and the OpenAPI artifact. `latest-stable` is reserved
for actual stable releases. Prerelease tags must not be used to trigger this stable-channel
workflow without first adapting its tag/channel policy.

Initial GitHub backend tests, browser workflows and Docker smoke checks pass. Security
scanning initially stopped on a removed upstream action dependency; the updated pinned
action and current v0.70.0 scanner now execute. The previous Debian image still failed
the vulnerability gate; the Alpine replacement passes the local AMD64 scan and awaits
the native AMD64/ARM64 CI matrix. The former v0.67.2
GitHub release is no longer available; the newer release and its asset checksums were
verified through GitHub metadata. Container scanning and
acceptance gates must be required checks on the release commit before tag creation; the
workflow is not a substitute for that policy. Reproducible wheel packaging/build-toolchain
pinning and a complete release attestation review remain outstanding.


The protected distribution environment must define `RELEASE_ACCEPTANCE_VERIFIED=true`
only after documented product, security and release acceptance is actually complete.
It is intentionally unset for this development implementation.

## Peach interaction preview

`poc-20261021.6` from `183c91f19f984a33aeec4fb31d5497f82fd3e0bf` passed all six
exact-source CI jobs in run 39634556996 (226 backend tests per architecture and 39 frontend
tests). Publication 39635000477 passed fresh native AMD64/ARM64 Docker and security checks.
The image index is `sha256:6b5963edc90c4943cbaa351f7f491b60cb8c905196c73433d4f065cc00c31740`.
Anonymous pull, all six asset checksums, report/config/build identities and a disposable
published `.5` → `.6` same-volume upgrade on internal 5152 passed. Shared peach assets
match source bytes and are precached; original art, manifest identity, household/session/
recipe/sync proof persist. See [exact evidence](validation/github-peach-preview.json).
Physical Safari/iPhone and full-product acceptance remain unverified.

## Phone viewport preview

`poc-20261021.7` from `b8e2b1b3e114df58ca17dcd23c8651342208cc0c` passed all six
exact-source CI jobs in 39638277178, including real Chromium/WebKit layout checks with
simulated safe areas. WebKit uses disposable persistent profiles because its ephemeral
session rejected staging the real demo image Blob; production storage is unchanged.
Publication 39638823438 passed both fresh architecture scans and Docker runtime checks.
The image index is `sha256:49d8e3eed44a2cd2940eb5b08b6e33b04abf72aefe62eee9df52d439c47355ee`.
All six release assets, public pull, image config/report/build identities and a disposable
published `.6` → `.7` same-volume upgrade on internal 5152 passed. Packaged CSS includes
the minimum mobile font, text autosizing and safe-area rules. Original assets, sessions
and household data remain intact. See [exact evidence](validation/github-phone-viewport-preview.json).
The reported physical-phone installation/keyboard behavior still needs operator confirmation.

## Mobile calendar preview

`poc-20261021.8` from `4d614b0e21b9393db00d1fcd98108b9ca529e7d6` passed all six
CI jobs in 39645754201, including Chromium/WebKit calendar interaction and form-geometry
checks. Publication 39646222333 passed fresh native AMD64/ARM64 security and runtime
checks. The image index is `sha256:211e26f02798b199f1606b0417847dc7d52400e0108a4ca00672e088ee552fe2`.
Public pull, six asset checksums, build/config/report identities and the published
`.7` → `.8` disposable same-volume 5152 upgrade pass. New calendar/pointer/grid code
ships; household/session/recipe/sync proof and original assets persist. Duplicate tag
event 39646224899 succeeded at the release gate and skipped verify-images/publish.
Physical iPhone gestures/keyboard remain unverified. See [exact evidence](validation/github-mobile-calendar-preview.json).

Theme-library update: `poc-20261021.9` from a9659effcd6bb85b77b37e1a81022fc9bd4c4823
passed all six source jobs in 39652782031, including complete Chromium/WebKit theme,
offline, native-control, contrast/Axe and narrow German layout checks. Publication
39653391814 passed both fresh native scans/runtime gates and published digest
`sha256:9cc1e8f386c4c47792727b52a0408564c0e1dc486514270167e57eb777ac10e8`.
Public pull, all six release checksums, native build/scan/published config identities and
a disposable published .8-to-.9 same-volume upgrade on internal 5152 pass. Both SBOMs
identify Trivy 0.70.0, with zero HIGH/CRITICAL findings in both reports. Provenance,
job IDs, intermediate browser findings and platform limits are recorded in
validation/github-themes-preview.json and validation/mealf-themes-local.json.
Physical iPhone and full-product acceptance remain open. Keep existing volume and custom
port/command/healthcheck settings; update only the image and accept the PWA update after
saving edits. No browser reset or reinstall is required.

Photo import is published in `poc-20261021.10` from db207a2. Exact-source CI 39665948052
passes all six jobs with 240 backend tests per architecture and 45 web tests; browser
coverage includes actual OCR, offline image/edit reload and explicit save in Chromium
and trusted-HTTPS WebKit. Headless WebKit explicitly models native push unavailable;
push opt-in behavior retains separate synthetic fixtures and live delivery is unverified.
Publication 39666575713 passes both fresh native image scans/runtime gates. Public asset
checksums, native-build/config/scan identities, anonymous pull and the published AMD64
.9-to-.10 same-volume 5152 upgrade plus real EN/DE OCR pass. Preserve user volumes,
custom command/healthcheck and 5152:5152; accept the PWA update without clearing storage.
Exact digest, jobs, prior failed test-helper attempts, attestation, assets and limits:
validation/github-image-import-preview.json. This remains a development preview.
