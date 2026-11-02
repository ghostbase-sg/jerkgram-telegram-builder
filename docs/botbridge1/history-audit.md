# BOTBRIDGE1 historical evidence audit

Research only. No builder or generated source changed. Modern Build177 GREEN checkpoint is pending; this document does not authorize implementation or call Build177 proven working. Paths below are relative to `jerkgram-next`; modern symbol paths are under `build177-source/submodules/TelegramCore/Sources/`.

## Evidence and limits

Historical source: `ghostbase-sg/jerkgram-telegram-builder`, exact commit `2d120ab4a72dd2217269d7b6a7142a8ef0ce3cd3`, “Add persistent Bot Inbox and account badge”. Local evidence is `botbridge1/research/build82/PROVENANCE.json` and its three scripts. Independently computed Git blob hashes match all three recorded SHA1 values. The saved GitHub primary API response `build82/EXACT-COMMIT-DIFF.json` was subsequently inspected: it identifies the exact commit and parent `fa7615a35f0d4f9f5a56bbdd4d780bc287d4c0fa`, includes all five changed files and their patches, and resolves the commit-diff provenance gap. This audit still does not contain the original fully generated Telegram tree. Runtime success on old Build82 is user evidence, not a new reproduction.

The v1.0ZC verifier is substring/anchor verification. Its output “Postbox replay OK” does not execute replay, verify completeness, demonstrate server availability or prove restart/multiaccount behavior.

## Exact commit diff supplement

`build82/EXACT-COMMIT-DIFF.json` records 706 additions, 11 deletions across five files:

| File in builder repository | Exact change | Classification |
| --- | --- | --- |
| scripts/apply_ghostbase_v10zc_bot_inbox.py | Added 609 lines; auth preflight, bot dialog bypass/inclusion and account badge | HISTORY REQUIRED subset plus OLD ACCOUNT LIFECYCLE and OLD UI ONLY, as classified below |
| scripts/verify_ghostbase_v10zc_bot_inbox_generated_source.py | Added 93 lines of source assertions | HISTORY REQUIRED verification dependency; adapt to modern behavioral/static checks, do not treat as runtime proof |
| scripts/apply_ghostbase_v10z_bot_login_runtime.py | Replaces initial persistent all-zero state with nil (1 addition, 6 deletions) | OLD ACCOUNT LIFECYCLE compatibility fix; confirms zero bootstrap is not the target historical semantics |
| scripts/verify_ghostbase_v10z_bot_login_generated_source.py | Removes five assertions demanding zero state and checks state:nil (1 addition, 5 deletions) | OLD ACCOUNT LIFECYCLE verification compatibility; modern verifier must not demand obsolete zero state |
| scripts/bazel_build_probe_official.sh | Adds v1.0ZC apply and verify calls immediately before Bazel build, after v1.0ZB difference UI/seasonal gift stages | HISTORY REQUIRED build wiring dependency; modern pipeline needs its own scoped stage, no old UI/gift transplant |

Order matters: the earlier v1.0Z login patch first becomes nil-safe; the late v1.0ZC patch then replaces the authorization block with its getState/preflight result. Therefore the exact target commit neither mandates a persistent zero cursor nor stops at the earlier nil initialization. No outbound implementation is changed by any of these five diffs.

## Exact Build82 semantics

`apply_ghostbase_v10zc_bot_inbox.py` replaces the old v1.0Y authorization block. `ghostBaseBotInitialState`:

1. Requests `updates.getState(automaticFloodWait: false)` on the existing UnauthorizedAccount network. Failure returns nil.
2. Builds current state from server pts/qts/date/seq.
3. Only when unreadCount > 0 and pts > 1, computes `candidatePts = max(1, pts - unreadCount)`. This is an unread-based heuristic, not a history start timestamp and not a guarantee to recover every old message. Unread count is not generally an exact PTS distance.
4. Issues a preflight `updates.getDifference(flags: 0, pts: candidatePts, date: current.date, qts: current.qts, all limits nil, automaticFloodWait: false)`.
5. For difference or differenceSlice, RETURNS THE CANDIDATE STATE, with original current qts/date/seq. It discards the entire preflight payload, including messages, peers and intermediate state. For empty/tooLong/error it returns current state.
6. `ghostBaseAuthorizeBot` stores the bot user, candidate/current state and bot marker, then switches to authorized account. The normal Telegram state manager subsequently requests difference again and performs import and slice iteration. There is no independent legacy history database/importer/paging loop in this script.

Thus literal historical behavior is a one-time authorization-state seed plus normal manager replay. The proof is not a zero-cursor fetch, constant state reset, messages.getHistory loop or Bot API request. v1.0ZC explicitly rejects persistent zero state left by earlier auth work.

## Classification

