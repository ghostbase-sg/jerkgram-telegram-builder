# BOTBRIDGE1 device experiment — draft, not a released build

Target supplied by user: iPhone14Pro, iOS26.7.1. Actual BOT commit/run/IPA will be filled only after GREEN. No runtime success is claimed by this plan.

## What this experiment checks

Build82's unread-based historical starting point, adapted into finite direct import, plus current modern Jerkgram interactions. It cannot promise all-time history: server getDifference retention, unread candidate and channel coverage are separate runtime results. Absence of recovered history is reported as a terminal/partial reason, not automatically a crash or authorization failure.

Export dedicated **BOTBRIDGE1 diagnostics** from Jerkgram → Data & Backup after each stage and immediately after any session problem. The export contains only allowlisted opaque lifecycle/operation/history events; it does not include general app logs or the canonical history archive. The export entry should also work from another remaining active account after a bot is removed. Zero-account login-screen export remains outside this minimal entry point; do not claim Files access unless verified.

Record a private local mapping BotA/B/C → opaque diagnostic session label and approximate login time. No bot token, message text, auth key or credential belongs in the test report. Use messages/media/posts that the user intends to send, in user-controlled test destinations. The agent does not send them.

## Staged scenarios

| Stage | Actions | Evidence to retain |
| --- | --- | --- |
| BotA baseline | Login or open existing confirmed bot; allow finite history attempt; read known old chats, no text/reply/reaction/media/edit/delete/post | Original/candidate tuples, reserved requests/committed pages, inserted/skipped counts, terminal and coverage reason, active/last request, absence of user send categories |
| BotA restart | Restart app after completed import; open same history and compare known samples; later keep reading/idle as practical, matching historical ~14h observation | Persisted messages, no duplicate import/new budget, ordinary modern live updates, lifecycle gaps after process kill explicitly marked |
| BotB text | Repeat baseline, send one text, then a real reply; wait for each server result and incoming test response | Explicit text/reply flags, submitted vs typed result/error, request IDs/attempts, incoming live processing after import |
| BotC rich actions | Repeat baseline, then separate reaction, media, album, permitted broadcast post, edit and delete, exporting between categories | Correct category flags and real RPC terminal results; failed/rejected operations remain visible rather than appearing successful |
| Multiaccount | Switch between A/B/C and one ordinary user; interleave a small number of distinct operations | Independent opaque scopes/generations, no cross-account history/cancellation, ordinary user bridge absent |
| Navigation/accessibility | On stable modern IPA check Settings/root/nested/device card, low power/reduced transparency, profile/static/animated avatar, typing/scroll | Device timings/video/visual findings separate from source/compile proof; this is not a BOT UI refactor |

BotA is not network-silent: native reading may send `read_ack`, while normal update traffic continues. Do not classify those acknowledgements as user text/replies or infer that no request preceded an auth event. Preserve modern native reading behavior.

## On a session failure

1. Note visible event and timestamp: soft reset, logged-out UI, account disappearance or failed RPC are distinct.
2. Export dedicated diagnostics from a remaining active account. Preserve previous stage exports; they establish whether the same state appeared before any sends.
3. Inspect finite auth class/numeric code, history phase and terminal reason, last submitted/completed mutation and bounded in-flight requests, including `read_ack` and historical reads.
4. Check loss/expired/unknown/restart markers before treating absence of an event as evidence. Submission is not proof of wire execution; acknowledgement is not a successful RPC result; RPC result is not proof of local application.
5. Compare A/B/C: an action preceding an auth failure establishes observation order/correlation only. Reproduction with another controlled bot and a read-only baseline is needed before assigning a cause.

## Acceptance boundaries

- Source/native tests and GREEN IPA establish architecture, tested behavior and compilation; they cannot establish server history availability,14h session survival or Swiftgram performance parity.
- Imported absent messages must survive restart; existing live/edited/retained-deleted messages and archive/pins/cutoff must remain unchanged. Report known sample IDs privately if needed, never in exported diagnostics.
- Physically deleted messages without durable tombstones cannot be distinguished universally from missing history. Same-response deletion exclusion/session-known deletions and existing-ID preservation do not solve unseen preexisting deletions; report coverage honestly.
- If getDifference returns tooLong/noCandidate/limit/error, keep modern live state and normal operations. Never retry by resetting the account/update state or sharing bot credentials.

## Diagnostic JSON field guide (schema 1)

The envelope has `status` and `records`. `admissionDenied` separates aggregate `capacity`, `duplicateTarget` and `invalidGeneration` counts without account identifiers; they cover this process only and do not prove crash durability. Check `sinkDropped`, `snapshotDropped`, `storageFailures`, `storageLossCountUnknown`, `exportTruncated`, `retentionExpiredFiles`, `rotationEvictedFiles`, `malformedRecords` and `retentionExpiredRecords` before interpreting missing events. A storage error is an export failure, not proof that no sessions were captured.

Each record carries opaque `session`/`epoch`, `sequence`, `wall`, `phase`, optional `request`/`logical`, `category`, `flags`, `attempt`, optional numeric `errorCode` and finite `errorClass`, `lifecycle`, bounded `inFlight`, `lastSubmitted` and `lastCompleted`. Flags are additive: text=1, reply=2, media=4, post=8. `state_read` and `read_ack` are separate categories. Request attempts are observed wrapper submissions; internal network retries and uploads are not fully observed.

History records expose `original`, `candidate`, `lastRetrieval`, `observedLive` tuples; `reservedAttempts`, `committedPages`, `examinedMessages`, insertion/skipped/unsupported/deletion/missing-reference counters; and `reason`. `restoredTerminal` describes persisted completion without inventing a new history run. Reasons such as `noCandidate`, `tooLong`, `limit`, `deadline`, `timeout`, `rpcError` or `interruptedState` describe incomplete coverage; they are not evidence of logout. `liveStateNeverReplaced`, `deletionCoverageLimited` and `modernProcessingResumed` preserve the source-level boundary in the export.

`submitted`, `acknowledged`, `result`, `rpcFailure`, `parseFailure` and `cancelled` have different meanings. Lifecycle values distinguish `softReset`, `authKeyUnknown`, local/remote/server logout, removal, cleanup, scheduled deletion and deinitialization. `cleanupResult` records signal completion; `deletionScheduled` does not prove successful physical deletion. `correlation` may be `expired`, `history_lost`, `none` or `observed_order_only`.

Envelope coverage markers explicitly retain unknowns: `internalRetriesUnobserved`, `uploadsUnobserved`, `localUpdateApplicationUnobserved`, `restartAndCrashDurabilityUnknown`, `snapshotPersistenceBestEffort` and `unknownMethodsAreCoverageGaps`. No exported event can by itself establish the cause of session invalidation.
