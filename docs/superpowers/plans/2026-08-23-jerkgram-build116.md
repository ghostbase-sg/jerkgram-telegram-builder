# Jerkgram Build116 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a verifier-first Build116 overlay that fixes the confirmed Build115 UI/deep-link regressions, exposes bounded extension failure stages, and introduces typed Settings/Archive foundations.

**Architecture:** Preserve the historical patch chain and add three late Build116 overlays: user-facing fixes, extension diagnostics, and typed foundation models. Each overlay edits only final materialized owners and has fixture tests plus a strict final-source verifier. A final installer wires Build116 after all Build115 verifiers and before Bazel, then publishing is renamed mechanically to Build116.

**Tech Stack:** Python 3 patchers/verifiers and `unittest`; Swift 5 in Official Telegram iOS 12.9.2 modules; Bazel/GitHub Actions; Foundation `Codable` and atomic file writes.

**Spec:** `docs/superpowers/specs/2026-08-23-jerkgram-build116.md`

## Global Constraints

- Official Telegram iOS 12.9.2 is the API/geometry source of truth.
- Do not fabricate Telegram peers or access hashes.
- English is canonical/fallback; Russian is the initial translation; language follows `PresentationStrings.baseLanguageCode`.
- No auth keys, tokens, keychain data, sessions, provisioning, or signing material in archives.
- No raw Runtime/event log list in release Settings; one bounded copy-diagnostics action is permitted.
- No Bazel execution before all patcher/verifier unit tests and final-source preflight pass.

---

### Task 1: User-facing Build116 overlay

**Files:**
- Create: `tests/test_build116_ui.py`
- Create: `scripts/apply_jerkgram_v12e_build116_ui1.py`
- Create: `scripts/verify_jerkgram_v12e_build116_ui1.py`

**Interfaces:**
- Consumes: final Build115 materialized `PeerInfoData.swift`, `ChatController.swift`, `GhostBaseSettingsController.swift`, and `JerkgramStrings.swift`.
- Produces: `patch_profile_ui(text)`, `patch_chat_mentions(text)`, `patch_strings(text)`, and `patch_settings(text)` pure transforms plus markers `BUILD116_PROFILE_SCOPE1`, `BUILD116_CHAT_NUMERIC_MENTION1`, `BUILD116_STYLE_LOCALIZATION1`, and `BUILD116_ABOUT_COMMUNITY1`.

- [ ] **Step 1: Write failing profile and chat-owner tests**

  Add fixtures proving Build115's `return availablePanes` is replaced by the original bounded pane append policy, raw Settings Runtime rows are absent, `ChatController.openPeerMention` routes `@N`/`@idN` to `https://t.me/@idN`, and `resolvePeerByName` survives for usernames.

- [ ] **Step 2: Run tests and verify RED**

  Run: `python3 -m unittest tests.test_build116_ui -v`

  Expected: import failure because `apply_jerkgram_v12e_build116_ui1.py` does not exist.

- [ ] **Step 3: Implement the minimal pure transforms**

  Use exact function-boundary replacements. Numeric normalization is local to `ChatController.openPeerMention`; explicit bare numeric URL/deep-link normalization remains in `OpenUrl.swift`, and normal phone entities are unchanged.

- [ ] **Step 4: Add failing localization and About fixtures**

  Assert semantic keys for `sendStyleNormal`, `sendStyleBold`, `sendStyleItalic`, `sendStyleMonospace`, `sendStyleStrikethrough`, `sendStyleUnderline`, `sendStyleSpoiler`, `sendStyleExamplePrefix`, `sendStyleExampleBody`, `community`, `communityHint`, and `copyExtensionDiagnostics`. Assert the Settings owner contains no hardcoded Cyrillic style-page literals and About targets `https://t.me/JerkgramApp` without displaying `Bundle ID`.

- [ ] **Step 5: Run tests and verify RED for missing style/About behavior**

  Run: `python3 -m unittest tests.test_build116_ui -v`

  Expected: assertions fail on missing semantic tokens.

- [ ] **Step 6: Implement style/About transforms and final verifier**

  Pass `JerkgramStrings` into style title/entries/preview rendering. Add one native disclosure row with a localized title/subtitle and a controller argument closure that opens the canonical channel URL through Telegram's existing URL path.

- [ ] **Step 7: Verify GREEN**

  Run: `python3 -m unittest tests.test_build116_ui -v`

  Expected: all Build116 UI fixture tests pass.

### Task 2: Bounded extension stage diagnostics

**Files:**
- Create: `tests/test_build116_extensions.py`
- Create: `scripts/apply_jerkgram_v12e_build116_extensions1.py`
- Create: `scripts/verify_jerkgram_v12e_build116_extensions1.py`
- Modify: `submodules/BuildConfig/PublicHeaders/BuildConfig/BuildConfig.h`
- Modify: `submodules/BuildConfig/Sources/BuildConfig.m`

**Interfaces:**
- Consumes: the seven Build115 shared-container runtime owners and their resolved App Group paths.
- Produces: public `BuildConfig` diagnostic record/report methods shared by all seven Swift owners; one atomic JSON file per process under `telegram-data/jerkgram-extension-diagnostics/`, copied through the single Settings action. `BuildConfig` is Objective-C in Official Telegram 12.9.2, so the shared implementation extends its existing public header and `.m` owner rather than adding an invalid Swift source to an `objc_library`.

