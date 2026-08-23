# Jerkgram Build117 Runtime Boundaries and Release Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a verifier-first Build117 patch that fixes the Settings/self-profile scope, adds a live About channel credit, exposes local extension failure stages, and makes release readiness an enforced pre-Bazel gate.

**Architecture:** Add three bounded late overlays after Build116: UI scope/About, extension-local diagnostics, and release readiness/wiring. Keep the historical chain intact, classify paths without changing storage selection, and publish one canonical success artifact. Build117 diagnostics gather the evidence needed for the later signing/compatibility decision while the UI changes are independently complete.

**Tech Stack:** Python 3 patchers/verifiers and `unittest`; Swift 5; TelegramEngine/Postbox; ItemListPeerItem; SwiftUI/WidgetKit; ReplayKit; Bazel/GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-23-jerkgram-build117-release-readiness.md`

## Global Constraints

- Official Telegram iOS 12.9.2 is the API and geometry source of truth.
- Write a failing fixture before each production transform.
- Do not change App Group selection or storage roots in the diagnostic overlay.
- Never expose a complete sandbox UUID/path in user-visible diagnostics.
- Preserve typed `JerkgramSettingsV1` and `JerkgramArchiveV1`; do not add import/export UI yet.
- Build green is not runtime success.
- Do not run Bazel locally.

---

### Task 1: Settings/self-profile scope

**Files:**
- Create: `tests/test_build117_profile_scope.py`
- Create: `scripts/apply_jerkgram_v12f_build117_profile_scope1.py`
- Create: `scripts/verify_jerkgram_v12f_build117_profile_scope1.py`
- Materialized owner: `submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoData.swift`

**Interfaces:**
- Produces `ghostBaseAppendingProfilePanes(..., isSettings: Bool)`.
- `PeerInfoScreenData.init` receives `isSettings: Bool = false` and the Settings data constructor passes `true` explicitly.

- [ ] Write a failing fixture proving Build116 appends custom panes to both routes.
- [ ] Run `python3 -m unittest tests.test_build117_profile_scope -v` and confirm failure on the missing `isSettings` contract.
- [ ] Implement the minimal transform: return stock panes when `isSettings`, preserve Build116 append behavior otherwise, and mark `BUILD117_SETTINGS_PROFILE_SCOPE1`.
- [ ] Add a final-source verifier that requires every Settings constructor path to pass the explicit flag and rejects universal suppression/universal append.
- [ ] Re-run the focused test and confirm green.

### Task 2: Live About channel credit

**Files:**
- Create: `tests/test_build117_about_channel.py`
- Create: `scripts/apply_jerkgram_v12f_build117_about_channel1.py`
- Create: `scripts/verify_jerkgram_v12f_build117_about_channel1.py`
- Materialized owners: `submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift`, `submodules/TelegramPresentationData/Sources/JerkgramStrings.swift`

**Interfaces:**
- Produces `JerkgramAboutChannelState` with `.loading`, `.available(peer: EnginePeer, preview: String)`, and `.unavailable`.
- Adds a `GhostBaseSettingsEntry.aboutChannel` rendered with `ItemListPeerItem` and existing `AccountContext`.
- Resolves `JerkgramApp`, obtains a bounded latest regular message preview, and opens the resolved peer through `navigateToChatController`/existing shared-context navigation.

- [ ] Write failing fixtures for semantic strings, avatar-capable native peer item, latest-post preview, fallback state, and no static URL disclosure.
- [ ] Run `python3 -m unittest tests.test_build117_about_channel -v` and confirm failure for the absent state/item.
- [ ] Implement the smallest transform and keep the About version/build text concise.
- [ ] Add verifier invariants: canonical username once, no fabricated peer, preview length bounded, ordinary Telegram resolver retained.
- [ ] Re-run the focused test and confirm green.

### Task 3: Extension-local stage surfaces

**Files:**
- Create: `tests/test_build117_extension_boundaries.py`
- Create: `scripts/apply_jerkgram_v12f_build117_extension_boundaries1.py`
- Create: `scripts/verify_jerkgram_v12f_build117_extension_boundaries1.py`
- Materialized owners: `submodules/BuildConfig/PublicHeaders/BuildConfig/BuildConfig.h`, `submodules/BuildConfig/Sources/BuildConfig.m`, `Telegram/Share/ShareRootController.swift`, `Telegram/WidgetKitWidget/TodayViewController.swift`, `Telegram/BroadcastUpload/BroadcastUploadExtension.swift`

**Interfaces:**
- Produces `jerkgramContainerPathClassification(_:)` and redacted diagnostic summaries.
- Share owns a visible failure controller, Widget owns a `.diagnostic(String)` timeline state, Broadcast owns a stage-specific `NSError` description.

- [ ] Write failing model tests for `shared`, `processLocal`, `missing`, and `other`, plus UUID/path redaction.
- [ ] Run `python3 -m unittest tests.test_build117_extension_boundaries -v` and confirm failure for the absent classifier/surfaces.
- [ ] Implement the shared classifier and inject only diagnostic presentation; do not change group selection or root path.
- [ ] Add strict verifier counts for three processes and reject full path interpolation in visible strings.
- [ ] Re-run the focused test and confirm green.

### Task 4: Release-readiness gate and Build117 wiring

**Files:**
- Create: `tests/test_build117_release_readiness.py`
- Create: `scripts/verify_jerkgram_v12f_build117_release_readiness1.py`
- Create: `scripts/install_jerkgram_v12f_build117_probe_hook.py`
- Create: `scripts/jerkgram_publish_build117_artifact.py`
- Modify: `.github/workflows/build.yml`
- Modify: `.github/workflows/build-official.yml`

**Interfaces:**
- Produces Build116 → Build117 profile → About → extension boundary → release verifier → Bazel order.
- Publishes one `Jerkgram-build117` success artifact.

- [ ] Write failing tests for exact chain order, Build117 names, foundation preservation, raw Runtime UI rejection, and duplicate success-artifact rejection.
- [ ] Run `python3 -m unittest tests.test_build117_release_readiness -v` and confirm failure on missing Build117 wiring.
- [ ] Implement the installer, release verifier, publisher, and workflow rename/removal of the duplicate success upload.
- [ ] Re-run focused tests and confirm green.

### Task 5: Full preflight and commit

**Files:**
- Verify all Build117 scripts/tests and the bounded repository diff.

**Interfaces:**
- Produces a commit-ready same-branch Build117 source state; no IPA and no runtime claim.

- [ ] Run `python3 -m py_compile scripts/*build117*.py tests/test_build117_*.py`.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_build11*.py' -v`.
- [ ] Run `git diff --check`, inspect `git status --short`, and confirm no unrelated files.
- [ ] Commit only Build117 files and intended workflow changes with message `Prepare Jerkgram Build117 runtime boundaries`.
- [ ] Update the GitHub branch and report the exact commit/remote HEAD; ask the user to run the Build117 workflow.
