# BOTBRIDGE1 bounded history and modern interaction design

Design prepared before implementation. The modern-base gate is now fulfilled: Build177 commit `5ba6add985d6995ca102d4e40d8da66e98f443c1`, run `41372637134`, required native/source and app jobs SUCCESS, IPA artifact `13111834999`. See modern-green-checkpoint.json. This is compilation and artifact evidence; device/server behavior remains unverified. Historical source is exactly `2d120ab4a72dd2217269d7b6a7142a8ef0ce3cd3`. Evidence and API caveats are in HISTORY-AUDIT.md, FINITE-IMPORT-DESIGN-NOTES.md and WRITE-AUDIT.md; exact missing modern worker blobs are preserved under research/official-1312 with provenance, not inferred from scratch files.

## Architecture and responsibilities

One authorized Account owns one Network, one Postbox and its existing AccountStateManager. The manager serializes each finite history page with current processing. Modern send, reply, reaction, media, edit, delete and post implementations retain ownership of their operations. The bridge has no outbound mutation API.

`Legacy history bridge is read/import only. Server mutations must use the current Jerkgram runtime.`

Use focused internal Swift files accepted by the current TelegramCore BUILD source glob; no new target or broad dependency change is needed. Suggested boundaries (names are proposals until full-source compilation):

* `BotBridgeHistoryProgress`: Codable Postbox preference containing schema, opaque session generation, original server snapshot, candidate and next cursor, committed page/counter budgets and terminal reason. Allocate an unused preference key only after checking the full tree. No token/auth key-derived generation.
* `BotBridgeHistoryController`: manager-owned lifetime, one active page token, request MetaDisposable, monotonic timeout and exactly-once finish closure. Exposes start-if-confirmed-bot and cancel(reason); it does not expose a sender or state setter.
* `importBotBridgeHistoryPage(transaction:page:expectedProgress:token:)`: narrow storage helper beside the existing file-private chat inclusion helper or through a narrow internal wrapper. Returns actual inserted counts and new progress; no generic replay.
* `BotBridgeDiagnosticScope`: Account-owned, epoch-bound bounded recorder. Network holds only a weak registration after confirmed bot identity. An immutable `BotBridgeOperationContext` carries opaque logical ID and finite flags into request calls. It carries no peer/message ID, request payload or Account reference.

Disable the existing automatic BotShadow startup and its dedicated logout suppression in the experimental branch. Assert no remaining caller starts its zero-cursor pager. Retain unrelated modern lifecycle/stability fixes. Ordinary user accounts do not create a history controller or registered recorder.

## Retrieval semantics and explicit adaptation

Obtain updates.getState through the existing Network with automaticFloodWait false. For unreadCount > 0 and pts > 1 choose max(1, Int64(pts) - Int64(unreadCount)), safely narrowed; preserve current qts/date/seq. Request updates.getDifference with flags 0 and nil limits. This is Build82's unread-based heuristic, not a complete-history algorithm.

Consume the first response instead of discarding its payload and reseeding the live manager. Keep intermediate slice cursors private to the finite bridge. Do not write AuthorizedAccountState, live pts/qts/date/seq, channel PTS or acknowledgements. Do not call initialStateWithDifference/finalStateWithDifference/replayFinalState, resetAccountState, dialogs, getHistory, channel difference or peer-resolution RPCs. This deliberate adapter supports existing accounts and preserves their live state. Build82's actual seed/refetch mechanism is not being represented as a literal transplant.

A final difference or empty response terminates retrieval; tooLong terminates unavailable and performs no reset. No candidate is terminal noCandidate. Zero insertions can be a valid deduplicated terminal result. Record completion as retrieval terminated, not proof that all old messages were recovered. Unsupported or skipped payload counts accompany a partial coverage label.

## Fixed bounds and resume policy

Preflight correction: transactionally persist generation/start/deadline and reserve each request before subscription. Keep attempted requests distinct from committed pages/cursor. Crashes consume reservations even when no response commits. An interrupted initial getState without a persisted snapshot terminates incomplete; it does not obtain a new unbudgeted window. A repeated getDifference cursor consumes another of the same 32 reserved attempts. Only response kind determines successful termination: a progressing empty/deduplicated differenceSlice continues, including when zero messages were inserted. This supersedes any earlier research note suggesting a deduplicated first slice is terminal.

These are new safety policies, not Build82 constants:

| Resource | Bound/policy |
| --- | --- |
| Network requests | getState plus at most 32 getDifference pages per session generation; no bridge retry loop |
| Request time | 10 seconds monotonic timeout per request |
| Entire generation | 120 seconds wall deadline from initial start; monotonic remaining budget within each process |
| Payload processing | At most 5,000 newMessages and 10,000 peers per page; at most 20,000 examined messages total |
| Historical deletion IDs | At most20,000 aggregate IDs inspected per page; reject excess before mutation and construct bounded deletion sets, avoiding candidate×update×vector scans |
| Ancillary updates | At most 10,000 otherUpdates inspected per page; excess terminates incomplete before page mutation/additional arrays; encrypted payloads are ignored and counted without conversion |
| Page scheduling | One manager custom operation per request/page; next continuation appended only after current operation finishes |
| No progress | Reject a slice whose cursor is identical or whose pts regresses; terminate malformed/nonadvancing, never spin |
| Resume | Same persisted cursor and original deadline only; no renewed budget, no repeated getState window selection |
| Terminal rerun | No automatic rerun for completed/noCandidate/empty/tooLong/limit/error/cancelled; new session generation is a new experiment |

Payload bounds apply before constructing additional working arrays; transport still necessarily receives the server response and these bounds do not claim control of Network's decoding allocation. Oversize response terminates incomplete without partially importing that page. Persist committed counts and cursor with insertion. Crash before commit safely repeats the page; after commit resume at the next cursor. Backward wall-clock movement relative to persisted observations terminates clockChanged, forward movement can expire the deadline. A queued page rechecks budget before issuing its request.

RPC/flood/parse failures terminate with finite classified reason. Auth errors retain normal lifecycle behavior. Partial history remains. A terminal incomplete preference prevents restart from silently granting another budget. A future explicit retry facility would require its own reviewed policy; it is not necessary for this experiment.

## Storage and deletion behavior

Within one Postbox transaction, validate confirmed TelegramUser.botInfo, session generation, expected cursor/version and cancellation identity. Parse response newMessages plus necessary chats/users only. Use modern StoreMessage conversion with current peer metadata preferred for forum determination. Accept cloud full MessageIds, deduplicate deterministically by first occurrence, and skip every existing ID, including retained GhostBase isDeleted placeholders. Preserve current peers; insert only absent required peers with an existing-or-new preserving closure. Insert missing messages through the callback-suppressed historical transaction entry described below, at .Random, and invoke existing jerkgramIncludeBotMessagePeers on inserted messages. Never alter existing archive/pins/history cutoff, explicit read state, drafts or live message contents.

otherUpdates are never replayed. A narrow inspection of audited delete-update constructors may extract IDs to exclude candidate inserts from that same response; global cloud IDs and channel-scoped IDs require correct namespace matching. Do not apply historical delete updates to existing local data. All other update constructors remain ignored with bounded counts.

Known-deleted IDs from existing MessagesRemovedContext exclude inserts within its supported session scope. DeletedMessagesView is transaction-ephemeral, not a durable tombstone source. Preexisting physically deleted IDs without a durable tombstone cannot be reliably distinguished from missing history, especially after restart. Report this limitation explicitly; do not promise universal non-resurrection.

A later page can contain deletion evidence for a message imported on an earlier page. Minimal policy is preservation: do not delete either existing messages or previously committed bridge messages. Record a finite historicalDeletionObserved count and mark coverage partial when delete updates appear; without an imported-ID set, do not claim that a specific deletion belongs to a prior bridge page. No unbounded imported-ID or deletion journal is introduced. An optional bounded set of at most 20,000 IDs belonging to the current import generation could improve conflict identification, but it cannot recover preexisting deletion evidence and is not needed to protect live content. If strict non-resurrection becomes a release gate, this adapter is blocked until a durable deletion policy or complete staging design is agreed; do not quietly install a broad tombstone subsystem.

## Required Postbox insertion adapter: installed interactive callbacks

Plain Transaction.addMessages(.Random) is insufficient to establish read/import-only behavior. Verified official Postbox.swift calls both installedMessageActionsByPeerId and installedStoreOrUpdateMessageActionsByPeerId after insertion, independent of .Random. The audited interactive-read installer can schedule consume/readReaction actions and apply a max read index; visible-reaction and wallet-transfer hooks also consume insertion callbacks. An open chat therefore changes the safety analysis even without generic final-state replay.

Add one narrowly named public Transaction entry, `addHistoricalMessagesWithoutInteractiveActions(_:location:)`, because TelegramCore calls across the Postbox module boundary. Delegate to the same fileprivate PostboxImpl.addMessages implementation with a defaulted `runInstalledActions: Bool = true`. The existing public addMessages continues to delegate with the default. Guard only the two installed-callback blocks with that flag. Leave messageHistoryTable insertion, indexes, tags, pending-operation bookkeeping, location/hole handling and returned ID mapping identical. The bridge alone uses the false entry with .Random. Do not change message flags, unregister account-wide listeners, suppress all workers, or add mutable process/global transaction mode.

