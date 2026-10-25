# Corrected Build170 excluded-chat behavior

User correction: keep the same chat in the regular chat list with locally available history, title/avatar/known participant metadata. Read-only after exclusion, footer replaces composer. No separate archive screen as the implementation of this feature. Publication is paused by the user.

Implementation choice: preserve the native account-specific Postbox dialog and messages. Add a local-only retained-exclusion bit to group/channel peer flags; keep actual Removed/kicked membership and incoming restrictions. Mark only a known member transitioning to excluded while enabled, or an already retained excluded peer. Never retain voluntary leave. Preserve last known metadata when a forbidden response strips it, without preserving administrative permissions. Central peer-update and chat-list exclusion logic respect this local marker. Manual deletion clears it so subsequent forbidden refreshes cannot resurrect the dialog. Rejoin clears it.

UI: suppress kick-triggered dismissal only for a retained peer; show locally cached history despite the inaccessible-history overlay while keeping server membership unchanged; static noninteractive exclusion footer; guard reactions, votes, replies/edit/send paths. Keep normal info screen and already cached participant data. No promise of fresh participant lists or inaccessible attachments after server access is revoked.

Checks: exact-stage application/reversal, old source contracts, Foundation policy truth table/lifecycle regressions, native syntax and full IPA compile on macOS. Device checks: foreground/background kick, restart, history/metadata, no write/reaction/vote, explicit deletion, rejoin, account isolation. Local source checks cannot establish runtime correctness.

Participant handling: persist actually loaded recent channel members (bounded4096) in per-account Postbox cache collection63, below application-specific64. Read the snapshot after kick; no network request for the retained recent list. Clear on manual deletion/rejoin. Legacy groups reuse cached participants. No invite-members control on retained peers.
