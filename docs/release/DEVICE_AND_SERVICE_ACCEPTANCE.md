# Device, integration and household acceptance

Use a versioned candidate and record image digest, source SHA, device/OS/browser version,
date, result and a redacted issue/evidence reference for every scenario. Keep credentials,
private recipe content and raw logs out of repository evidence. Synthetic/engine tests do
not close physical or live-service gates. These checks do not require a Mac.

## Real iPhone / installed PWA

- Install from Safari over valid HTTPS, launch from Home Screen, sign in and reopen.
- Use Flo, After Dark and Sunday in both OS appearances; check portrait, landscape,
  notch/home indicator, large text, VoiceOver, reduced motion and the software keyboard.
- Create/edit a recipe with an image, fractions and a range; verify serving scaling.
- Use Day/3 days/Week; drag a meal between dates/categories, scroll at edges, cancel a
  gesture, and use the accessible move form. Check plan-dialog date/select alignment.
- Take a camera photo and choose a screenshot; confirm local OCR produces a preview,
  correction is possible, and no recipe exists until explicit Save.
- Disconnect networking, edit recipes/plans/pantry/leftovers, queue an import, close and
  reopen. Reconnect and verify every pending operation and image reaches the backend once.
- Edit on two devices, replay an interrupted sync, expire/revoke a session, and test a
  deletion versus an offline edit. Incorrect device clocks must not change write order.
- Install an application update while an editor and queued changes exist. Finish saving,
  accept the update and verify the draft/outbox survives. Never clear site data as a fix.
- Exercise restored-server history detection, archive/rebuild and recovery export. Record
  browser storage persistence/eviction behavior and verify the documented recovery route.

## AI providers

For every provider/model advertised as supported, explicitly configure documented formats
and run text plus every enabled image/PDF/video input. Record the model and destination,
not its key. Verify consent, uncertain/missing facts, refusal/truncation, invalid JSON,
unsupported formats, rate limits/timeouts and changed-provider consent. No preview should
auto-save; credentials must never appear in browser responses or logs. Disable undocumented
capabilities. A successful connection probe alone does not verify all file formats.

## Bring! dedicated test list

Use a dedicated account/list with identifiable manual items; never a real household list.
Record connector capability flags and an initial read-only snapshot. Test additions, owned
updates/removals, manually entered duplicate names, purchases, an increased requirement,
unit incompatibility, calendar changes, leftovers, pantry exclusions and weekly rollover.
Interrupt a batch, lose a response, restart the backend and retry. Verify idempotency and
that no manual item is adopted, modified, completed or removed. Missing UUID-safe semantics
must keep automatic mutations disabled. Record API/permission/rate-limit failures clearly.

## Web Push

On a real installed iPhone PWA and a supported desktop browser, test permission grant,
denial and later changes, test notification, configured meal reminder, rescheduling after
calendar changes, category disable, timezone/DST, reconnect and revoked sessions. Delivery
is connected best-effort browser Web Push, not exact offline iOS local alarms. Document
actual OS limits; never infer vendor delivery from injected worker events.

## Household pilot and operations

- Rehearse fresh setup and container terminal/log recovery on the supported host.
- Back up a synthetic household, restore to a clean volume, compare recipes/media/plans/
  templates/pantry/preferences and exercise offline-device reconciliation afterward.
- Upgrade from the last published preview with the same volume, custom `5152:5152`
  command/healthcheck and credentials. Keep the original volume/snapshot for rollback.
- Verify explicit data deletion/recovery behavior and explain offline device copies and
  separately retained operator backups accurately.
- Run normal meal planning/importing/shopping through a weekly rollover. Log material
  defects and repeat affected acceptance after fixes. Record a maintainer pilot decision.

Update v1-acceptance.json only with actual evidence. The administrator supplies/configures
external accounts locally; automated tests stay synthetic and live checks remain opt-in.
