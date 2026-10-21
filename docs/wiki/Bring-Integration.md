# Bring! integration

MealF can project the current household shopping week into a selected Bring! list.
This is an **unofficial integration**, with no affiliation with Bring! Labs AG.
Review Bring!'s current terms and use a dedicated disposable list for compatibility
testing. Live service compatibility has not been verified by synthetic connector tests.

The backend stores credentials and contacts Bring!; the PWA does not receive those
credentials or call the service directly. An installed app is not required to stay open
after a calendar change has synchronised to the backend.

## Connect an account and list

1. Sign in to the administration console at `/` and open **Bring!**.
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

The source checkout includes `scripts/bring_compatibility.py`. It is an explicit live
experiment, not a runtime container command. It creates a unique test item, checks
UUID-based replay/update/completion/removal and verifies existing items remain intact.
It must run only against a dedicated disposable test list, with your deliberate consent
to those external mutations.

From an environment with the project's pinned Python dependencies, prepare private
credential files and set:

```sh
export BRING_EMAIL_FILE=/secure/bring-email
export BRING_PASSWORD_FILE=/secure/bring-password
export BRING_TEST_LIST_ID=REPLACE_WITH_DEDICATED_LIST_UUID
export BRING_DEDICATED_TEST_LIST=YES
export BRING_COMPATIBILITY_REPORT=/secure/bring-compatibility.json
python scripts/bring_compatibility.py
```

Replace the paths/UUID, restrict the credential files and keep passwords out of shell
history. Do not run this on a normal household list. Install a genuinely successful
generated report at `/data/config/bring-compatibility.json` in the backend volume,
readable by UID 10001 with restricted permissions. Do not fabricate or edit a passed
report. A report for one list does not authorise a different list.

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
