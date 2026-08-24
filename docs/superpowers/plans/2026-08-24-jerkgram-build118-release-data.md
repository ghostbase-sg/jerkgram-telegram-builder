# Jerkgram Build118 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the real Build118 with account-isolated retention, Archive v2 export/import, Time Machine search/diff/visit summaries, profile-glass parity, Presence/About polish, and an artifact chain that cannot publish Build117 as Build118.

**Architecture:** Add a small `JerkgramCore` Swift module for account-scoped models, persistence, retention, indexing, diffing, and archive validation so SettingsUI and TelegramUI share one source of truth without circular dependencies. Keep ZIP/document-picker UI in SettingsUI, chat search and visit UI in TelegramUI, and profile material ownership in the existing PeerInfo components. Materialize every source change through ordered Build118 overlay scripts and gate Bazel plus artifact upload with independent verifiers.

**Tech Stack:** Swift 5, Foundation, Postbox/TelegramCore peer identities, SwiftSignalKit queues/signals, Bazel `swift_library`, Official Telegram 12.9.2 UI APIs, SSZipArchive/ZipArchive, Python 3 overlay/verifier tests, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-24-jerkgram-build118-release-data.md`

## Global Constraints

- Official Telegram iOS 12.9.2 commit `6ad963e5b62d354da79040f388ae2b9132fb17b8` is the only API reference.
- Every setting, policy, event, index row, and archive payload is scoped by exact Telegram account peer ID.
- Event identity is `(accountPeerId, eventId)`; equal text never defines a duplicate.
- Default retention is 30 days, recovered-media limit is 1 GB, and Secret Chat archival is disabled.
- `Forever` and `Unlimited` are explicit independent choices; `Forever + Unlimited` is valid.
- Time Machine indexes canonical records by reference and never stores a second message/media payload copy.
- Jerkgram Glass off restores Official Telegram behavior; no global color replacement and no per-cell blur.
- New visible text is semantic RU/EN localization through `JerkgramStrings`.
- No auth keys, sessions, tokens, signing data, provisioning data, sandbox UUID paths, or binary media bytes enter `.jerkgram` archives.
- The workflow publishes exactly one `Jerkgram-build118` artifact containing `Jerkgram-build118.ipa` and `Jerkgram-build118-info.txt`.

---

### Task 1: Materialize the shared JerkgramCore module

**Files:**
- Create: `scripts/jerkgram_v12g_build118_core1_payload/BUILD`
- Create: `scripts/jerkgram_v12g_build118_core1_payload/JerkgramModels.swift`
- Create: `scripts/jerkgram_v12g_build118_core1_payload/JerkgramStore.swift`
- Create: `scripts/apply_jerkgram_v12g_build118_core1.py`
- Create: `scripts/verify_jerkgram_v12g_build118_core1.py`
- Create: `tests/test_jerkgram_v12g_build118_core1.py`

**Interfaces:**
- Produces: `JerkgramAccountId`, `JerkgramChatId`, `JerkgramEventId`, `JerkgramEventKind`, `JerkgramCanonicalEvent`, `JerkgramEventStore`, and a Bazel target `//submodules/JerkgramCore:JerkgramCore`.
- Consumes: Foundation only in the model/store layer; Telegram peer IDs are converted to `Int64` by callers.

- [ ] **Step 1: Write the failing overlay fixture test**

```python
def test_materializes_core_once(tmp_path, run_overlay):
    run_overlay("apply_jerkgram_v12g_build118_core1.py", tmp_path)
    core = (tmp_path / "submodules/JerkgramCore/Sources/JerkgramModels.swift").read_text()
    assert "public struct JerkgramEventId" in core
    assert "public let accountPeerId: Int64" in core
    assert "public let eventId: JerkgramEventId" in core
    assert "messageText" not in (tmp_path / "submodules/JerkgramCore/Sources/JerkgramIndex.swift").read_text()
```

- [ ] **Step 2: Run the test and verify it fails because the Build118 overlay does not exist**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_core1 -v`

- [ ] **Step 3: Define exact public models and atomic store contract**

```swift
public struct JerkgramEventId: RawRepresentable, Codable, Hashable, Comparable {
    public let rawValue: String
}

public struct JerkgramCanonicalEvent: Codable, Equatable {
    public let accountPeerId: Int64
    public let chatPeerId: Int64
    public let eventId: JerkgramEventId
    public let sequence: Int64
    public let kind: JerkgramEventKind
    public let senderPeerId: Int64?
    public let messageNamespace: Int32?
    public let messageId: Int32?
    public let observedAtMs: Int64
    public let payload: JerkgramEventPayload
}