| Historical piece | Category | BOTBRIDGE treatment |
| --- | --- | --- |
| getState snapshot; unread/PTS candidate; bounded preflight and fallback | HISTORY REQUIRED | Preserve retrieval semantics with modern API constructors; document best effort |
| Authorized-state seed before first normal poll | HISTORY REQUIRED | Literal minimal option uses the sole modern state manager; never reseed an already running manager |
| Normal difference replay, peer merge, StoreMessage conversion, storage | HISTORY REQUIRED dependency | Reuse modern equivalents, not old source |
| Avoid bot getPeerDialogs discarding imported peer/chat state | HISTORY REQUIRED | Already modern bypass; retain modern message-based inclusion |
| Avoid bot getDialogs/getPinnedDialogs | HISTORY REQUIRED dependency | Retain existing modern guards, audit separately; do not reinstall old implementations |
| Legacy synthesized PeerChatInfo and unconditional root inclusion | HISTORY REQUIRED intent, unsafe old detail | Use current inclusion that changes only notIncluded; preserve archive/pins/cutoff |
| Purple account BOT capsule in PeerInfoScreenMemberItem | OLD UI ONLY | Do not port |
| importBotAuthorization, migration retry, login settings, future token, switchToAuthorizedAccount | OLD ACCOUNT LIFECYCLE | Keep current implementation; needed context, not history code to replace |
| UserDefaults GhostBase.BotAccount marker | OLD ACCOUNT LIFECYCLE dependency | Use confirmed modern bot peer and account-local durable bridge state; do not resurrect old global marker scheme |
| Send/reply/media/reaction/edit/delete implementations | OLD OUTBOUND | None occur in this v1.0ZC patch; do not import earlier stack |
| v1.0Y previous zero-state initialization | OLD ACCOUNT LIFECYCLE superseded | Explicitly not the v1.0ZC algorithm |
| Other GhostBase features, old Telegram runtime/build/UI | UNRELATED | Do not port |

## Modern comparison and existing competing history path

`Authorization.swift:1441 ghostBaseBotInitialState` currently stores only current server state, logging BotRepair1; no unread subtraction or preflight. `ghostBaseAuthorizeBot:1501` retains modern duplicate-account prevention, marker naming and modern lifecycle. Its transaction at ~1575 sets initial authorized state.

`State/AccountStateManagementUtils.swift:665 initialStateWithDifference` builds current-schema mutable state. `:800 finalStateWithDifference` merges chats/users, converts `StoreMessage(apiMessage:accountPeerId:peerIsForum:)`, handles final/slice state and feeds modern update processing. `:4235 replayFinalState` verifies the snapshot unless explicitly skipped, stores messages at ~4573 and state at ~5375. `jerkgramIncludeBotMessagePeers:3125` runs after storing upper-history-block messages and changes only `.notIncluded`; it preserves existing archive/pin/minTimestamp. `resolveMissingPeerChatInfos:3143` immediately bypasses bot getPeerDialogs. Reuse these modern mechanisms.

`State/AccountStateManager.swift:826 .pollDifference` owns ordinary polling. At ~881 it requests current authorized pts/qts/date; ~904 validates starting state still matches current snapshot; ~909 calls finalStateWithDifference; ~922 verified replay; ~988 requeues slices. Its tooLong handling resets ordinary state (~968), so a history bridge must treat tooLong as unavailable without entering this destructive/reset fallback accidentally.

IMPORTANT: Build177 includes ACTIVE BotShadow history, not dormant dead code:

- `Account/Account.swift:1900` schedules `stateManager.ghostBaseStartBotShadowHistory()` after 1.5 seconds for nonsupplementary bot safe mode.
- `State/AccountStateManager.swift:1562–1844` runs separate `GhostBaseBotShadowCursor`, per-peer UserDefaults cursor, zero initial state, own recursive getDifference loop and 96-slice cap.
- Its replay filters UpdateState but allows deletes, edits, reactions and peer updates; uses `skipVerification: true`; restores a stale sampled persistentState in memory; updates minTimestamp separately through `updatePeerChatInclusionWithMinTimestamp`. These permit old events to overwrite modern live content or alter existing inclusion and history boundary.
- `Account/Account.swift:1620` suppresses network.loggedOut while `GhostBaseBotHistoryGate` is active. This is account-wide timing suppression, despite comment claiming “only for this request”; a genuine simultaneous auth failure could be hidden. Gate definition: `Account.swift:1360`.

For BOTBRIDGE, disable the single automatic BotShadow startup and its dedicated logout-suppression condition in the experimental branch, and prove no alternate caller starts it. Do not wholesale disable modern bot safe mode, outgoing managers or unrelated lifecycle fixes. Leaving the second pager active while adding legacy bootstrap would defeat a single-owner experiment even though it shares Network/Postbox.

## Minimal integration recommendation after GREEN

