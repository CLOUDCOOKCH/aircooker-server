# Release process

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
action and current v0.70.0 scanner still need successful execution. The former v0.67.2
GitHub release is no longer available; the newer release and its asset checksums were
verified through GitHub metadata. Container scanning and
acceptance gates must be required checks on the release commit before tag creation; the
workflow is not a substitute for that policy. Reproducible wheel packaging/build-toolchain
pinning and a complete release attestation review remain outstanding.


The protected distribution environment must define `RELEASE_ACCEPTANCE_VERIFIED=true`
only after documented product, security and release acceptance is actually complete.
It is intentionally unset for this development implementation.