public protocol JerkgramEventStore {
    func append(_ event: JerkgramCanonicalEvent) throws
    func events(accountPeerId: Int64, chatPeerId: Int64?) throws -> [JerkgramCanonicalEvent]
    func replaceAtomically(accountPeerId: Int64, events: [JerkgramCanonicalEvent]) throws
}
```

- [ ] **Step 4: Implement queue-confined JSONL persistence with sorted-key side metadata and atomic replacement**

Use one directory per account and one JSONL file per event kind. Generate a random stable event ID once for new captures. Expose deterministic structural migration IDs only through a separate migration initializer; do not derive identity from user text.

Migrate existing deleted/edit/reply/profile/presence/gift/personal-channel records incrementally into canonical events. Preserve the legacy payload as compatibility input until the migration marker and canonical output are atomically committed; rerunning migration must not create a second event.

- [ ] **Step 5: Run fixture test and structural verifier**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_core1 -v && python3 scripts/verify_jerkgram_v12g_build118_core1.py`

- [ ] **Step 6: Commit the shared core**

```bash
git add scripts/jerkgram_v12g_build118_core1_payload scripts/apply_jerkgram_v12g_build118_core1.py scripts/verify_jerkgram_v12g_build118_core1.py tests/test_jerkgram_v12g_build118_core1.py
git commit -m "Add Build118 account-scoped core"
```

### Task 2: Add account/chat retention and bounded cleanup

**Files:**
- Create: `scripts/jerkgram_v12g_build118_storage1_payload/JerkgramRetention.swift`
- Create: `scripts/apply_jerkgram_v12g_build118_storage1.py`
- Create: `scripts/verify_jerkgram_v12g_build118_storage1.py`
- Create: `tests/test_jerkgram_v12g_build118_storage1.py`
- Modify: `scripts/ghostbase_v11g_unified_recovery1_payload/GlobalDelete.swift.fragment`
- Modify: `scripts/ghostbase_v11g_unified_recovery1_payload/LocalDelete.swift.fragment`
- Modify: `scripts/ghostbase_v11g_unified_recovery1_payload/EditMessage.swift.fragment`
- Modify: `scripts/apply_ghostbase_v11t_build105_full1.py`

**Interfaces:**
- Consumes: `JerkgramCanonicalEvent`, `JerkgramEventStore`.
- Produces: `JerkgramHistoryDuration`, `JerkgramMediaByteLimit`, `JerkgramRetentionPolicy`, `JerkgramRetentionStore`, `JerkgramRetentionEngine.previewCleanup(...)`, and `applyCleanup(...)`.

- [ ] **Step 1: Write failing policy and eviction tests**

```python
def test_defaults_and_unlimited_are_independent(rendered_swift):
    assert "historyDuration: .days30" in rendered_swift
    assert "mediaByteLimit: .gigabytes1" in rendered_swift
    assert "archiveSecretChats: false" in rendered_swift
    assert "case forever" in rendered_swift
    assert "case unlimited" in rendered_swift
```

- [ ] **Step 2: Run test to confirm RED**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_storage1 -v`

- [ ] **Step 3: Implement typed policies and exact scope lookup**

```swift
public enum JerkgramHistoryDuration: String, Codable { case disabled, days7, days30, days90, forever }
public enum JerkgramMediaByteLimit: String, Codable { case disabled, megabytes250, megabytes500, gigabytes1, gigabytes2, gigabytes5, unlimited }
public struct JerkgramRetentionPolicy: Codable, Equatable {
    public var historyDuration: JerkgramHistoryDuration
    public var mediaByteLimit: JerkgramMediaByteLimit
    public var archiveSecretChats: Bool
}
```

Account defaults use `30 days / 1 GB / Secret Chats off`. Chat overrides are keyed only by `(accountPeerId, chatPeerId)` and inherit missing values from the account policy.

- [ ] **Step 4: Gate all existing delete/edit/recovered-media capture owners before persistence**

Pass exact account/chat IDs and a Secret Chat classification into the policy lookup. `disabled` returns before writing payload bytes or JSON. Keep existing text fallback when a media write fails.

- [ ] **Step 5: Implement deterministic pruning and cleanup preview**

Finite durations remove expired canonical events; `forever` skips age pruning. Finite media budgets sort recoverable bytes by capture time and remove oldest bytes first without deleting the canonical text event; `unlimited` skips byte eviction.

- [ ] **Step 6: Run tests/verifier and commit**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_storage1 -v && python3 scripts/verify_jerkgram_v12g_build118_storage1.py`

