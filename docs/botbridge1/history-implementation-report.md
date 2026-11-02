# Task 1 implementation report — source review candidate

Status: **DONE_WITH_CONCERNS** for the scoped source package. Native fixture execution, generated-source collision scan, application compilation, runtime/controller integration and device proof remain pending. This source draft is not the final integrated solution. No materializer/stage/CI wiring, commits, pushes or full build were performed.

## Provenance and package

Modern GREEN: builder `5ba6add985d6995ca102d4e40d8da66e98f443c1`, run `41372637134`, native and app SUCCESS, IPA artifact `13111834999`; upstream fixed at `279f89e4d4f63f17227bf877dc3d8990f22ecd58`.

Package root: `/home/pixi/ChatGPT/iOS DEV/jerkgram-next/botbridge1/task1/`.

- `before/`: genuine `build177-appfix2-source` (403 product/non-.git files plus 142 copied .git metadata files), plus ten previously missing official inputs. Every added input was verified using Git blob SHA1 against `research/official-1312/PROVENANCE.json` before copying its exact bytes to both trees. `BASELINE.json` records all original and added bytes, with SHA256 and added-input provenance. It is frozen and has not been edited after creation.
- `source/`: the only edited product tree.
- `SOURCE.patch`: unified before → source patch, paths rooted at `submodules/`.
- `SOURCE-MANIFEST.json`: six changed/new product files and before/after SHA256 values.

All 403 common product files and 142 copied .git metadata files were compared again against the genuine input and matched. The 555-entry frozen manifest contains these 545 copied files plus ten official inputs; the product/non-.git total is 413. Parent independently verified this distinction in TASK1-PROVENANCE-CHECK.json. The original build177 source, historical research, original Projects source, and stable branch were not changed. Tests verify all frozen baseline bytes, unchanged modern worker/converter hashes from `MODERN-WRITE-BASELINE.json`, the exact native `.pollDifference` case, the generic custom-operation method, and the existing inclusion algorithm.

## Changed product files

1. `submodules/Postbox/Sources/Postbox.swift`: public `Transaction.addHistoricalMessagesWithoutInteractiveActions(_:)`; delegates to the same `.Random` insertion with `runInstalledActions: false`. Existing `addMessages` bytes are unchanged. The shared implementation has a default-true argument and conditions only the two installed callback dispatch blocks. Index/tag/hole/message-history code is unchanged.
2. `submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift`: new progress/cursor/policy, exact authorization validation, storage helper, finite controller, owned request lease, typed no-op history event hook.
3. `submodules/TelegramCore/Sources/State/AccountStateManager.swift`: replaces active BotShadow pager with manager-owned controller and append-one-custom-operation scheduling. Generic custom machinery and native poll/difference remain unchanged. Synchronous lifetime-token invalidation precedes the cancellation queue hop.
4. `submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift`: only removes `private` from `jerkgramIncludeBotMessagePeers`; algorithm bytes are preserved.
5. `submodules/TelegramCore/Sources/Account/Account.swift`: starts the confirmed-bot bridge for primary accounts; removes only BotShadow's process gate and dedicated logout suppression; cancels on network logout, soft auth reset, public state-management reset and Account deinit. Existing unrelated safety branches remain.
6. `submodules/TelegramCore/Sources/Authorization.swift`: one call inside the successful bot-authorization Postbox transaction; UUID generation is renewed only when the returned `TelegramUser` has botInfo. Other authorization paths are unchanged.

## Implemented behavior

One existing manager/Network/Postbox handles history. The bridge requests only updates.getState and updates.getDifference with automaticFloodWait false. It selects `max(1, Int64(pts)-Int64(unread))`, preserving current qts/date/seq. The first difference payload is imported rather than discarded; no live state is installed or replayed. Empty/deduplicated progressing slices continue. Final and empty responses terminate, tooLong terminates unavailable, and malformed/nonadvancing/regressing cursors stop.

Per-Postbox Codable progress at `0x4A470002` includes schema, record owner, confirmed account peer, environment, nonsecret opaque generation, original/candidate/next tuples, original wall start/deadline/observations, request reservations, committed-page counters, inserted users/chats/messages and finite terminal reasons. Existing bots initialize from the validated Account record only once. Corrupt, mismatched or unreadable progress fails closed. Reserved getState without a stored snapshot terminates interruptedState on restart. Page reservations survive crashes and consume the same 32-attempt budget; committed cursor/page counters are atomic with storage.