- [ ] **Step 1: Write failing transform/model tests**

  Cover all seven owners, require unique process names, bounded detail length, atomic replacement, no shared append-only log, and stage tokens `profile`, `container`, `root`, `encryption`, `account`, and `broadcastCoordination`.

- [ ] **Step 2: Run and verify RED**

  Run: `python3 -m unittest tests.test_build116_extensions -v`

  Expected: missing Build116 extension module.

- [ ] **Step 3: Implement diagnostics materialization and owner injections**

  Add the BuildConfig Swift source through its existing glob. Inject records immediately after each proven boundary; never change fallback/group choice or account data behavior. Wire one localized `Copy Extension Diagnostics` action that reads only the bounded per-process files and copies a canonical JSON report. A failed `containerURL` remains observable through `os_log` and the extension's existing visible failure behavior because no shared path exists yet.

- [ ] **Step 4: Implement strict verifier and verify GREEN**

  Run: `python3 -m unittest tests.test_build116_extensions -v`

  Expected: seven owners and all required stage boundaries pass.

### Task 3: Typed Settings and Archive v1 foundations

**Files:**
- Create: `tests/test_build116_foundation.py`
- Create: `scripts/apply_jerkgram_v12e_build116_foundation1.py`
- Create: `scripts/verify_jerkgram_v12e_build116_foundation1.py`
- Materialize: `submodules/SettingsUI/Sources/Jerkgram/JerkgramSettingsStore.swift`
- Materialize: `submodules/SettingsUI/Sources/Jerkgram/JerkgramArchive.swift`

**Interfaces:**
- Produces: `JerkgramSettingsV1: Codable, Equatable`, `JerkgramSettingsStore.load()/save(_:)`, `JerkgramArchiveManifestV1`, `JerkgramArchiveEventV1`, `JerkgramArchiveV1`, `JerkgramArchiveCodec.encode/decode`, and deterministic event identity `(accountPeerId, peerId, messageId, eventTimestamp, kind)`.

- [ ] **Step 1: Write failing schema and safety tests**

  Assert `schemaVersion == 1`, semantic enum values, deterministic merge/dedupe ordering, rejection of unsupported versions, bounded event counts, and absence of forbidden secret/signing field names.

- [ ] **Step 2: Run and verify RED**

  Run: `python3 -m unittest tests.test_build116_foundation -v`

  Expected: missing foundation overlay.

- [ ] **Step 3: Implement minimal Swift foundation sources**

  Use Foundation `Codable`, ISO-8601-compatible integer timestamps, JSONL-compatible event records, atomic settings writes, and explicit validation errors. Do not add import/export UI in Build116.

- [ ] **Step 4: Implement verifier and verify GREEN**

  Run: `python3 -m unittest tests.test_build116_foundation -v`

  Expected: schema, safety, merge, and source invariant tests pass.

### Task 4: Canonical Build116 chain and publishing

**Files:**
- Create: `tests/test_build116_wiring.py`
- Create: `scripts/install_jerkgram_v12e_build116_probe_hook.py`
- Create: `scripts/jerkgram_publish_build116_artifact.py`
- Modify: `.github/workflows/build.yml`
- Modify: `.github/workflows/build-official.yml`

**Interfaces:**
- Consumes: the three Build116 apply/verify pairs.
- Produces: Build115 chain → Build116 UI → extensions → foundation → Bazel; artifact `Jerkgram-build116.ipa`.

- [ ] **Step 1: Write failing wiring tests**

  Assert each apply/verify occurs exactly once after Build115 numeric verification and before Bazel; assert both workflows and publisher use Build116 names only for active visible artifacts.

- [ ] **Step 2: Run and verify RED**

  Run: `python3 -m unittest tests.test_build116_wiring -v`

  Expected: Build116 installer/publisher missing.

- [ ] **Step 3: Implement installer and mechanical publishing rename**

  Reuse Build115 finalization; do not rerun finalizers on already-finalized artifacts. Only active workflow/artifact labels advance to Build116.

- [ ] **Step 4: Verify GREEN**

  Run: `python3 -m unittest tests.test_build116_wiring -v`

  Expected: canonical order and naming pass.

### Task 5: Full local preflight and review

**Files:**
- Verify: all Build116 scripts/tests and bounded diff.

- [ ] **Step 1: Compile Python scripts**

  Run: `python3 -m py_compile scripts/*build116*.py tests/test_build116_*.py`

- [ ] **Step 2: Run all focused tests**

  Run: `python3 -m unittest discover -s tests -p 'test_build11*.py' -v`

- [ ] **Step 3: Run patchers/verifiers against isolated fixtures/materialized copies**

  Confirm every marker count, function survival, no active hardcoded Cyrillic style literals, seven diagnostic owners, two foundation Swift files, and Build116-before-Bazel order.

- [ ] **Step 4: Review bounded diff and commit**

  Inspect `git diff --check`, `git status --short`, and `git diff --stat`. Commit only Build116 files and intended workflow changes with message `Build Jerkgram Build116 stabilization foundation`.

- [ ] **Step 5: Push/update GitHub branch and hand off runtime matrix**

  Confirm remote HEAD, then ask the user to run `Jerkgram 12.9.2 Build116`. Device acceptance covers numeric routes, restored profile panes, absent raw Settings logs, complete RU/EN style UI, About channel row, Share content/error stage, Widget data/stage, Broadcast timer/stage, and regression locks.