Commit: `git commit -am "Add Build118 retention controls"`

### Task 3: Implement reference-only Time Machine indexing and diffing

**Files:**
- Create: `scripts/jerkgram_v12g_build118_time_machine1_payload/JerkgramTimeMachineIndex.swift`
- Create: `scripts/jerkgram_v12g_build118_time_machine1_payload/JerkgramTextDiff.swift`
- Create: `scripts/apply_jerkgram_v12g_build118_time_machine1.py`
- Create: `scripts/verify_jerkgram_v12g_build118_time_machine1.py`
- Create: `tests/test_jerkgram_v12g_build118_time_machine1.py`

**Interfaces:**
- Consumes: canonical store event append/migration callbacks.
- Produces: `JerkgramTimeMachineFilter`, `JerkgramTimeMachineQuery`, `JerkgramTimeMachineResult`, `JerkgramTimeMachineIndex.query(_:)`, `JerkgramTextDiff.diff(old:new:)`, and visit watermark methods.

- [ ] **Step 1: Write failing identity, filter, and Unicode diff fixtures**

Fixtures must prove same text/different IDs survive, same ID/same canonical bytes deduplicates, author filters use sender peer ID, combined filters intersect, and emoji/ZWJ grapheme clusters are never split.

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_time_machine1 -v`

- [ ] **Step 3: Implement reference-only index records**

```swift
public struct JerkgramTimeMachineIndexRecord: Codable, Equatable {
    public let accountPeerId: Int64
    public let chatPeerId: Int64
    public let eventId: JerkgramEventId
    public let sequence: Int64
    public let kind: JerkgramEventKind
    public let senderPeerId: Int64?
    public let observedAtMs: Int64
    public let locator: JerkgramCanonicalLocator
    public let searchKey: String
}
```

Do not include canonical message bodies, captions, or media bytes in index records. Resolve a result through `locator` only after selection/render demand.

- [ ] **Step 4: Implement bounded Unicode diff**

Tokenize extended grapheme clusters into word/whitespace/punctuation runs. Use a bounded Myers/LCS sequence operation model: `.equal`, `.insert`, `.delete`, `.replace`. For oversized input, diff paragraphs/lines first and refine changed chunks only.

- [ ] **Step 5: Implement atomic visit watermarks**

`snapshotChangesSinceLastOpening(accountPeerId:chatPeerId:)` returns `(upperSequence, counts, eventIds)` and advances the stored watermark to the pre-query maximum sequence. Watermarks remain outside archive models.

- [ ] **Step 6: Run tests/verifier and commit**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_time_machine1 -v && python3 scripts/verify_jerkgram_v12g_build118_time_machine1.py`

Commit: `git commit -am "Add Build118 Time Machine engine"`

### Task 4: Implement Archive v2 codec, preview, and transactional merge

**Files:**
- Create: `scripts/jerkgram_v12g_build118_archive1_payload/JerkgramArchiveV2.swift`
- Create: `scripts/jerkgram_v12g_build118_archive1_payload/JerkgramArchiveTransaction.swift`
- Create: `scripts/apply_jerkgram_v12g_build118_archive1.py`
- Create: `scripts/verify_jerkgram_v12g_build118_archive1.py`
- Create: `tests/test_jerkgram_v12g_build118_archive1.py`

**Interfaces:**
- Consumes: typed settings, retention policies, canonical events.
- Produces: v2 manifest/payload encoder, v1 in-memory migrator, `JerkgramImportPreview`, duplicate/conflict classifier, rollback transaction.

- [ ] **Step 1: Write failing two-account, duplicate, conflict, traversal, checksum, and v1 fixtures**