Bounds: getState + 32 difference reservations, 10 seconds per active request/page lease, original 120-second wall deadline with per-process monotonic remaining time, 5,000 messages / 10,000 peers / 10,000 otherUpdates per page, 20,000 total examined messages. No bridge retry or terminal automatic rerun. Encrypted payload conversion is unsupported and counted (count >10,000 also fails closed). Reference-count validation fails closed above 100,000 missing references in a page; these conservative validation caps do not grant extra requests.

Parent-approved resource refinement: inspect delete vector lengths before allocating sets; permit at most **20,000 delete IDs per page**, aggregated across updates. An oversized vector or aggregate overflow terminates limit before peer/message mutation. `deleteIdsObserved` is numeric; on rejection it records the capped 20,001 marker instead of materializing or exporting the oversized vector. Same-page deletion sets are bounded and membership checks avoid quadratic candidate/update/vector scanning.

Storage converts with the existing modern StoreMessage converter, keeps current forum/peer metadata, accepts full cloud IDs only, deduplicates by first occurrence, skips every existing ID including edited/live/deleted placeholders, and excludes same-page or known-session deleted IDs. Only absent referenced peers are inserted with an existing-wins closure. Existing archive/pins/cutoff and inclusion behavior are preserved. Other historical mutation updates are ignored, never applied. Deletion observations mark partial coverage; physical preexisting deletions without durable tombstones cannot be detected universally, especially after restart.

Request work belongs to the lease's MetaDisposable, not to the generic custom subscription. Completion, timeout, error and cancellation finish the lease through a once gate. Transactions check lifetime, account/environment, exact expected progress and request gate; cancellation can prevent mutation before the final guard, but cannot roll back an already begun atomic commit. Queued signals and callbacks use weak controller ownership. Completion precedes an asynchronous enqueue of the next page, allowing live manager work between pages.

## Tests and actual evidence

Builder additions: `tests/test_jg131_botbridge1_history.py`, and `tests/fixtures/botbridge1/{policy,postbox,storage,lease}.swift`.

RED before changes:

```text
python3 ../jerkgram-next/botbridge1/red-fixtures/run_red.py
exit 1: RED missing Postbox.Transaction historical insertion API
NOT RUN: 37 production behavioral cases; native driver unavailable/unconfigured
```

The initial focused suite also failed on the absent bridge, old active pager/suppression and missing callback suppression. Feature-absence native runners could not execute. The additional nested deletion-bound guard was observed RED (`missing nested delete-ID bound`) before the approved product refinement, then GREEN. These are source RED results, not proof of native behavioral RED. Runtime RED/GREEN has not been observed here.

Final focused command:

```text
python3 -m unittest discover -s tests -p test_jg131_botbridge1_history.py -v
Ran 11 tests; OK (7 passed, 4 skipped)
```

`JERKGRAM_BOTBRIDGE_SOURCE` selects an alternate source tree. Native harnesses compile/exercise extracted production code unchanged when swiftc exists:

- Foundation-only policy: candidate arithmetic, reservations versus commits, original deadline, backward wall clock, terminal rerun rejection, state crash before dispatch/commit, page response before commit, after-commit resume, zero-insert progressing slice, final dedup result, 32 attempts, corrupt counts and nonadvancing cursor.
- Exact Postbox public entries and shared insertion method: both callback kinds, mixed historical/ordinary calls in one Transaction, default callback order/payload/transaction identity, IDs, storage/index/tag boundary observations, Random versus UpperHistoryBlock. Interactive consume/readReaction/max-read, visible-reaction and wallet behavior use callback sentinels; this is not execution of the real TelegramEngine hook or a real database.
- Exact storage helper with unavoidable API/Postbox boundary facades: confirmed bot/ordinary user gate, existing edited/live/deleted placeholders, duplicate IDs, missing/unchanged/unrelated peers, archive/pins/cutoff sentinel preservation, same-page/session deletion exclusions, ignored mutation updates, progress/message atomic boundary observations, stale generation/token guards, oversized otherUpdates and nested/aggregate delete-vector bounds.
- Exact page lease: disposal/completion once, repeated finish/late callback gate, request installed after disposal immediately disposed, timer invalidation.

