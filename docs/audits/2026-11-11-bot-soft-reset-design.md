# BOTBRIDGE routine reset and retained softReset repair design

2026-11-11. Design only against `../jerkgram-next/beta2/saved-tags/source` (paths below are relative to that snapshot's `submodules/`). No implementation, staging, manifest, Git, or CI change. The bounded derived export summary is `.superpowers/sdd/2026-11-11-beta3-followup/user-export-analysis.json`; no raw user export is copied here.

## Evidence and cause

The new device evidence supersedes the earlier recon's statement that no export was supplied: two fresh history starts each reserved the initial state request, then encountered `softReset` with zero examined/inserted/committed messages. Later sessions restored terminal `softReset`, reservation count 1, and made no history retry. The parent investigation matched the first initial-state cancellation to `Account.resetStateManagement()` about 46 ms after history start. The 1,458 unknown-method RPC failures with numeric code 400 have no error names and cannot be attributed to history.

The routine startup call is source-proven: `TelegramUI/Sources/SharedAccountContext.swift:772` invokes `account.resetStateManagement()` when adding the created AccountContext. `Account/Account.swift:1873` has already requested history startup during Account initialization. `Account.resetStateManagement`, line1931, reports diagnostic `.softReset, terminal:false`, explicitly cancels bridge history, then resets the modern manager. The diagnostic call already invokes the installed cancellation closure: `JerkgramBotBridgeDiagnostics.swift:208–223` calls `cancelHistory(kind)` regardless of the `terminal` flag. `terminal:false` means keep the diagnostic scope open; it does not mean keep the importer alive. The explicit second cancellation is redundant.

Cancellation is irreversible for this Account: `AccountStateManager.swift:2368` cancels its single `private let botBridgeLifetime`; the implementation disposes its `private let botBridgeStartDisposable`; and the controller persists a sticky terminal. Merely calling `jerkgramStartBotBridgeHistory` again cannot resume it.

## Recommended smallest protocol: preserve history across a routine manager reset

Distinguish routine state-manager activation/reset from a genuine authentication soft reset. The former must observe lifecycle without invalidating history. Keep genuine `network.didReceiveSoftAuthResetError` and `authKeyUnknown`, logout/removal/cleanup/deinit cancellation semantics intact.

Concrete proposed changes:

1. Add finite diagnostic lifecycle case `stateManagementReset` to `BotBridgeDiagnosticLifecycle`.
2. In `BotBridgeDiagnosticScope.lifecycle`, exempt `.stateManagementReset` from `cancelHistory`, alongside the existing observation-only exceptions. Use it only with `terminal:false` (prefer an explicit assertion/precondition or dedicated owner helper to prevent callers freezing it accidentally).
3. In `Account.resetStateManagement()`, replace its diagnostic call with `.lifecycle(.stateManagementReset, terminal:false)` and remove its explicit `jerkgramCancelBotBridgeHistory(reason:.softReset)`. Leave its existing `stateManager.reset()` and ordinary contact/sticker/preload work in place.
4. Do not move history to a separate queue, restart the controller, reopen a lifetime, or change generic operation behavior.

This is smaller and safer than a pause/resume implementation because the existing manager already preserves custom operations across reset:

- `AccountStateManager.Impl.reset`, line445, clears `operationDisposable`, calls `replaceOperations(with:.pollDifference(...))`, and invokes `startFirstOperation`.
- `replaceOperations`, line570, retains the currently running operation and collects pending `.custom` operations, appending them after its replacement live poll.
- Crucially `.custom` activation, line1112, starts its subscription with `let _ = ...start(...)`; it does **not** install that subscription in `operationDisposable`. Therefore clearing `operationDisposable` does not dispose a running bridge lease. This is an important distinction from generic assumptions about reset.
- A running custom remains first and marked running; the manager must not start a second subscription. On completion its existing callback removes it and starts the next live operation. Pending bridge custom work is retained behind live work. `didStore` continues to yield between pages normally.

Consequently the importer need not wait for a vague “reset complete” event. Initial state/response work may finish before, during or after routine reset, still using its existing generation/lifetime/request gates. A reset initiated while a live operation is running may delay the bridge, but grants no additional reservation, watchdog window, wall deadline or request budget. The active 10-second lease bound remains in force. Repeated routine resets do not rearm any terminal.

The diagnostic owner stays admitted once in the same scope/epoch. No unregister/admit cycle is needed and no frozen owner is reopened. A genuine auth reset still invalidates before snapshots; later routine resets cannot revive that cancelled lifetime. The existing explicit duplicate cancellation in the genuine auth-reset callback can remain for this minimal patch (or be addressed separately with a pre-admission safety analysis); removing cancellation there indiscriminately would weaken cancellation when no diagnostic scope has been admitted yet.

## One-time retained-record repair, before admission

Stopping future self-cancellation does not repair existing `.softReset` preferences. Add a narrowly scoped migration inside `jerkgramPrepareBotBridgeHistory`, after the existing confirmed bot/authorized-state validation and **before** diagnostic admission or controller creation. Do not use `jerkgramRenewBotBridgeGeneration` as a generic retry entry point; that function remains the successful-authorization entry point.

Add an additive field `softResetRecoveryVersion: Int32` to `BotBridgeHistoryProgress` (default0 in initializer and `decodeIfPresent(Int32.self,...) ?? 0`; encode as keyed Int32; validate `0...1`). Preserve schema1 and the existing key. Proposed helper: `botBridgeRecoverInitialSoftReset(_:owner:accountPeerId:testing:) -> BotBridgeHistoryProgress`, pure policy called from that existing preparation transaction. Eligibility must require all of:

- the record decoded successfully and is valid, with exactly matching record owner, peer and testing environment;
- `.terminal == .softReset` and `softResetRecoveryVersion == 0`;
- the proven initial-state interruption shape: `reservedState == true`, `original == nil`, `candidate == nil`, `next == nil`, `reservedPages == 0`, `committedPages == 0`, and all message/peer/delete/skip/unsupported/missing counters zero.

Construct a fresh progress value with the same owner/peer/testing, a new UUID generation and version1; persist it atomically in the preparation transaction. It has no old reservation or deadline. The old lifetime belongs to a dead Account at upgrade/relaunch, so no runtime replacement or owner readmission is involved. Any concurrently active/preparing predecessor remains subject to lifetime and exact-generation checks; tests must demonstrate old reservation/terminal writes cannot affect the new generation. Never migrate an already admitted controller in place.

This grants one bounded recovery generation, not an automatic retry loop. Its normal policy remains one state request plus at most32 difference requests, <=20,000 examined messages, 120-second wall budget and <=10-second active operation watchdog. For the eligible retained record the cumulative granted upper bound is its one previously consumed state request plus33 recovery requests (34 total), explicitly rather than silently resetting an unlimited lifetime budget. Version1 persists through every terminal and ordinary relaunch/reset; it must not become0 through terminal writes or validation fallback. Only a genuinely successful new bot authorization can begin an independent authorization generation. An old `.softReset` record with committed history, an interrupted reservation without `.softReset`, corrupt/foreign data, an unrecognized version, or any other terminal remains stopped for a separately reviewed repair policy.

The fresh 120-second recovery window is intentional: retaining the historical expired wall deadline would make this migration unable to repair the observed retained accounts. This exception is granted exactly once by persisted version, never by startup count. If policy requires preserving a strict across-upgrade 120-second budget, automatic recovery of these old records is impossible; expose an explicitly authorized new generation instead.

## Required tests before implementation is considered ready

Extend `tests/fixtures/botbridge1/controller.swift` and its extraction harness with **actual manager reset/replace/custom activation methods**, not only the simplified fixture manager. The current fixture proves controller behavior but cannot prove production manager reset ordering.

- Fresh history reserves state; routine Account reset executes before response: zero cancellation, one state request, matching response accepted, one difference subscription follows; no stuck running operation or double completion.
- Reset before preparation returns, before custom activation, during active state RPC, during state storage, during active difference RPC and between pages. Repeated resets consume no additional history requests or deadlines and yield to live operations. Exact custom operation IDs survive replacement and complete once.
- Genuine auth soft reset, unknown auth key, logout/removal/deinit still synchronously invalidate lifetime, dispose active RPC, reject late callbacks/transactions and preserve their terminal. Routine reset after genuine cancellation cannot resurrect history. Logout before diagnostic admission still prevents any request.
- Actual Postbox keyed codec: old valid initial-state `.softReset` fixture decodes version0 and migrates once to version1/new UUID; serialize/relaunch never migrates again, including if recovery itself ends `.softReset` or times out. All negative eligibility cases remain unchanged. Unknown versions fail closed without becoming migration eligible.
- Migration transaction compares the exact validated record; stale old generation state/page/terminal writes fail. Distinct record IDs, namespace/account manager instances and testing environments cannot influence one another. Ordinary users and supplementary Accounts remain excluded.
- Diagnostics lifecycle fixture: routine `.stateManagementReset` emits a snapshot without cancellation/freeze/registration detach; genuine `.softReset` still cancels; no second owner admission or live-target registry eviction occurs. Existing privacy and bounded-storage fixtures continue to pass.
- Existing terminal, monotonic/wall clock, 32-page, 20k-message, duplicate/deleted-message and no-live-state-replacement tests remain passing. New optional field must use real Postbox Int32 encoding, never synthesized Codable Int or raw enum encoding.

## Proof boundaries

This repair addresses a local lifecycle race and exactly the retained failure shape observed in the export. It preserves the sole modern manager, existing network, current authorized/live cursor, bounded historical cursor heuristic and import transaction behavior; no live PTS rewind, global hook, alternate poller, new queue or forever retry is introduced. It does not prove a server will return read/all-time bot history. Unread0 can still produce `.noCandidate`; server empty/tooLong/error outcomes remain honest finite results. Real-device follow-up must show the new routine reset snapshot, accepted state response and ensuing bounded history terminal/counters. Database/UI visibility requires actual inserted-message evidence. Unknown 400 RPC failures remain unattributed.