Test an archive with accounts A/B where equal message IDs/text remain isolated. Verify unavailable B causes zero writes. Verify same `(account,eventId)` with equal canonical bytes skips, differing bytes conflicts, and different IDs preserve both.

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_archive1 -v`

- [ ] **Step 3: Implement manifest and payload contracts**

Use the exact spec layout under `accounts/<peer-id>/`. Declare counts, uncompressed bytes, and SHA-256 per payload. Reject duplicate/undeclared paths, traversal, missing files, malformed JSON/JSONL, limits, and checksum mismatches before mutation.

- [ ] **Step 4: Implement preview and rollback transaction**

Decode/validate all selected components, prepare pre-import snapshots, then write per exact account. On any failure restore snapshots. Settings changes require a second explicit confirmation flag separate from history merge selection.

- [ ] **Step 5: Run fixtures/verifier and commit**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_archive1 -v && python3 scripts/verify_jerkgram_v12g_build118_archive1.py`

Commit: `git commit -am "Add Build118 Archive v2 transactions"`

### Task 5: Add Data and Backup, retention, export, and import UI

**Files:**
- Create: `scripts/jerkgram_v12g_build118_data_ui1_payload/JerkgramDataAndBackupController.swift`
- Create: `scripts/jerkgram_v12g_build118_data_ui1_payload/JerkgramArchiveFlowController.swift`
- Create: `scripts/apply_jerkgram_v12g_build118_data_ui1.py`
- Create: `scripts/verify_jerkgram_v12g_build118_data_ui1.py`
- Create: `tests/test_jerkgram_v12g_build118_data_ui1.py`
- Modify through overlay: `submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift`
- Modify through overlay: `submodules/SettingsUI/BUILD`

**Interfaces:**
- Consumes: `JerkgramCore` stores/archive preview and Official `legacyICloudFilePicker`/activity-controller patterns.
- Produces: localized Data and Backup route, per-account component selection/weights, retention editors, cleanup previews, export and import flows.

- [ ] **Step 1: Write failing structural UI tests**

Assert there is one Settings route; accounts/components are keyed by peer ID; safe components default selected; every row has count/bytes; settings confirmation is separate; `Forever + Unlimited` warning exists; no auth/session fields exist.

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_data_ui1 -v`

- [ ] **Step 3: Implement account-grouped retention and cleanup UI**

Expose 7/30/90/Forever, disabled capture, media disabled/250/500/1G/2G/5G/Unlimited, Secret Chat switch default off, per-chat override search, current bytes, and exact destructive preview.

- [ ] **Step 4: Implement export/import UI off the main thread**

Generate ZIP via the existing ZipArchive dependency, show progress/errors, hand off `.jerkgram` through the native picker/share flow, and delete temporary files after completion. Import copies security-scoped input to controlled temporary storage, previews accounts/components/changes/conflicts, then calls the transaction.

- [ ] **Step 5: Run tests/verifier and commit**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_data_ui1 -v && python3 scripts/verify_jerkgram_v12g_build118_data_ui1.py`

Commit: `git commit -am "Add Build118 data portability UI"`

### Task 6: Integrate Time Machine into chat search and chat opening

**Files:**
- Create: `scripts/jerkgram_v12g_build118_time_machine_ui1_payload/JerkgramTimeMachineResultsController.swift`
- Create: `scripts/jerkgram_v12g_build118_time_machine_ui1_payload/JerkgramTimeMachineDetailController.swift`
- Create: `scripts/jerkgram_v12g_build118_time_machine_ui1_payload/JerkgramSinceLastVisitNode.swift`
- Create: `scripts/apply_jerkgram_v12g_build118_time_machine_ui1.py`
- Create: `scripts/verify_jerkgram_v12g_build118_time_machine_ui1.py`
- Create: `tests/test_jerkgram_v12g_build118_time_machine_ui1.py`
- Modify through overlay: `submodules/TelegramUI/Sources/ChatSearchState.swift`
- Modify through overlay: `submodules/TelegramUI/Sources/ChatControllerUpdateSearch.swift`
- Modify through overlay: `submodules/TelegramUI/Sources/Chat/ChatControllerLoadDisplayNode.swift`
- Modify through overlay: `submodules/TelegramUI/BUILD`

**Interfaces:**
- Consumes: Time Machine query/diff/watermark APIs and Official chat message navigation.
- Produces: in-chat Deleted/Edited/Recovered Media/From User filters, local result/detail route, exact diff view, and dismissible visit summary.

- [ ] **Step 1: Write failing route/state tests**

