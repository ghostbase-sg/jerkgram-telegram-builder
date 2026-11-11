# Local Premium and Saved Tags implementation plan

> Latest user steering: retain this recovery as a reviewed local base. Do not publish or launch a separate recovery IPA. Implement Local Premium (TASK A) and Saved Messages Tags (TASK B) as separate descendant commits, then review and build one combined release. This supersedes the earlier recovery-first delivery order below. Native/device gates remain pending.

Spec: `docs/superpowers/specs/2026-11-05-local-premium-saved-tags.md`.

## Global constraints

Execute after the reviewed recovery stage on its actual accepted source. Reuse current checkout and descendant feature branch. TASK A and TASK B are separate commits; internal B tasks may remain uncommitted until their reviewed integration forms the one Task B product commit. Preserve recovery, native entitlement checks and Translation behavior. No new Premium scope, swizzling, global polling, backup-format expansion or wholesale history scans. Real supported persistence codecs and native gates are required; do not claim device success from source/CI. Keep immutable evidence and exact reversible source stages. User authorized implementation/publication/build and requested only a few minutes of IPA monitoring.

## Task 1: TASK A native Hub and exact stage

Read premium-settings audit and spec before changes. Confirm current recovery parent/identity and copy its materialized owners into a new draft, preserving originals. Modify reachable `.home`, existing page enum/title/entries/actions, localized strings and existing icon helper only as necessary. Reuse official Premium Settings resource; group existing four controls as specified. Retain old entries as coherent aliases unless an evidenced refresh risk warrants moving them. Preserve all persisted key/scope/default/setter semantics, unique IDs and native push.

Add focused source/state tests for reachable navigation/native resource, no new renderer/store/entitlement mutation, RU/EN, no settings writes on open, aliases/back refresh, scopes and defaults. Add exact Hub terminal materializer/verifier/manifest and reverse-parent test view; all-parent refusal before any write and reapply/reverse tests. Review compliance and quality, then commit Task A independently. Do not publish an IPA with incomplete Tags advertised.

## Task 2: TASK B durable indexed store

Read saved-tags audit, inspect actual Postbox schema allocation/transaction/view patterns and current patched semantic mutation owners. Select free table IDs only after verifying all current registrations. Implement versioned durable definitions/primary membership/reverse page/direct-ID metadata indexes and transaction revision/counts, with validated fixed-width codecs and finite decode limits. Exact quotas/name/identity constraints are in the spec. Account isolation follows store path plus explicit service generation; no account-global map.

Add real table/transaction or smallest real ValueBox integration tests, not only a dictionary model: create/rename/delete, idempotence/multi-tag, atomic batch admission, quota rejection preserving old rows, reopen durability, malformed codec values, stable Saved-copy identity, account separation, indexed oldest-of-1,001 paging and bounded result allocation. Record measured query costs without extrapolating to device FPS. Review this task before the UI uses the store. Keep changes staged for Task B, not an extra Task A commit.

## Task 3: TASK B account facade and semantic lifecycle

Expose async account-local operations/snapshots and cancellable typed page provider in the existing dependency direction. Bind account/environment/generation; reject stale completions; no UI-thread I/O, per-cell store reads or global launch subscription. Missing page content uses bounded ordinary ID reads and unavailable/retry rows, never tag mutation or membership deletion.

Integrate confirmed interactive/shared/global-ID/replay/range/thread/full-history cleanup transactionally with current product owners; preserve existing retention behavior. Cache eviction and failed content reads retain memberships. Edit/refetch retains identity and updates index metadata only when necessary. Verify uncached ID cleanup, original-forward deletion independence, account switch/removal, process interruption and all accepted deletion scopes. Review the task's code and test evidence.

## Task 4: TASK B native UI and complete local filter

Implement native tag management/editor with RU/EN locality, quota/error and no-backup text. Native Saved context menu and batch selection support create/select/add/remove/mixed states without touching reaction entitlements or underlying messages. Add distinct local strip/filter domain and native bounded result list provider: 45-row pages, at most three windows, cancel on filter/pop/account switch. One selected tag; disable local text query explicitly. Native cloud tags remain on their original path.

Test native owner wiring, correct selected IDs including albums/copies, no API mutation, empty tags, rename/delete-active-filter, offscreen/oldest paging, unavailable-content navigation/retry and request/window bounds. Verify all presentation state copies/equality and clear-filter behavior. Review scoped implementation. No fake reaction bytes or native 500-result fast-path reuse.

## Task 5: TASK B exact stage, integration and release

Generate exact Tags stage after accepted Hub, include real source/build declaration owners and localized strings. Reverse views restore prior gates without weakening them. Test all-parent refusal/no mutation, reapply, exact reverse and correct source view for historical/Hub/Tags/recovery checks. Keep App Icons/Boost/No Ads/Translation unchanged from accepted Hub. Verify archive unchanged and explicit tag backup limitation.

One broad whole-branch review plus scoped corrections. Commit Task B separately from Task A. Synchronize actual next build identity using proven dependent hash transformations; do not pick a number from the plan blindly. Publish reviewed tree with expected-head lease; run mandatory macOS/native/source checks, then a product IPA build. Monitor first few minutes and report real run/status without waiting for IPA completion. Deliver concise summary, detailed owners/files/commit/test evidence and iPhone runtime matrix with unresolved limits explicitly marked.
