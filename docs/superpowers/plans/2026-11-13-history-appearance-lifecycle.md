# History, appearance and lifecycle implementation plan

**Goal:** Restore deeper bot history, soften the scoped Wallet panel, retain the Beta 2 label, implement local native profile appearance, and complete the separate bounded lifecycle wave.

**Baseline:** GREEN Build180, published `fbefb07215542ab2d453a62d03d30336a67b1668`, Actions43258189305; local equivalent tree3c7809484c168233af53813133fd783869b081cf. Telegram13.2 `24638bc69bd083981b178dd1e7f921eebbf7fc46`.

**Architecture:** New reversible builder-owned successors; preserve all accepted32+4stages and Wave2A.1. Native Telegram renderers consume account-scoped presentation data, never rewritten database peers. Performance work stays on its requested branch and is not merged automatically.

**Spec:** User attachments6e894716 (Wave2A.2),152231c2 (appearance), and the November13 strict account/bot isolation requirements in this chat.

## Global constraints

- Stable account record ID plus own Telegram peer ID and environment; fail closed for missing own user or botInfo.
- Own active account only; temporary expiry per account; local store resides in that account's Postbox and cannot leak after logout.
- No Premium spoof, server appearance setters, global hooks, live protocol/retry changes, layout I/O, or new renderers.
- No user-account runtime operations; device testing belongs to user. Do not claim full history without server/device evidence.
- Preserve Telegram/Xcode/Bazel/signing/BundleID. One planned build per completed independent candidate.

## Review focus

- Existing terminal importer records must not permanently block the new deeper history policy.
- Historic replay never rewinds live AuthorizedAccountState or resurrects locally deleted messages.
- A→B→A and A→Bot→A reject old account callbacks; missing peer data never enables override.
- Expired status restores the real server status; a server peer refresh cannot erase an enabled local choice.
- Hidden About requests cancel without cancelling other Settings/account subscriptions; reopening resubscribes once.

## Tasks

- [x] Verify green baseline and reproduce its selected source hashes locally.
- [x] Audit old bot backfill vs Build180 request cursor, import, hole and terminal policies. Add behavioral fixtures before changing replay admission/resume.
- [x] Add a separate exact successor for history fixes and scoped translucent Wallet; preserve historical patches. Restore visible Beta2 identity consistently.
- [x] Audit current native appearance models, picker, palettes and render boundaries. Implement one account-local store with expiry and real bot guards; native pushed Settings controller and preview. Integrate only own-peer rendering with lifecycle-owned change subscriptions.
- [ ] Exercise isolation, migration, expiry, no server mutation, and the native API boundaries against current13.2 declarations. Verify apply/reapply/reverse/corrupt refusal.
- [ ] Publish the product candidate and run preflight/app build; observe startup only and retain artifact/run link. Device runtime remains pending.
- [ ] On `perf/build180-wave2a2-request-lifecycle` from the same green baseline, prove up to2lifecycle defects; implement only proven fixes with before/after component counts and exact independent overlay.
- [ ] Run the planned performance CI if a real fix exists; no automatic merge, release, or further waves.

## Superseding user instruction

User requested all changes in one build. Integrate reviewed Wave2A.2 as a new exact successor after native appearance; one product workflow/IPA. Cancel the two superseded runs. Prior independent-branch/no-auto-merge instruction is superseded by this explicit request. No further performance wave.
