# Jerkgram Build118 Performance Repair Specification

## Scope

This change repairs the global runtime regression introduced by the first
Build118 Time Machine implementation. It does not change version `12.9.2`,
Build `118`, the public artifact names, product behavior, account isolation,
Archive v2, signing, or the Jerkgram Settings root menu.

Official Telegram 12.9.2 at commit
`6ad963e5b62d354da79040f388ae2b9132fb17b8` remains the sole reference for
Telegram API and lifecycle behavior.

The visual redesign of Jerkgram's inner settings pages is a separate change.
This repair must establish a smooth runtime baseline before any UI work is
added.

## Confirmed defect

`JerkgramJSONLEventStore.append` is not append-only. For every captured event
it:

1. reads the complete account `events.jsonl` file;
2. decodes every historical event;
3. scans for a duplicate ID;
4. sorts the complete collection;
5. encodes every event again;
6. atomically replaces the complete file.

A deleted message with recovered media performs this sequence twice. Across
many events this produces quadratic cumulative work and continuous CPU and
filesystem contention. Running it on a utility queue prevents a direct main
thread call but does not prevent the process-wide scheduling and storage
pressure observed as delayed keyboard input and animation frames.

There are two additional hot paths:

- `ChatController.viewDidAppear` loads and decodes the complete account event
  file for every ordinary chat opening before filtering it to one chat;
- `JerkgramRetentionRuntime.shouldCapture` locks and decodes the account
  retention configuration for every checked message identifier.

Normal memory use does not exclude these defects because they are CPU and I/O
regressions, not an accumulating memory leak.

## Storage design

### Append path

The canonical event log remains JSONL and keeps the existing encoded event
schema. A capture append must never read, sort, or rewrite existing canonical
events.

Each account owns one serialized writer. The writer:

- creates the account directory once;
- opens `events.jsonl` for append;
- encodes each event exactly once;
- buffers at most 32 events or 250 milliseconds and flushes them in order,
  whichever threshold is reached first;
- closes or synchronizes the handle on application lifecycle boundaries;
- reports a bounded write failure without blocking Telegram's transaction
  owner.

The stable `eventId` remains the identity. New capture IDs are generated once.
Equal text remains irrelevant to identity.

### Index

A compact append-only account index stores only fixed metadata needed for
lookup:

- `eventId`;
- byte offset and byte length in `events.jsonl`;
- sequence;
- chat peer ID;
- event kind;
- sender peer ID when known;
- observation timestamp;
- message namespace and ID when known.

Index updates are serialized with log appends. Atomic replacement is used only
when publishing a rebuilt or compacted index, never for an ordinary event.
Time Machine queries first
select index records by exact account and chat, then decode only the referenced
canonical event lines. Search may decode matching chat records lazily in
bounded pages; it must not load another chat's payload.

The index is disposable derived data. If it is missing, truncated, or does not
match the canonical log length, it is rebuilt incrementally away from the main
thread. The canonical JSONL log remains the source of truth.

### Existing Build118 data

No destructive migration is required. On first access, an existing JSONL file
is scanned once to create the index. The scan is incremental and resumable.
Capture can continue during repair through the same serialized writer.

Archive v2 continues to export the canonical records with their original
account IDs and event IDs. Import validates and stages records using the
existing transaction rules, then performs a bulk canonical rewrite only as an
explicit import/cleanup operation. Ordinary runtime capture never uses the
bulk rewrite path.

## Since-last-opening behavior

Opening a chat reads the previous watermark and the current upper sequence
from the index. It queries only index rows in that bounded sequence interval
for the exact `(accountPeerId, chatPeerId)`.

It must not read or decode the complete account log. The visible summary and
Time Machine route remain unchanged. Watermarks remain transient local state
and are excluded from export.

If index repair for that account has not completed, the summary is omitted for
that opening rather than performing an unbounded fallback scan. This preserves
UI responsiveness and does not lose canonical data.

## Retention hot path

Retention configuration is decoded when it changes or when an account cache is
first populated, not once per message ID. Reads use an immutable cached
snapshot keyed by exact account peer ID. Writes replace that snapshot after
the encoded value is persisted.

Per-chat override lookup is pre-indexed by chat peer ID. `shouldCapture` must
perform bounded in-memory work and preserve these rules:

- exact account isolation;
- exact chat isolation;
- Secret Chats disabled unless explicitly enabled;
- the legacy setting migration occurs once per concrete account;
- `7/30/90 days`, `Forever`, bounded media limits, and `Unlimited` keep their
  existing meaning.

## Failure and crash safety

- A partially written final JSONL line is ignored during repair and reported;
  previous complete records remain valid.
- Index publication uses a temporary file plus atomic replacement.
- A failed index write never invalidates the canonical log.
- A failed capture write never blocks or crashes Telegram message processing.
- Import and cleanup remain explicit bulk transactions and retain rollback
  behavior.
- No auth, signing, notification, or Telegram database material enters the
  Jerkgram store.

## Verification

Automated tests must prove:

1. append does not call full-account load or canonical rewrite;
2. N appends encode N events and preserve order and IDs;
3. equal text with different IDs remains two records;
4. duplicate IDs are detected through the index without scanning payload text;
5. chat queries do not decode unrelated chat lines;
6. since-last-opening reads only the requested sequence interval;
7. retention reads use the cached typed snapshot and remain account-scoped;
8. legacy Build118 JSONL data rebuilds into the new index without mutation;
9. a truncated tail does not destroy complete records;
10. Archive v2 export/import and cleanup still work;
11. all existing Build118 semantic tests remain green.

The CI build is necessary but not sufficient. The device gate is:

- cold launch;
- chat-list scrolling;
- rapid text entry in a normal chat;
- switching among several chats;
- opening a chat with a large local Time Machine history;
- receiving or creating deleted/edited capture events;
- repeating the same checks after relaunch.

There must be no persistent keyboard delay, process-wide stutter, or growing
lag. RAM is recorded for context but is not the primary acceptance metric.

## Delivery order

1. Add failing store, index, retention-cache, and bounded-query tests.
2. Implement the append writer and disposable index.
3. Move since-last-opening to bounded index queries.
4. Cache retention snapshots.
5. Run Build118 tests and source verifiers.
6. Commit and push the performance repair without changing Build118 identity.
7. Monitor GitHub Actions until green, fixing compile-only issues minimally.
8. Perform the device performance gate before starting the settings UI
   redesign.
