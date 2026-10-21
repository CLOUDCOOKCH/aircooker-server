# Dependency attribution and distribution review

Project-authored code uses Apache-2.0; dependency copyrights and licences remain separate.
The recommendation and API ownership are recorded in ADR 004. No third-party endorsement
or right to redistribute imported recipe text/images is implied.

`licenses/runtime-approval.json` pins the installed versions and declared licence expressions
of 34 runtime Python wheels. This is a change-review baseline, not a legal-clearance report.
`docs/validation/runtime-wheel-licenses.json` records the lock digest and SHA-256 of the
installed wheel attribution files. The scanner does not download or execute package code.

```sh
python scripts/license_inventory.py --check
```

The check requires the hashed runtime lock to be installed. It fails on a version or
licence-expression change, missing installed notice, empty notice or changed baseline.
CI runs on AMD64/ARM64 and retains the platform's inventory with its test artifact. Release
validation repeats the check and attaches the inventory alongside OpenAPI. These workflow
configurations are not evidence that a release has been published.

For a deliberate dependency update, inspect upstream licence text/source and bundled
components first. Run `--write-approval`, review the manifest/report diff and commit the
updated lock and baseline. Never regenerate an approval automatically in CI to hide drift.
For older metadata, the exact `Apache 2.0` spelling normalises to `Apache-2.0`; all other
expressions are retained, including conjunctions/disjunctions.

The current declarations include MIT variants, BSD-3-Clause, Apache-2.0, PSF-2.0 and MPL-2.0.
`bring-api` 1.1.2 declares MIT. `certifi` declares MPL-2.0, and `orjson` declares
`MPL-2.0 AND (Apache-2.0 OR MIT)`; preserve their notices and applicable source-availability
obligations. Do not describe every dependency as Apache-licensed. The runtime installs
unmodified wheels and retains their `.dist-info` attribution files; deleting build wheels
does not delete installed notices. The standalone project licence does not replace them.

## Remaining release gates

Review actual pinned source and redistribution obligations beyond metadata. Inventory
bundled native libraries/Rust crates, the Python standard library, SQLite, Alpine packages,
development tools and GitHub Actions separately. In particular, an Alpine container can
redistribute GPL-licensed BusyBox/readline components even though application code uses
Apache-2.0. Supply applicable copyright notices and corresponding source/distribution
arrangements; an SBOM alone does not satisfy those obligations. No blanket compatibility
or legal-compliance claim is made by the wheel check.

The iOS runtime has no external Swift package dependencies; Apple system frameworks and
SQLite are system components. XcodeGen/Mint and build tooling still require their own
inventory. AI/Bring service terms, social-source access policies, Apple review requirements
and recipe/image rights remain separate reviews. Do not publish a stable image or app
until the documented release-acceptance gate covers these remaining checks.