This is a deliberate minimal dependency outside TelegramCore and must be included in builder application/verification and the final file report. The focused-new-Swift-files glob observation does not remove the need to patch this existing Postbox owner. Suppressing installed callbacks also suppresses any benign work those callbacks perform for these historical inserts; the explicit modern chat-inclusion call still runs separately. This tradeoff is preferable to replaying interactive read/consume actions for backlog insertion, but must be documented and tested.

Tests must execute a real or faithful compiled callback facade of both entries: register both callback kinds for an affected peer, import historical messages and assert zero callbacks; insert ordinary messages and assert original callback counts, order, transaction and payload; mix historical then ordinary insertion in one transaction and prove suppression does not leak. Compare returned IDs and stored/index/tag/hole behavior for equivalent .Random inserts. Verify .UpperHistoryBlock and normal update paths keep baseline behavior. Integrate the audited interactive-read hook with an open-chat fixture and assert historical insertion does not enqueue consume/readReaction operations or invoke max-read advancement through installed actions; verify an ordinary insertion still does. Include visible-reaction/wallet callback sentinels and a normal outgoing message case.

Source guards must prove both callback dispatch blocks alone are conditional, the default is true, and the bridge calls only the new false entry. Source assertions cannot replace the behavioral tests. The shared messageHistoryTable.addMessages path still emits normal storage bookkeeping; inspect its real handling of converted historical message flags/actions and run full-source integration to exclude additional mutation triggers. Do not claim that bypassing these two callbacks proves every possible observer is passive. Exact helper-name collisions, Swift module visibility and full-source test integration remain CI gates.

## Manager lifetime and cancellation contract

Existing custom operation completion serializes with normal work, but its returned subscription disposable does not cancel the underlying operation. The bridge therefore explicitly owns its request disposable independently. Each page has a manager-queue-confined once gate and generation token. Timeout, failure, terminal response and cancellation all converge on one finish path; that path disposes only bridge work, closes the signal exactly once and permits the manager queue to continue. A normal completion followed by disposal is not a second cancellation. Teardown invalidates tokens before releasing the recorder/controller; late callbacks cannot schedule pages or import into a later account generation.

Revalidate inside the transaction. An atomic transaction already begun may finish its page when cancellation races; cancellation cannot roll back committed Postbox work, but prevents all subsequent pages. Avoid self → queued signal → self cycles and capture only the required weak owner/token. Include logout/removal/reset paths, not merely deinit. If local custom-operation lifetime cannot establish these guarantees in the actual implementation, use a narrowly scoped dedicated page operation with a stored disposable rather than modifying every generic custom operation consumer.

## Passive diagnostics and exact category attribution

Instrument the source-native Network.request and requestWithAdditionalInfo cold subscription bodies. Allocate a unique request ID per subscription and observe immediately before requestService.add. Name this phase submitted: it is not proof of wire delivery or server execution. Observe valid typed response, TL verification failure, original RPC error and disposal before terminal; preserve callbacks, original error object, parsing, dependency tags, flood waits, policy return value, operator ordering and disposal behavior. Preserve acknowledged:nil where currently nil. Do not emit upload/progress ticks.

Read only FunctionDescription.name, exact-whitelist it into a finite method enum, and discard the name after classification. NEVER access parameters: its lazy loader materializes all payload fields. Never interpolate descriptions, reflect, inspect buffers or retain API requests/responses. Unlisted requests have an unknown/uncovered classification, not fabricated category coverage.

Add a defaulted optional immutable operation context parameter to these Network entry points. Propagate it only at modern workers where category cannot be inferred safely: explicit reply intent and resolved broadcast-channel post semantics at terminal send sites, including albums/group and standalone sends. text/media are additive flags; reply is explicit user reply, not any topic/monoforum InputReplyTo; post means broadcast post, not every channel-shaped peer. Capture logical IDs in worker scope so resubscriptions correlate while every subscription retains its own request ID. Do not use thread-local state, timing joins or dependency tags as correlation carriers. Other named methods classify reaction/edit/delete centrally; modify those workers only if exact logical retry grouping requires it.

Network result is the terminal RPC result, not proof of local update application. Media sendMedia/sendMultiMedia result is covered; upload failure before those requests is separately unknown unless a narrow upload observer is implemented. Multiplexed/download/upload paths outside these two functions are explicit coverage gaps. Transport-internal retry count is unknown unless an audited existing policy callback can be wrapped without changing its return; rate-limited observations are not wire-attempt proof.

Use finite server error classes and validated numeric codes only; never export raw descriptions. Lifecycle hooks record soft reset, logout requested/observed, account record marking, cleanup/removal and snapshots of last submitted, last completed and bounded in-flight requests. Correlation is observation ordering, not logout causation. Snapshot before unregistering, and preserve the original auth behavior without suppression.

## Diagnostic resource and retention policy