Linux has no swift/swiftc/xcrun. All four native fixtures are therefore SKIP, not PASS. The 37 original declarative cases were not claimed as executed. The complete controller with a fake serial scheduler/transport, actual Postbox rollback/DB behavior, actual interactive-hook integration and actual live interleaving are not established by these fixtures. Those require further source/unit/mock or macOS integration proof; a whole-worker/real-DB/device success gate has not been invented or claimed. No full repository suite or application build was run in this source-only package.

## Exact Task 2 interfaces

All are internal to TelegramCore, no new Account/Network/state owner:

```swift
AccountStateManager.jerkgramStartBotBridgeHistory(
    recordId: Int64,
    event: @escaping (BotBridgeHistoryEvent) -> Void = { _ in }
)
AccountStateManager.jerkgramCancelBotBridgeHistory(reason: BotBridgeHistoryReason)
BotBridgeHistoryController.start()
BotBridgeHistoryController.cancel(reason: BotBridgeHistoryReason)
```

The Account startup currently uses the no-op default. Task 2 should pass its bounded recorder event closure at that call; no second recorder/controller is needed. Cancellation invalidates the manager's lock-protected `BotBridgeLifetime` synchronously before entering the manager queue. Cancellation is idempotent. An Account lifetime is once-only; a later Account instance has its own lifetime and validates persisted generation/owner before resuming. Soft reset cancels history without suppressing modern auth behavior. The planned lifecycle registry must call this same cancel method on explicit logout-request/removal/replacement paths before Account deinit; current direct hooks cover network logout, soft reset, state-management reset and teardown, not a new registry.

`BotBridgeHistoryEvent` contains phase enum (`reserved`, `committed`, `terminal`, `handoff`), optional original/candidate/retrieval/live numeric tuples, reservedRequests, committedPages, examinedMessages, insertedMessages, insertedPeers, insertedUsers, insertedChats, deleteIdsObserved, skipped, unsupported, historicalDeletionObserved, missingReferences, optional finite reason, and `deletionCoverageLimited=true`. The live tuple field is optional and currently nil; Task 2 can supply an observed live snapshot without modifying live state. Event delivery occurs on the manager queue and must remain cheap; recorder callback must not perform I/O. Handoff means modern processing resumed with live state never replaced. No Account, API payload, peer/message ID, token, text or raw error enters the event.

Finite reasons: completed, noCandidate, tooLong, limit, deadline, clockChanged, corrupt, nonadvancing, rpcError, timeout, cancelled, replaced, loggedOut, softReset, interruptedState. The no-op event callback does not introduce temporary Logger output.

## Remaining limits / review gates

- Independent Task 1 review and scoped fixes are required before accepting this candidate.
- Full generated checkout key collision scan remains Task 3. Only the complete supplied 555-entry baseline snapshot (413 product/non-.git files and 142 copied .git metadata files) has been scanned here; no global uniqueness claim.
- swiftc execution of all native fixtures and actual application compile remain pending. No module/API or compile success is inferred from source checks.
- Complete controller timing/queue interleaving and explicit logout/removal registry callbacks need integration proof. The source lease/policy fixtures are narrower unit boundaries.
- Real storage indexes/tags/pending bookkeeping and actual open-chat observers need integration proof. Only the two audited installed insertion callbacks are suppressed; broader zero-network side effects are not proved.
- Durable physical-delete coverage, actual history availability, completeness, server behavior, relogin/device and multi-account runtime behavior remain experimental/device gates.
- Task 3 must materialize this patch authoritatively; no CI source inclusion is asserted yet.


# Task 1 review fix round 1 — R1, R2, R3, R4

This section supersedes the initial source-review package's missing-controller-fixture statement. It does not turn skipped native execution into a pass. The frozen `task-1-fix1-before`, `task1/before`, `BASELINE.json`, genuine modern177 input and official research were not modified. Product changes in this round are confined to `source/.../JerkgramBotBridgeHistory.swift`; the corresponding source patch and manifest were regenerated.

## Fixes