Prove filters preserve current chat/account, live messages call canonical navigation, deleted records never fabricate Postbox messages, and summary taps carry the exact sequence interval.

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_time_machine_ui1 -v`

- [ ] **Step 3: Extend search state without replacing Official remote search**

Add a separate local Time Machine mode/filter state. Ordinary search remains Official Telegram. Activating a Time Machine filter queries local index; filters combine and an empty query is valid.

- [ ] **Step 4: Implement result/detail/diff and visit summary**

Resolve canonical locators lazily. Existing messages use Official open/highlight. Deleted/local-only events open the detail controller. Add the summary below navigation only when counts are nonzero; no notifications or background work.

- [ ] **Step 5: Run tests/verifier and commit**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_time_machine_ui1 -v && python3 scripts/verify_jerkgram_v12g_build118_time_machine_ui1.py`

Commit: `git commit -am "Add Build118 Time Machine UI"`

### Task 7: Fix Presence, About cards, and profile glass parity

**Files:**
- Create: `scripts/apply_jerkgram_v12g_build118_runtime_polish1.py`
- Create: `scripts/verify_jerkgram_v12g_build118_runtime_polish1.py`
- Create: `tests/test_jerkgram_v12g_build118_runtime_polish1.py`
- Modify through overlay: `GhostBaseProfileReportPaneNode.swift`
- Modify through overlay: `PeerInfoScreenItemSectionContainerNode.swift`
- Modify through overlay: `PeerInfoHeaderEditingContentNode.swift`
- Modify through overlay: `PeerInfoVisualMediaPaneNode.swift`
- Modify through overlay: `PeerInfoPaneContainerNode.swift`
- Modify through overlay: `GhostBaseSettingsController.swift`
- Modify through overlay: `BuildConfig.h`
- Modify through overlay: `BuildConfig.m`

**Interfaces:**
- Consumes: existing fullscreen profile background, Build117 About resolution/navigation, and semantic presence records.
- Produces: one shared profile material contract, corrected Presence rendering, and two 88-point live About credit cards.

- [ ] **Step 1: Write failing owner-specific tests for all seven screenshot surfaces**

Assert profile sections clear scoped child fills; editing receives glass state; Files/Music/Voice no longer tint opaque `itemBlocksBackgroundColor`; Links gets a rounded material surface; report cards use the same helper; no per-cell blur exists; glass-off branches retain stock colors.

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_runtime_polish1 -v`

- [ ] **Step 3: Centralize and apply reference card material**

Use clear roots, radius 16, black alpha 0.075 in dark appearance and white alpha 0.035 in light appearance. Keep the fullscreen scene as sole blur owner and preserve stock geometry/interactions.

- [ ] **Step 4: Correct Presence semantics and legacy rendering**

Render `.present(until:)` as online only when `until >= observedAt`; otherwise render exact last-seen. Compact semantic duplicates without deleting distinct events.

- [ ] **Step 5: Add large live About cards**

Resolve `@JerkgramApp` and `@JerkgramCommunity` through TelegramEngine as `EnginePeer`, use avatars/title/username/bounded preview, minimum 88-point height, and canonical peer navigation.

- [ ] **Step 6: Expose truthful extension compatibility status**

Classify the resolved shared-container state as `shared`, `processLocal`, `missing`, or `other`, redact sandbox UUID paths, and show the localized result in Settings. Do not convert bundle presence or an extension callback into a success claim.

- [ ] **Step 7: Run tests/verifier and commit**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_runtime_polish1 -v && python3 scripts/verify_jerkgram_v12g_build118_runtime_polish1.py`

Commit: `git commit -am "Polish Build118 runtime surfaces"`

### Task 8: Complete semantic RU/EN localization

**Files:**
- Create: `scripts/apply_jerkgram_v12g_build118_localization1.py`
- Create: `scripts/verify_jerkgram_v12g_build118_localization1.py`
- Create: `tests/test_jerkgram_v12g_build118_localization1.py`
- Modify through overlay: `JerkgramStrings.swift`

**Interfaces:**
- Consumes: all Build118 semantic string keys.
- Produces: complete RU/EN text for archive, retention, cleanup, Time Machine, diff, visit summary, errors, extension status, and About loading states.

- [ ] **Step 1: Write failing key-parity and Cyrillic-leak tests**

Enumerate every new semantic key and require exactly one RU and EN value. Materialize English and fail on remaining Cyrillic literals in Build118-owned UI sources.

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_localization1 -v`

- [ ] **Step 3: Add semantic keys and replace literals**

Do not persist localized labels as enum values. All counts, byte sizes, transitions, destructive confirmations, unavailable states, and unlimited warnings go through `JerkgramStrings`.

- [ ] **Step 4: Run tests/verifier and commit**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_localization1 -v && python3 scripts/verify_jerkgram_v12g_build118_localization1.py`

