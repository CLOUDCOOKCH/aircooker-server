# Bring! integration

This is an **unofficial** shopping-list integration. There is no affiliation with Bring!
Labs AG. The operator must review the current service terms and limitations.

The backend alone calls Bring. The app is not a second shopping-list product. The server
expands the current household-local Monday–Sunday week, skips existing leftovers, scales
servings with decimal arithmetic, normalises safe units and excludes available pantry
staples. Grams and millilitres remain separate; unknown/ranged quantities are preserved.
Language aliases are deliberately limited to known units; ingredient translations are not
guessed.

## Configure

Authenticated API operations:

1. POST `/api/v1/integrations/bring/connect` with email/password. They are encrypted in
   `/data/config/bring.enc` using a separate restricted `/data/config/integrations.key`.
   Saved credentials are not a claim that authentication succeeded.
2. GET `/api/v1/integrations/bring/lists` performs read-only authentication/list retrieval.
3. PUT `/api/v1/integrations/bring/configuration` with `list_id`. Membership is checked.
4. Verify the SDK and dedicated selected test list with the compatibility experiment.
5. POST `/api/v1/integrations/bring/reconcile` queues work; inspect jobs/status for the result.

The administration console's Bring! section supports connection, existing-list selection,
status, reconciliation and disconnection. See the [Wiki setup guide](wiki/Bring-Integration.md).
Do not put passwords in shell history. Use the console or a secret-aware administrator tool.
Disconnect deletes the saved credential and compatibility report, without deleting external
list content.

## Packaged compatibility verification

The PWA now offers the same explicit dedicated-test-list experiment through its durable
worker. See [Shopping list](SHOPPING.md). No shell or external script is needed. Reports
now also bind the exact saved credential/list configuration; old unbound reports must be
verified again. Ordinary writes validate returned UUID/state before marking success.

## Source-only compatibility experiment

Run only against a dedicated disposable test list. The probe does not run by default.
Set `BRING_EMAIL_FILE`, `BRING_PASSWORD_FILE`, `BRING_TEST_LIST_ID`,
`BRING_DEDICATED_TEST_LIST=YES`, and optionally
`BRING_COMPATIBILITY_REPORT=/data/config/bring-compatibility.json`, then execute:

```sh
python scripts/bring_compatibility.py
```

The developer script is present in the source checkout, not installed as a runtime package command.
Its report path must be the configured server config directory so it can bind the saved connection.
Run it from an environment with the pinned SDK. Its assertions must pass; do not hand-write
an affirmative report. Reports expire after 30 days and match SDK 1.1.2 plus the selected
list UUID. This deliberate gate means unverified automatic mutations remain disabled.
Live service smoke tests were **not** run during development.

## Ownership and reconciliation

The ledger records period, internal requirement, list UUID, item UUID, desired spec, applied
spec, state and reconciliation time. An identity is persisted before a remote add, so retry
after a lost response uses the same UUID. Name-only mutation methods are never used.
Manually created same-name entries are left alone and never adopted. Only ledger-owned
UUIDs can be updated or removed. A purchased or user-removed requirement stays suppressed
for its shopping period. Purchased requirements are conservative: increasing the same
requirement does not silently recreate it. A precise additional-requirement model remains
outstanding. New periods use independent IDs; completed history remains preserved.

Calendar mutations commit and enqueue work together. The worker retries with exponential
backoff, stores redacted errors, and polls at minute intervals for purchased changes/weekly
rollover. Eight consecutive attempts can mark a job failed; manual retry or a new meal
change requeues it. No iOS background execution is required once the server has the change.

Automated tests prove preservation of manual items, duplicate suppression, UUID replay,
purchased suppression and rollover using synthetic connectors. They cannot prove external
atomicity or service stability. The unofficial API has no guaranteed compare-and-swap;
read/write races and external changes require continued live compatibility testing.