- **R1:** The custom signal installs its lease, arms an independent watchdog, then subscribes to the reservation transaction. The watchdog is bounded by ten seconds from operation activation and the original generation's remaining wall/monotonic time. The reservation result no longer creates or renews a timer. Expiry closes the request gate, disposes bridge work and completes the serialized operation once, even if Postbox never returns. A suspended transaction may still run later under Postbox's unchanged contract; its guard sees the closed gate and performs no reservation, dispatch or message/peer mutation. Terminal marking remains a separate generation-bound transaction.
- **R2:** The second policy-fixture commit now operates on `afterCommit`, which actually reserved the second request. A separate `unreserved` copy explicitly asserts that a second commit without a second reservation is rejected as corrupt. No production reservation rule was weakened.
- **R3:** Added `tests/fixtures/botbridge1/controller.swift` and its extraction runner. The runner inserts the **complete production controller**, actual `botBridgePage`/`botBridgeCursor` adapters, progress policy, actual storage helper, lease and preference/validation helpers unchanged. It shares the existing unavoidable API/storage boundary facades and adds deterministic serial-manager/queue/clock/timer, cold transport subscription/disposal, and suspendable-transaction facades. Facades implement I/O and serial completion contracts; they do not implement history selection, request reservation, page continuation, response adaptation or historical import logic. A portable check confirms exact full production type/function insertion with no unexpanded placeholders. Native compile/runtime errors now expose captured compiler/program output in the test failure.
- **R4:** Parse the bounded response chat vector once into a first-occurrence lookup plus ordered parsed array. Per-message forum lookup prefers current transaction peers and then performs a dictionary lookup; peer insertion reuses those same parsed objects. This preserves metadata/first-occurrence behavior and avoids up to 5,000 × 10,000 parsing attempts. The storage fixture counts actual chat-parser boundary invocations for 5,000 absent cloud-user destinations and 10,000 response chats and requires exactly 10,000 conversions.

## Controller fixture scenarios (present, native execution pending)

The actual extracted controller/response adapter is driven through: held reservation → watchdog → modern work proceeds → stale transaction released without mutation/dispatch; reservation wait consumes the existing lease window rather than renewing it; committed reserve-before-transport ordering; confirmed bot and ordinary user fast path; exact candidate request; consumption of first final payload; final/slice/empty/tooLong shapes; empty and dedup progressing slices; modern live operation between pages and content/inclusion preservation; nonadvancing/regressing cursor; no candidate; hanging request; RPC error without retry; cancel before activation, in flight, after response before transaction, during executing transaction before mutation, and after commit; late response and late suspended page transaction; generation replacement; two isolated Postboxes/lifetimes; crash after reservation commit before dispatch, response before page commit, and after page commit before callback; resume cursor/reservation accounting; terminal generation does not rerun; 32-page cap; original deadline/remaining-time timeout and backward wall clock; oversized ancillary updates. Assertions include custom-operation starts/completions and transport disposal counts.

This is a deterministic **source/unit/mock harness**, not a whole-worker, native DB or device success claim. The mock storage/index/inclusion boundaries retain the previously documented limitations. No new real-DB/whole-worker/device gate is required to review these fixes.

## Commands and observed results

Before the R1 product change, the focused command returned:

```text
python3 -m unittest discover -s tests -p test_jg131_botbridge1_history.py -v
Ran 12 tests; FAILED (failures=1, skipped=4)
FAIL test_active_watchdog_precedes_reservation_subscription:
'self.armWatchdog(lease)' not found in production schedulePage
```

After all round-1 changes:

```text
python3 -m unittest discover -s tests -p test_jg131_botbridge1_history.py -v
Ran 14 tests; OK (9 passed, 5 skipped)
```

Native skips: production policy/lifetime, complete controller/response adapter, real page lease, real Postbox methods, real storage helper. Swift compiler remains unavailable on Linux. Consequently no native compile or behavioral execution success is asserted for the corrected policy or the new controller/conversion-count scenarios. Their macOS execution remains mandatory during Task 3. The existing before-source/hash/modern-owner guards passed as part of the focused command; provenance was not redefined or regenerated.

## Task 2 contract and remaining work

No Task 2 interface changed: `jerkgramStartBotBridgeHistory(recordId:event:)`, `jerkgramCancelBotBridgeHistory(reason:)`, typed event fields, controller start/cancel, and synchronous lifetime-token invalidation remain as recorded above. The new watchdog is private. Ten seconds now explicitly bounds the **entire active custom lease including reservation wait**, rather than beginning only after reservation returns.

Independent rereview, native fixture execution and final generated-source/application integration remain pending. No stage, CI, commit, push, full build or unrelated product change was made in this fix round.
