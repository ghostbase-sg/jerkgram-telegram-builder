# Bot history follow-up: focused source diagnosis

2026-11-11. Read-only inspection of the final Beta2 source snapshot at
`../jerkgram-next/beta2/saved-tags/source`, relative to this builder. The user
confirms that Build179 fixed launch/token crashes and that old bot history still
never appeared. This report does not reopen that completed crash diagnosis.
No product, script, test, Git or CI change was made. No device diagnostic export
has been supplied in this investigation.

Read existing BOTBRIDGE history/API audits, decisions, final fix report and the
2026-11-05 recovery and combined Local Premium/Saved Tags reports. Their pending
device statements are historical; the user's newer successful-launch report is
the current launch evidence. A successful build does not establish history RPC
responses or imported database contents.

## Concrete source findings

All source paths below are relative to the inspected snapshot's `submodules/`.

1. **Crash recovery does not rearm an unsuccessful importer.**
   `TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift:351`
   (`botBridgeReadProgress`) returns an existing valid progress record unchanged.
   An unreadable/foreign record becomes a persisted `.corrupt` terminal.
   `BotBridgeHistoryController.start`, line617, emits `restoredTerminal` and
   returns for **every** nonnil terminal (line621). No request is attempted.
   The Beta2 keyed Int32/String codec removes the Postbox trap but intentionally
   preserves schema/key/generation and valid progress. Therefore retained
   `corrupt`, `rpcError`, `timeout`, `cancelled`, `interruptedState`, `noCandidate`
   or zero-message `completed` outcomes stay stopped across upgrade/relaunch.
   This is a source-proven recovery gap relative to recovering missing history;
   the actual user's persisted reason is unknown.

2. **Unread-based admission can produce zero history requests permanently.**
   `BotBridgeCursor.candidate(unread:)`, line16, requires `unread > 0 && pts > 1`.
   `BotBridgeHistoryProgress.acceptState`, line241, persists `.noCandidate` when
   this fails. With unread0 the controller makes only `updates.getState`, never
   `updates.getDifference`, even if extensive old/read messages exist. The native
   fixture `tests/fixtures/botbridge1/controller.swift:258` explicitly expects
   this one-request behavior; it is intentional policy, not a missed compiler
   branch. `pts - unreadCount` is the exact Build82 heuristic, not an all-history
   cursor. Preserving current qts/date/seq can also restrict what is returned;
   source alone cannot establish server response coverage.

3. **An interrupted state reservation cannot retry after restart.**
   `BotBridgeHistoryProgress.reserve`, line228, changes a reserved-but-not-stored
   initial state to `.interruptedState`. Its 120second original wall deadline
   also survives restart, and expired progress becomes `.deadline`. The
   controller's per-operation watchdog terminates after at most10seconds,
   including Postbox reservation/response transaction delay (lines674–696).
   These bounds prevent loops but a transient incident ends the generation.

4. **No alternate historical fetch exists behind the bridge.**
   `dispatch`, line730, uses the existing Network for current `updates.getState`
   followed by `updates.getDifference(flags:0, pts:candidate.pts, date:candidate.date,
   qts:candidate.qts, all optional limits:nil, automaticFloodWait:false)`.
   `botBridgePage`, line402, consumes the first response and slices; empty is a
   final zero-message page, tooLong terminates, and any RPC error becomes
   `.rpcError`. There is no dialog/history enumeration, channel backlog request,
   lower-date fallback, arbitrary zero-state reset or retry. This matches the
   documented bounded adaptation and does not prove the server can return all
   old bot messages. No claim of a Telegram server prohibition is justified by
   this source inspection.

## Reachability and persistence check

`TelegramCore/Sources/Account/Account.swift:1873` starts the bridge for every
nonsupplementary Account. `AccountStateManager.swift:1563` prepares it on the
Postbox queue; `jerkgramPrepareBotBridgeHistory` (history owner line367) requires
an AuthorizedAccountState matching the account peer/environment and an actual
stored TelegramUser with botInfo. Ordinary users do not enter the importer.
Preparation failure returns silently and is not separately exported.

Manager line1572 requires diagnostic admission. Diagnostics registry
`JerkgramBotBridgeDiagnostics.swift:293` rejects invalid UUID generations,
duplicate live account targets, or more than32 live scopes; Owner.admit at347
also rejects a closed owner/already installed scope. These can prevent the
first history request. Exported `admissionDenied` counters cover registry
rejections only, are process-local and cannot identify an individual bot.
Thus an empty export cannot by itself prove server failure.

