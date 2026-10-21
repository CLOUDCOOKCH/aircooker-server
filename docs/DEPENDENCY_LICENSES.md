# Dependency attribution and distribution review

Project-authored code uses Apache-2.0; dependency copyrights and licences remain separate.
The recommendation and API ownership are recorded in ADR 004. No third-party endorsement
or right to redistribute imported recipe text/images is implied.

`licenses/runtime-approval.json` pins the installed versions and declared licence expressions
of 40 runtime Python packages. This is a change-review baseline, not a legal-clearance report.
`docs/validation/runtime-wheel-licenses.json` records the lock digest and SHA-256 of the
installed attribution files and the pinned app-shipped supplemental notice. The scanner does not download or execute package code.

```sh
python scripts/license_inventory.py --check
```

The check requires the hashed runtime lock to be installed. It fails on a version or
licence-expression change, missing notice, empty notice or changed baseline. The sole reviewed
exception is http-ece 1.2.1: its upstream sdist/wheel omits LICENSE. An exact upstream MIT
notice is shipped in the application package, pinned by version, expression and SHA-256 in
`licenses/supplemental-attribution.json`, which also records the source commit and sdist hash.
A missing/tampered supplement or changed version fails; unknown missing notices still fail.
CI runs on AMD64/ARM64 and retains the platform's inventory with its test artifact. Release
validation repeats the check and attaches the inventory alongside OpenAPI. These workflow
configurations are not evidence that a release has been published.

For a deliberate dependency update, inspect upstream licence text/source and bundled
components first. Run `--write-approval`, review the manifest/report diff and commit the
updated lock and baseline. Never regenerate an approval automatically in CI to hide drift.
For older metadata, the exact `Apache 2.0` spelling normalises to `Apache-2.0`; all other
expressions are retained, including conjunctions/disjunctions.

The current declarations include MIT variants, BSD-3-Clause, Apache-2.0, PSF-2.0 and MPL-2.0.
`bring-api` 1.1.2 declares MIT. The reminder addition pins pywebpush 2.5.0 and py-vapid
1.9.6 (MPL-2.0), http-ece 1.2.1/charset-normalizer 3.5.2/urllib3 2.8.0 (MIT), and
requests 2.34.2 (Apache-2.0); existing pinned package versions are unchanged. Preserve
MPL notices and applicable corresponding-source obligations when distributing these
unmodified dependencies. `certifi` declares MPL-2.0, and `orjson` declares
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

POC `.2` deliberately adds the unmodified Alpine `bash=5.3.9-r1` package for container
terminal compatibility. It is GPL-3.0-or-later, separate from the Apache-2.0 application;
its GPLv3 text is packaged in `aircooker/attributions/bash-GPL-3.LICENSE`, and Bash's own
version output retains the Free Software Foundation copyright/licence notice. The Alpine
packaging recipe at `alpinelinux/aports` commit `1522c3193610902d8493f9790a2755c11f21f26d`
(`main/bash/APKBUILD`, 3.24-stable) records the GNU Bash 5.3 source, vendor patches 001–009,
Alpine patches and source SHA-512 values. The architecture-specific preview SBOMs record
the installed package and libraries. The broader OS corresponding-source review above
remains a stable-release gate; this does not relicense Bash as Apache or claim legal clearance.

The iOS runtime has no external Swift package dependencies; Apple system frameworks and
SQLite are system components. XcodeGen/Mint and build tooling still require their own
inventory. AI/Bring service terms, social-source access policies, Apple review requirements
and recipe/image rights remain separate reviews. Do not publish a stable image or app
until the documented release-acceptance gate covers these remaining checks.

## Browser client

`frontend/licenses/bundled.json` pins the reviewed declarations/versions for six bundled
runtime JavaScript packages plus Vite's generated preload helper. The build recursively
checks runtime dependency names, rejects version/licence drift, copies complete attribution
texts (including Lucide's inherited icon notices), and emits `THIRD_PARTY_NOTICES.txt` plus
`dependency-licenses.json` into the public client. Type-only packages are not bundled.
This is a reproducible attribution/declaration check, not full legal clearance. npm's locked
full dependency graph is audited separately in CI; Node and build packages are absent from
the final Python runtime image. Continue the existing OS/bundled-library/source obligations
review before stable distribution.