The weak lifecycle registry is keyed by a validated weak AccountManager namespace identity, AccountRecordId and authorization generation, with at most 32 entries. Purge dead entries on access; do not evict a live cancellation target. If full, fail closed for the new experimental bridge and report capacity loss. Resolve targets under the lock and invoke cancellation/recorder callbacks after releasing it. Soft reset cancels finite history and freezes an observation while retaining the recorder registration for the continuing modern Account; unregister only on terminal teardown/replacement. An old-generation deinit cannot remove a replacement registration.

History export schema explicitly includes numeric original server tuple, selected candidate tuple, last retrieval tuple, observed current live tuple when available, reserved request count, committed pages, inserted messages/chats/users, skipped/missing-reference/unsupported/deletion counters and finite terminal/coverage reason. No private peer/message ids or serialized progress are exported. Handoff event says `modern processing resumed; live state never replaced`; it does not claim a reset back to an old tuple. Start/end fields must be privacy- and bound-tested in the dedicated export fixture.

Per confirmed account lifetime: 256 event ring slots, 64 active logical/request contexts, 8 reserved frozen lifecycle snapshots; 30-minute correlation TTL. A short bounded lock protects allocation/order/queues; it performs no I/O or callbacks. A maximum 256 pending event slots feeds an asynchronous sink; saturation drops ordinary events and increments loss counters, preserving lifecycle slots. Exports include lost/expired/evicted/unknown labels rather than inventing a last operation after evidence loss.

Persist redacted snapshots and batched events asynchronously outside removable account directories. Cap storage globally to eight rotated 256-KiB files (2 MiB) with a 24-hour retention limit and include an export schema version. Dedicated serial sink owns rotation/export, with no synchronous filesystem/UserDefaults writes on request, update, UI or auth callbacks. Never retain an Account to keep files alive. Asynchronous storage survives ordinary account cleanup once written; crash/immediate process termination durability is not guaranteed. Export copies only this allowlisted representation, no general application logs. Establish the existing app-level export destination and UI entry before promising a user-accessible artifact.

## Work packages and proof gates

1. Record exact modern GREEN source/builder commits and run/artifact; create experimental branch without altering production. Freeze baseline hashes of modern workers and builder stage provenance.
2. Implement scoped bridge/progress/storage plus the narrowly gated Postbox insertion adapter, and disable only competing BotShadow start/suppression. Test real transaction preservation and bounded manager lifecycle before integration claims.
3. Implement bounded recorder, central request observers and necessary category contexts. For changed workers prove the original sender algorithm is identical after removing only additive diagnostic arguments/local immutable context construction; use an allowed-diff check plus behavioral request stubs. Hash equality alone is suitable only for unchanged workers.
4. Run source guards and behavioral tests, then full generated-source macOS build. Fix scoped compiler/build failures through GREEN. Deliver actual IPA/run/commit evidence.
5. Device Bot A read-only, Bot B text/reply, Bot C reaction/media/post/edit/delete; test restart, multi-account and known benign failure. Only this stage can establish availability/history coverage and session behavior.

Required behavioral cases: confirmed bot gate and ordinary-user fast path; exact candidate arithmetic/current qts/date; existing edited/live/deleted-placeholder preservation; missing-peer nonreplacement; duplicate and repeat pages; archive/pins/cutoff preserved; no generic update/delete/reaction/state replay; atomic progress/restart; final empty/dedup-only termination; malformed/tooLong/oversize/deadline/32-page bounds; backward clock; hanging request; cancellation before/after response and during transaction; account replacement and late callback; normal live processing between pages; no leaked active custom operation.

Diagnostic cases: cold signal constructed but never subscribed, reuse and resubscription, ack versus result, failure before existing catch/mapError, parse failure, result then disposal, cancellation race, preserved policy/dependency/disposal behavior, explicit reply versus topic routing, text/media broadcast post, albums and standalone sends, concurrent accounts, expired scopes, overflow/TTL/file rotation/export after cleanup, and forbidden token/text/error sentinel absence. Assert lazy parameter loader is never invoked by diagnostics. Do not present string-anchor tests as behavioral tests or Linux inspection as compilation.

## Explicit unresolved blocking facts

Before implementing affected portions: verify full-source StoreMessage/reference extraction and Transaction signatures; actual account session-generation ownership and reset/removal ordering; all duplicate worker call paths needing reply/post metadata; preference-key uniqueness; exact method names from pinned API; actual diagnostic export storage entry point. The exact modern GREEN checkpoint gate is fulfilled as recorded above. Actual BOT source/native integration remains a separate required gate.

Durable preexisting physical-delete detection is currently unavailable in audited APIs; the limited deletion policy above is explicit experimental behavior, not solved by MessagesRemovedContext or DeletedMessagesView. Channel/history completeness, actual server responses and logout correlation remain device-test questions. None may be inferred from a successful build.