Smallest literal adaptation: confirmed bot authorization only, get current state and historical candidate exactly as Build82, preflight, seed once before authorized manager construction, then let modern normal replay own all state/slices. This preserves actual Build82 semantics and does not need a new importer. However it does not retrofit history into existing accounts and temporarily makes the one manager's starting state historical. Explicitly state this limitation before choosing it over the requested separate importer.

If existing accounts or a fully independent read/import cursor are mandatory, use one finite bridge integrated into the modern manager operation queue, serialized with live replay. Preserve the same unread-based request starting point. Import new cloud messages and necessary peers through current StoreMessage/storage; do not replay historical deletes/edits/reactions/read/authorization/state operations onto modern data. Never commit the historical cursor as live authorized state. Keep the authoritative modern state untouched and hand back to ordinary polling after termination. This is a documented adapter change from Build82's seed/refetch approach, not a literal port. Avoid claiming a filtered generic finalState is safe without auditing preprocessing/network side effects before filtering.

A second background getDifference loop is not the minimal adapter. A new Account, Network or Postbox is unnecessary. Both options must disable BotShadow and retain modern outbound ownership. Recommendation: implement the finite existing-account-capable adapter after GREEN. A literal login-only seed is useful as a reference/control experiment but does not meet the full written scope on its own. The specification is not explicitly limited to first login, requires preservation of existing modern live/history data, repeated bootstrap deduplication, restart and per-account isolation, and requests a bounded read/import component handing ownership back. Current modern duplicate-account prevention also prevents simply readding an existing bot to trigger authorization, so a login-only implementation would force an unstated remove/relogin procedure and bypass the intended existing-data preservation case. A finite adapter can run once for each confirmed existing/new bot account generation and reach the same historical unread-based request without rewriting live state. Its difference from Build82 must be explicit: consume the first payload directly; keep a private finite retrieval cursor; import only missing messages/necessary peers; do not seed persistent live state; serialize under modern manager ownership. Retrieval remains best effort, and a user-facing completeness claim still requires device evidence. Existing-account support is an inference from the combined acceptance criteria, not a literal phrase in the spec; record that interpretation rather than claim the spec expressly names it.

## Failure, cancellation and persistence obligations

- Bot identity: confirm `TelegramUser.botInfo`, not a token prefix or stale UserDefaults boolean alone. Scope checkpoints by account record/environment/session generation as well as peer; equal peer IDs in different environments or relogins must not share cursor/completion.
- Arithmetic: clamp subtraction safely; retain original current qts/date/seq exactly for first historical request. Never replace with all-zero state or fabricate channel PTS.
- Cancellation: dispose pending network/replay work, clear activity in all terminal paths, resume modern queue exactly once, and prevent late callbacks committing after logout/account removal. Old preflight best-effort catch does not solve app shutdown or hanging network operations.
- Bounds: finite iteration/time budget and repeated/nonadvancing cursor detection. Persist partial progress and a distinct incomplete result; cap/error/tooLong are not success. Existing BotShadow cursor.slice >= 96 remains stuck after restart because slice is persisted.
- Errors: empty, tooLong, RPC/flood/auth errors need distinct outcomes. Never suppress auth/logout because history is active; no blind reauthorization/reset retry. Sanitize error identifiers and never log tokens/text/credentials.
- Restart: transactionally persist imported messages and bridge cursor/completion together in account Postbox. Existing BotShadow uses several nontransactional UserDefaults writes separate from message transaction, allowing torn cursor and stale RunningAt delays. Disposal releases its gate but leaves RunningAt until TTL expiry.
- Dedup: message identity is peer + namespace + server ID; counting existing IDs is not dedup preservation. Skip existing messages to preserve newer edits/reactions/media/live content. Duplicate peer merges must not regress modern metadata. Repeated successful empty import must not retrigger forever; BotShadow marks Completed only when newly added count > 0, including on final difference.
- Concurrent live delivery: serialize imports with manager replay; never apply a sampled old state after live advancement. Snapshot validation is essential for generic replay; `skipVerification: true` is not a safe default.
- Inclusion: reuse jerkgramIncludeBotMessagePeers after actual insertion; never force root on an already archived/pinned peer or overwrite minTimestamp. Avoid replay side effects that clear drafts/read state/notifications.
- Channel backlog coverage and complete old-history coverage remain runtime questions. getDifference responses are server-dependent; successful compile, substring verification or one preflight response cannot establish completeness.

## Verification status

Completed: read exact supplied historical scripts/verifier and all five patches in the saved primary GitHub commit response; verified all recorded blob hashes; inspected modern authorization, ordinary difference/import/replay, inclusion and active BotShadow call/gate. No modern source/build files modified. Source audit does not substitute for GREEN base checkpoint, compilation, behavioral tests or device scenarios A/B/C.
