# BOTBRIDGE1 preflight correction confirmation

2026-11-01. Scoped documentation check only; no new source audit or build.

**Verdict: all four preflight remedies are incorporated in DESIGN-DRAFT.md and IMPLEMENTATION-PLAN-DRAFT.md.** The superseding clarification in FINITE-IMPORT-DESIGN-NOTES.md explicitly overrides its older empty/deduplicated-first-page wording.

- Generation/start/deadline and request reservations persist before subscription; interrupted reservations consume budget, including terminal incomplete handling for interrupted initial getState without a stored snapshot.
- Progressing empty/deduplicated differenceSlice responses continue; response kind and finite failure/budget conditions determine termination.
- Weak lifecycle registrations are namespaced and generation-qualified, capped at 32, with no active-target eviction and callbacks outside the lock. Soft reset preserves the continuing recorder; stale deinit cannot unregister its replacement.
- History exports explicitly include safe numeric tuples/counters/reasons, and otherUpdates inspection is capped at 10,000 per page before mutation or additional arrays.

Runtime interpretation requirement: Bot A “reading only” means no deliberate send/reply/reaction/media/edit/delete/post action. Opening or reading chats may still emit modern read receipts or consumption acknowledgements. Include a finite `read_ack` control category in the closed diagnostic method allowlist for the existing modern read/ack methods verified at implementation; retain submitted/result/error events without payload inspection. Keep these events visible beside the last deliberate interaction so a read acknowledgement is not mislabeled as text/reaction or hidden as “no outbound activity.” Do not suppress modern read behavior to make Bot A network-silent. A bounded fixture should prove the category and unchanged request behavior; broad protocol research is unnecessary.

The documents did not yet contain the literal `read_ack` category at this check; this paragraph supplies the requested narrow addition for plan finalization. Existing modern app GREEN and later implementation/build/device proof remain unchanged. No additional approval gate or architecture rewrite is required.
