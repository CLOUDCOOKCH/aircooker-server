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

## Stable releases

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
