# mealf v1 production readiness

The v1 scope is now frozen. New features wait until the following production gates are
closed; fixes, validation, recovery and documentation continue. This is a **PWA/server v1**.
The original native product specification remains a later milestone and is not declared
complete by a PWA release. A Mac, signing certificates and App Store approval are not
requirements for this PWA milestone.

## Frozen scope

One self-hosted Docker container, one shared household with independently revocable device
sessions, SQLite WAL and persistent `/data`. Primary navigation remains Home, Calendar,
Recipes, Pantry and Settings, using the supplied original mealf artwork, glass surfaces,
Flo/After Dark/Sunday themes, English/German and accessible non-drag alternatives.

Recipes support structured ingredients, scaling, notes, ratings and images. Planning covers
breakfast/lunch/dinner, Day/3 days/Week, moving/copying meals, bounded recurrence with
exceptions, saved templates, leftovers and pantry-aware recommendations approved before
calendar changes. Offline viewing/editing uses persistent local drafts and an outbox,
server-ordered replay, tombstones and explicit recovery; unsynchronised work is never
silently discarded.

Imports cover public structured website recipes, user-supplied text, local EN/DE photo OCR,
and optional configured AI text/image/PDF or supported Gemini video inputs. Every import
needs editable review and explicit Save. Source-specific access failures keep manual content
entry available; no private social fetching, access bypass or universal transcript support
is promised. Optional AI must disclose its destination and supported model capabilities.
Bring! is a backend-only connector; ownership-safe live reconciliation is a release gate,
not inferred from synthetic connector tests. Opt-in Web Push also needs live validation.

The administration console covers secure setup, household/security/integration settings,
diagnostics and validated data transfer. Complete, documented restore, household deletion,
upgrade and device-recovery behavior must be verified before stable distribution.

Native WidgetKit, Face ID, the native Share Extension, exact local iOS alarms and App Store
release remain on the native roadmap. Pure PWA feature parity is not claimed. Browser
storage can be evicted and background execution is limited; foreground/reopen sync,
recovery exports and connected Web Push are the supported browser model.

## Gate register

[Machine-readable acceptance](release/v1-acceptance.json) is the authoritative checklist.
Only `passed` entries with concrete evidence permit stable publication; `partial`, `open`
or `blocked` entries fail closed. Do not mark a gate passed just to trigger a release.

| Gate | Current evidence and remaining work |
| --- | --- |
| Core workflows | 279 backend and 50 frontend tests plus Chromium/WebKit and native Docker checks pass for merged source 932e2ce; expanded recurrence and published-candidate checks remain |
| Offline/recovery | Atomic outbox/replay/tombstone and snapshot archival tests exist; guided non-recipe recovery and browser recovery-import UX remain |
| Backup/upgrade | Consistent SQLite backup and transactional JSON/ZIP merge restore exist; candidate disaster-recovery and compatibility rehearsal remain |
| Deletion | Interactive offline command, running-server exclusion, interruption/resume, explicit backup choice and fresh identity have unit coverage; packaged Docker verification and operator/device rehearsal remain |
| Resources | Configurable SQLite growth cap, real FULL rollback/retry, persistent client outbox and worker/shutdown recovery have tests; slow-client/load, physical disk faults and decoder stress remain |
| Security | Dependency/secret/container gates run; the dedicated repository audit is blocked because its required preflight assets/tools are unavailable in this session |
| Physical iPhone | Home Screen install, keyboard/camera, safe areas, drag/cancel, VoiceOver and update/offline lifecycle require real-device evidence |
| Live services | Supported AI models, dedicated Bring ownership/purchase/rollover and actual push delivery need credentials/device evidence |
| Distribution | Exact-source CI, native scan/runtime verification, immutable retries, verified-byte publication and RC/stable channel separation must be rehearsed on a real RC |
| Operations/pilot | Fresh install and documented recovery must be exercised, followed by household pilot sign-off |

Synthetic fixtures are explicit test doubles, not successful external integration claims.
The [device/service checklist](release/DEVICE_AND_SERVICE_ACCEPTANCE.md) records the checks
that require external access. No production user data or credentials belong in evidence.

## Execution order

1. Publish the merged functionality as a new `poc-*` preview after exact-source CI and both
   fresh image gates. Verify public pull, assets and upgrade using isolated synthetic data.
2. Complete the recovery/deletion/resource work and audit. Keep a reviewed, tested commit
   per bounded change; do not disable failing checks or rewrite released migrations.
3. Prepare matching `1.0.0rc1` package/API versions and tag `v1.0.0-rc.1`. The release workflow
   publishes the immutable version and moving `:rc` channel only; it cannot advance stable.
4. Close the independent live-service and physical-device gates on the candidate using the checklist.
5. Run the household pilot, fix material issues and repeat affected checks on a fresh RC.
6. Record all production evidence, set both package/API versions to `1.0.0`, require exact
   main-source CI and approve the protected `release` environment. Only then publish
   `v1.0.0` and `:latest-stable` from the verified native image bytes.

This document and workflow code do not themselves establish production acceptance.
