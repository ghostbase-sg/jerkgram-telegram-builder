# Jerkgram Build118 Performance Repair Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the process-wide Build118 input/UI stutter by making capture append-only, routing chat reads through a compact index, and caching retention settings without changing Build118 identity or product behavior.

**Architecture:** Keep canonical per-account JSONL as the source of truth. Add a disposable per-account JSONL index containing event identity and byte ranges. One serialized recorder batches capture writes; bounded chat queries decode only selected canonical lines. Cache immutable retention snapshots per account and invalidate them on writes.

**Tech Stack:** Swift, Foundation, SwiftSignalKit, Python `unittest`, repository patch/render verifiers, GitHub Actions/Bazel.

---

### Task 1: Lock the performance contract with failing tests

**Files:**
- Create: `tests/test_jerkgram_v12g_build118_performance1.py`
- Inspect: `scripts/jerkgram_v12g_build118_core1_payload/JerkgramStore.swift`
- Inspect: `scripts/jerkgram_v12g_build118_core1_payload/JerkgramRetention.swift`
- Inspect: `scripts/apply_jerkgram_v12g_build118_since_last_open1.py`

**Steps:**
1. Add focused source-contract tests proving ordinary append does not call `loadAccount`/`writeAccount`, recorder reuses one store and exposes bounded batching, the store exposes index-bounded chat lookup, since-last-open uses index records instead of full `events`, and retention has a per-account snapshot cache.
2. Run `python3 -m unittest tests.test_jerkgram_v12g_build118_performance1 -v` and confirm failures are for the missing behavior.
3. Do not weaken existing semantic tests.

### Task 2: Implement append-only canonical writes and disposable index

**Files:**
- Modify: `scripts/jerkgram_v12g_build118_core1_payload/JerkgramStore.swift`
- Test: `tests/test_jerkgram_v12g_build118_performance1.py`

**Steps:**
1. Add a codable index record with event ID, byte offset/length, sequence, account/chat/sender IDs, kind, timestamp, and optional message coordinates.
2. Add a cached per-account index state. Load or rebuild it once from existing canonical JSONL, ignoring a truncated final line and never modifying complete canonical records.
3. Implement `appendBatch` so canonical lines and matching index rows append in order; duplicate event IDs are rejected through the cached index.
4. Keep `replaceAtomically` as an explicit bulk path and rebuild/publish the derived index atomically after replacement.
5. Make `events(accountPeerId:chatPeerId:)` decode only indexed byte ranges when a chat is supplied; retain full-account loading only for explicit export/import/cleanup callers.
6. Make `JerkgramCaptureRecorder` own one store and flush at 32 events or 250 ms on its serial queue.
7. Run the focused test until green, then run all Build118 tests.

### Task 3: Bound since-last-open and cache retention

**Files:**
- Modify: `scripts/apply_jerkgram_v12g_build118_since_last_open1.py`
- Modify: `scripts/jerkgram_v12g_build118_core1_payload/JerkgramRetention.swift`
- Modify as needed: Build118 source verifiers/tests

**Steps:**
1. Patch chat opening to ask the store for exact chat index rows in `(previousSequence, currentSequence]`; omit the summary while the index is unavailable rather than scanning the complete account log.
2. Preserve summary counts, navigation, account/chat isolation, and watermark semantics.
3. Add a lock-protected immutable retention snapshot cache keyed by account peer ID. Populate once, replace after every persistence write, and pre-index chat overrides.
4. Run the focused test and all Build118 tests.

### Task 4: Verify, commit, push, and monitor CI

**Files:**
- Modify only compile-compatibility details required by Official Telegram 12.9.2 APIs

**Steps:**
1. Run all `test_jerkgram_v12g_build118*.py` tests and relevant render/source verifiers.
2. Inspect `git diff --check`, status, and the final diff for accidental version/build/artifact/UI changes.
3. Commit with a focused performance message.
4. Fetch and confirm remote `Jerkgram-12.9.2` HEAD still matches the base lineage before pushing; rebase only if safe and non-conflicting.
5. Push the commit to `Jerkgram-12.9.2` and monitor the triggered GitHub Actions run.
6. If CI fails, diagnose the full failed job log, make only the minimum compile-compatible correction, verify, commit, push, and repeat until green.
7. Report the green run and device test checklist; do not claim device smoothness until the user completes that gate.