Commit: `git commit -am "Localize Build118 features"`

### Task 9: Wire Build118, block stale artifacts, and verify materialized source

**Files:**
- Create: `scripts/install_jerkgram_v12g_build118_probe_hook.py`
- Create: `scripts/verify_jerkgram_v12g_build118_release_readiness1.py`
- Create: `scripts/jerkgram_publish_build118_artifact.py`
- Create: `tests/test_jerkgram_v12g_build118_release_chain1.py`
- Modify: `scripts/bazel_build_probe_official.sh`
- Modify: `.github/workflows/build.yml`
- Modify: `.github/workflows/build-official.yml`

**Interfaces:**
- Consumes: every Build118 apply/verifier pair in Tasks 1–8.
- Produces: ordered Build117 → Build118 → final verification → Bazel chain and exactly one canonical Build118 artifact.

- [ ] **Step 1: Write a failing release-chain test reproducing the mislabeled artifact bug**

```python
def test_build118_workflow_cannot_reference_build117_publisher(workflow):
    assert "jerkgram_publish_build118_artifact.py" in workflow
    assert "artifacts/Jerkgram-build118.ipa" in workflow
    assert "artifacts/Jerkgram-build117.ipa" not in workflow
    assert workflow.count("name: Jerkgram-build118") == 1
```

- [ ] **Step 2: Run the test and observe failure against the current Build117 workflow**

Run: `python3 -m unittest tests.test_jerkgram_v12g_build118_release_chain1 -v`

- [ ] **Step 3: Install the ordered Build118 chain exactly once**

The hook must reject partial/duplicate wiring and require all Build118 apply/verifier positions after Build117 and before Bazel. The final readiness verifier scans materialized sources, workflow names/paths, forbidden secrets, localization ownership, archive limits, and Build118 markers.

- [ ] **Step 4: Implement a Build118-only publisher**

Read the final CI-produced IPA, copy bytes to `artifacts/Jerkgram-build118.ipa`, emit its SHA-256/source commit/build metadata to `Jerkgram-build118-info.txt`, and reject any output/input basename containing `build117`.

- [ ] **Step 5: Run full local overlay/materialization verification**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_jerkgram_v12g_build118_*.py' -v
python3 scripts/install_jerkgram_v12g_build118_probe_hook.py
GHOSTBASE_PROBE_ONLY=1 scripts/bazel_build_probe_official.sh
```

Expected: every Build118 verifier is GREEN and the probe reaches Bazel with no Build117 artifact path in either workflow.

- [ ] **Step 6: Commit the release chain**

```bash
git add scripts .github/workflows tests
git commit -m "Wire Jerkgram Build118 release chain"
```

### Task 10: Final verification and publication

**Files:**
- Verify only; no planned source changes.

**Interfaces:**
- Consumes: complete Build118 branch.
- Produces: evidence for publication and the GitHub build handoff.

- [ ] **Step 1: Run Python syntax, fixture, diff-scope, and chain checks**

```bash
python3 -m py_compile scripts/*build118*.py
python3 -m unittest discover -s tests -p 'test_jerkgram_v12g_build118_*.py' -v
git diff --check origin/Jerkgram-12.9.2...HEAD
```

- [ ] **Step 2: Materialize from a clean Official source and run every verifier**

Run the canonical preparation/baseline/Build115/116/117/118 chain in probe mode. Confirm Official reference HEAD remains `6ad963e5b62d354da79040f388ae2b9132fb17b8` and Build118 overlays are applied once.

- [ ] **Step 3: Inspect final workflow/artifact assertions**

Require workflow display name `Jerkgram 12.9.2 Build118`, exactly one upload step, exact two paths for Build118 IPA/info, and no Build117 publisher/output path.

- [ ] **Step 4: Publish the verified local tree to `Jerkgram-12.9.2`**

Fetch remote branch immediately before publication, stop on divergence, create blobs/tree/commit, update the exact branch ref, then compare remote commit tree with local `HEAD^{tree}`.

- [ ] **Step 5: Trigger Build118 and wait for CI evidence**

Only after the GitHub run is green, fetch artifact metadata and verify the downloaded ZIP contains `Jerkgram-build118.ipa` plus `Jerkgram-build118-info.txt`. Do not infer inner identity from the outer ZIP name.