Only successful confirmed bot authorization renews progress through
`Authorization.swift:1576` → `jerkgramRenewBotBridgeGeneration`, history line338.
There is no Settings history retry/refresh route. The ordinary modern bot
authorization helper `ghostBaseBotInitialState`, `Authorization.swift:1441`,
stores current server state, not an old-history seed. Removing/readding an
account is not an appropriate repair recommendation for retained local data.

When a page actually contains messages, `importBotBridgeHistoryPage`, line438,
verifies account/generation/request gates, skips already stored/deleted IDs,
converts current API messages, and inserts absent required peers. Counters and
messages commit in one Postbox transaction. Line564 calls the real public
`Postbox/Sources/Postbox.swift:117`
`Transaction.addHistoricalMessagesWithoutInteractiveActions`, which delegates
to ordinary Postbox insertion at `.Random` with installed interactive actions
disabled. Line565 calls the existing
`AccountStateManagementUtils.swift:3125` message-based bot inclusion helper.
No clear unconditional insertion no-op or universally unreachable importer was
found. Imported peer missing references, excluded peers, retained inclusion
minTimestamp/history holes and actual UI database behavior remain possible
visibility boundaries if export reports insertedMessages >0; that branch needs
runtime/database evidence, not replacement with generic live replay.

## Minimum device evidence already supported

After opening the retained bot Account once, export **BOTBRIDGE1 diagnostics**
from Jerkgram → Data & Backup → Export BOTBRIDGE1 Diagnostics. Exact UI owner:
`SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift:143` and
`JerkgramArchiveFlowController.swift:639`. This is the existing dedicated
redacted JSON export, not general logs, a crash report, a history archive or
token collection. Relaunch before export if the app was already open long enough
that the session's startup events expired; a restored terminal should be emitted
again without making new history requests. Retention is24hours with bounded
rotation (`JerkgramBotBridgeDiagnostics.swift:443,453,516`).

Inspect `records[].phase`, `history.reason`, `reservedAttempts`,
`committedPages`, `examinedMessages`, `insertedMessages`, `skipped`,
`unsupported`, `missingReferences`, `original`, `candidate`, `lastRetrieval`,
`observedLive`; also `admissionDenied` and storage/loss counters. Mapping is the
actual production adapter at diagnostics line553 onward. Expected discriminants:

| Evidence | Immediate conclusion |
| --- | --- |
| restoredTerminal + corrupt/interruptedState/timeout/rpcError | Retained stopped generation; launch recovery has not rearmed history |
| noCandidate, candidate absent, reservedAttempts1 | unread/PTS gate stopped before a difference request |
| completed, examined0, inserted0 | Server response adapter reached an empty/final result; not proof of all-history completeness |
| tooLong/rpcError/nonadvancing/limit/deadline | Explicit incomplete stop; reason must guide any scoped change |
| inserted >0 but chats/history absent | Inspect real inclusion/history-hole/UI path, rather than changing retrieval blindly |
| no records, admissionDenied >0 | Admission/loss investigation; counters reset per process |

## Candidate minimal fix and tests, not implemented

First distinguish sticky failed progress from heuristic/server coverage using the
export. For retained failed progress, a bounded, explicit per-account retry
transaction can validate the same confirmed bot identity and renew only the
bridge generation, preserving modern authorized state, messages and peers.
Cancellation/request-generation gates must fence the old controller before
replacement. A one-time versioned recovery is another option for precisely
classified legacy corrupt/interrupted records. Neither option alone restores
read old history when the unread heuristic yields no candidate, and automatic
unlimited retries would recreate the rejected poller behavior.

Tests needed for that scoped fix: actual production controller + actual Postbox
codec with retained Build178/179 terminal fixtures; retry exactly once; duplicate
UI taps; cancellation/replacement/late callbacks; same peer in distinct account
records/environments; ordinary user/supplementary exclusions; current live state
and existing newer messages unchanged; zero-unread behavior reported honestly;
atomic progress/message persistence and a real-device exported terminal before
and after retry. Existing controller fixtures deliberately enforce the sticky
policy, so passing current tests is not evidence of recovery satisfaction.

For a wider retrieval algorithm change, first establish a server-supported
bounded starting cursor from actual device evidence and primary API research.
Do not label a changed unread/date/PTS heuristic an all-time history guarantee.
Telegram13.2 migration should preserve these owners and retention/progress
semantics explicitly; upgrading the official pin by itself neither clears the
stored terminal nor broadens this importer's requests. Migration implementation
is outside this report.
