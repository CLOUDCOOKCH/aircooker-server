# Bring! integration

MealF can project the current household shopping week into a selected Bring! list.
This is an **unofficial integration**, with no affiliation with Bring! Labs AG.
Review Bring!'s current terms and use a dedicated disposable list for compatibility
testing. Live service compatibility has not been verified by synthetic connector tests.

The backend stores credentials and contacts Bring!; the PWA does not receive those
credentials or call the service directly. An installed app is not required to stay open
after a calendar change has synchronised to the backend.

## Connect an account and list

1. Sign in to the administration console at `/admin/` and open **Bring!**.
2. Enter the Bring! account credentials and save them. Saving alone does not verify login.
3. Connect/retrieve the available existing lists.
4. Select a list returned for that account and save the selection.
5. Review connection and capability status before expecting automatic writes.

Credentials are encrypted at `/data/config/bring.enc` using the installation's restricted
`integrations.key`. Keep both in a protected full-volume backup. Disconnecting removes
the saved connection and compatibility report without deleting existing Bring! items.

## Why automatic writes can remain disabled

A successful account login and list retrieval do not prove that the unofficial API
supports safe UUID-based changes. MealF requires a current compatibility report matching
the selected list UUID and the supported SDK. The current gate expects SDK `1.1.2` and a
report no older than 30 days. The console cannot override a failed or missing report.

Use **Calendar → Shopping list → Verify Bring! compatibility** to run the packaged check
inside the Docker container. First select a dedicated disposable test list, then explicitly
confirm it. The worker tests one persisted temporary UUID for add/replay/update/completion/
removal and verifies baseline items remain unchanged. A failed identity check keeps writes
blocked and may leave a `mealf-test-…` item for manual cleanup. No terminal is required.

The result is specific to the exact saved credentials/list and SDK and expires after 30 days.
Changing lists/accounts requires new verification. Do not test on a normal household list or
fabricate a passing report. Source-only developer tooling remains in
`scripts/bring_compatibility.py`; the [shopping guide](../SHOPPING.md) documents the supported
operator workflow, per-item states, offline snapshot and manual **Sync to Bring!** button.

## Shopping behaviour

The backend uses the current Monday–Sunday week in the **household time zone**. It
scales ingredients to servings, combines compatible metric units, excludes available
pantry staples and skips meals using existing leftovers. Unknown/ranged quantities
remain explicit; it does not guess density, translations or package weights.

**Include in shopping this week** temporarily includes an available staple for that
shopping period. It expires for the following week. Offline edits retain the week
selected on the device, even if they reach the backend after rollover.

The ownership ledger tracks the external UUIDs MealF created. It never adopts manual
same-name items and only updates/removes ledger-owned UUIDs. Purchased or manually
removed requirements remain suppressed for that shopping period. Increasing an already
purchased requirement does not silently recreate it; finer additional-quantity handling
remains unfinished. A new week uses independent requirement identities.

## Reconcile and troubleshoot

Use the console's reconciliation action when available, then inspect queue/job status.
Queued work is not evidence that Bring! changed. The worker retries temporary failures
with bounded backoff and polls for purchases/week rollover. Repeated failures can become
terminal; review the safe error code before retrying.

If nothing appears, check saved credentials, list membership, selected list, report age,
matching SDK/list UUID, outbound connectivity and the current household week. Never
disable the capability gate to make an unverified connector write. External API changes
and races remain live-service risks.

Source: [Bring! engineering guide](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/BRING.md)
and [compatibility experiment](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/scripts/bring_compatibility.py).
