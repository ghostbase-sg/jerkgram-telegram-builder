# Jerkgram Jank Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a low-overhead, release-safe Jank Probe that records severe frame gaps for the Settings/animated-avatar and Chat/typing reproductions, exposes a hidden report action, and does not change runtime behavior being diagnosed.

**Architecture:** Keep bounded diagnostic state and report formatting in neutral `JerkgramCore`; keep the single `CADisplayLink` owner in `TelegramUI`; instrument only the Settings/profile and chat-input owners needed for the first two reproductions. Integrate via one Build141 apply script, verifier, unit/source-contract test, and the existing Build140 materialization hook.

**Tech Stack:** Python 3 patch/verifier/unit tests; Swift 5; UIKit/CoreAnimation `CADisplayLink`; Foundation monotonic timing; existing Jerkgram patch-chain/Bazel build.

**Spec:** `docs/superpowers/specs/2026-09-14-jank-probe-design.md`

## Global Constraints

- Base source is Official Telegram 12.9.2 at `6ad963e5b62d354da79040f388ae2b9132fb17b8`.
- Current builder branch is `dev/build133-runtime-repair`; Build140 is already appended by `scripts/install_jerkgram_v12w_build133_probe_hook.py`.
- This phase is diagnostic only: do not change avatar loading policy, `synchronousLoad`, filtering, history, read-state, Ghost Mode semantics, media behavior, or Settings appearance.
- Exactly one diagnostic `CADisplayLink` owner may exist.
- No per-frame file I/O, `UserDefaults`, JSON encoding, clipboard work, heap-heavy string formatting, Postbox/history scan, or network telemetry.
- All event storage is fixed/bounded and overwrites oldest records.
- No new visible Debug section; normal tap behavior of existing Settings rows stays unchanged.
- Do not add a `TelegramCore -> TelegramUI` dependency.
- Reuse the existing Build137 memory sampler rather than creating a second continuous RAM sampler.
- `>= 33 ms` is a hitch, `>= 100 ms` severe, `>= 250 ms` critical.
- Runtime conclusions require DEVICE-RUNTIME evidence; verifier/compile success is not proof of the root cause.

---

## File map

**Create**
- `scripts/apply_jerkgram_build141_jank_probe1.py` — materializes the bounded Swift probe and adds targeted source hooks.
- `scripts/verify_jerkgram_build141_jank_probe1.py` — verifies source ownership, single display-link owner, fixed capacities, hidden report action, and preservation contracts.
- `tests/test_jerkgram_build141_jank_probe1.py` — RED/GREEN source-contract suite using synthetic fixtures plus static forbidden-pattern checks.

**Modify**
- `scripts/install_jerkgram_v12w_build133_probe_hook.py` — append Build141 apply/verifier immediately after `verify_jerkgram_build140_identity.py` and before `verify_jerkgram_v12w_build133_runtime_repair1.py`.
- `.github/workflows/build.yml` — py_compile the Build141 scripts and run the Build141 test before materialization/Bazel.

**Materialized source modified by the apply script**
- `submodules/JerkgramCore/Sources/JerkgramJankProbe.swift` — bounded store, enums, counters, snapshots, report formatter.
- `submodules/TelegramUI/Sources/JerkgramJankDisplayLink.swift` — the only `CADisplayLink` owner and frame-gap classification.
- `submodules/TelegramUI/Sources/AppDelegate.swift` — one-time startup call for the display-link monitor, after existing app startup ownership.
- `submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift` — scoped profile-background region markers only; preserve Build120 `synchronousLoad: true, completeOnly: true` unchanged.
- `submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift` — outer text-input update/typing region and call counter only.
- `submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift` — Settings context/scroll markers and hidden long-press report access on Jerkgram Version.
- `submodules/JerkgramCore/BUILD`, `submodules/TelegramUI/BUILD`, `submodules/SettingsUI/BUILD` only if the current source lists/dependencies require explicit additions; the patch must first assert the exact existing `glob`/dependency form and make no BUILD edit when the source is already included transitively.

---

### Task 1: RED contract for bounded probe architecture

**Files:**
- Create: `tests/test_jerkgram_build141_jank_probe1.py`
- Create: `scripts/apply_jerkgram_build141_jank_probe1.py`

**Interfaces:**
- Consumes: synthetic Swift fixtures for JerkgramCore, AppDelegate, Settings, profile background, and chat input panel.
- Produces: pure Python `patch_*_text()` functions that later tasks fill in.

- [ ] **Step 1: Write the failing unit/source-contract tests**

Create tests that import `scripts.apply_jerkgram_build141_jank_probe1` and assert these exact contracts after patching fixtures:

```python
self.assertEqual(core.count("public final class JerkgramJankProbe"), 1)
self.assertIn("static let hitchCapacity = 64", core)
self.assertIn("static let regionCapacity = 256", core)
self.assertNotIn("UserDefaults.standard", core)
self.assertNotIn("JSONEncoder", core)
self.assertNotIn("FileHandle", core)

self.assertEqual(display.count("CADisplayLink("), 1)
self.assertIn("durationMs >= 250.0", display)
self.assertIn("durationMs >= 100.0", display)
self.assertIn("durationMs >= 33.0", display)

self.assertIn("JerkgramJankRegion.profileBackground", profile)
self.assertIn("synchronousLoad: true", profile)
self.assertIn("completeOnly: true", profile)

self.assertIn("JerkgramJankRegion.chatTextInput", chat)
self.assertIn("JerkgramJankProbe.shared.noteTyping", chat)

self.assertIn("BUILD141_JANK_REPORT_LONG_PRESS1", settings)
self.assertIn("UIPasteboard.general.string", settings)
```

Also assert idempotency by running every patch function twice and comparing byte-for-byte output.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest tests.test_jerkgram_build141_jank_probe1 -v
```

Expected: FAIL because the Build141 materialization functions/source payload do not yet exist.

- [ ] **Step 3: Add only patch-script scaffolding**

Define exact path constants and helpers in `apply_jerkgram_build141_jank_probe1.py`:

```python
ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
CORE = ROOT / "submodules/JerkgramCore/Sources/JerkgramJankProbe.swift"
DISPLAY = ROOT / "submodules/TelegramUI/Sources/JerkgramJankDisplayLink.swift"
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
PROFILE = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift"
CHAT_INPUT = ROOT / "submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift"
MARKER = "Jerkgram v1.0.2 BUILD141_JANK_PROBE1"
```

Implement `require`, brace-balanced owner lookup, `replace_once`, and idempotency markers. Do not materialize Swift yet.

- [ ] **Step 4: Run syntax check**

```bash
python3 -m py_compile scripts/apply_jerkgram_build141_jank_probe1.py tests/test_jerkgram_build141_jank_probe1.py
```

Expected: PASS; unit test remains RED.

- [ ] **Step 5: Commit**

```bash
git add scripts/apply_jerkgram_build141_jank_probe1.py tests/test_jerkgram_build141_jank_probe1.py
git commit -m "test: define Build141 jank probe contract"
```

---

### Task 2: Materialize bounded core store and single display-link owner

**Files:**
- Modify: `scripts/apply_jerkgram_build141_jank_probe1.py`
- Test: `tests/test_jerkgram_build141_jank_probe1.py`

**Interfaces:**
- Produces Swift public API:

```swift
public enum JerkgramJankContext: UInt8 { case other, settings, chat }
public enum JerkgramJankRegion: UInt8 { case settingsUpdate, profileBackground, avatarRequest, chatTextInput, typingPolicy }
public struct JerkgramJankRegionToken { let region: JerkgramJankRegion; let startedAt: CFTimeInterval }
public final class JerkgramJankProbe {
    public static let shared: JerkgramJankProbe
    public func setContext(_ context: JerkgramJankContext)
    public func noteScrolling(_ active: Bool)
    public func noteTyping(_ active: Bool)
    public func noteAnimatedAvatar(_ active: Bool)
    public func begin(_ region: JerkgramJankRegion) -> JerkgramJankRegionToken
    public func end(_ token: JerkgramJankRegionToken)
    public func recordFrameGap(timestamp: CFTimeInterval, durationMs: Double, severity: UInt8)
    public func makeTextReport() -> String
}
```

- [ ] **Step 1: Extend RED tests for bounded storage and hot-path safety**

Assert the generated core source contains capacities `64` hitches and `256` region events, integer/enum identifiers rather than per-event strings, and no hot-path `UserDefaults`, JSON, disk, clipboard, peer/message payloads, or unbounded `append` without capacity overwrite logic.

Assert the display-link source has one `CADisplayLink`, uses `link.timestamp`, and forwards only classified gaps to `JerkgramJankProbe.shared.recordFrameGap`.

- [ ] **Step 2: Run tests and verify RED**

```bash
python3 -m unittest tests.test_jerkgram_build141_jank_probe1 -v
```

Expected: FAIL on missing core/display-link payloads.

- [ ] **Step 3: Implement the minimal Swift payloads in the apply script**

Core rules:
- preallocate fixed `ContiguousArray`/fixed-capacity storage once;
- overwrite by modulo index;
- use `CACurrentMediaTime()`/monotonic `CFTimeInterval` tokens;
- no formatted strings until `makeTextReport()`;
- report contains only build/probe version, contexts, timestamps/durations, region IDs/names, counts, RAM snapshot if available, thermal state at report time;
- no peer/message/user content.

Display-link rules:

```swift
@objc private func step(_ link: CADisplayLink) {
    let now = link.timestamp
    defer { self.previousTimestamp = now }
    guard let previous = self.previousTimestamp else { return }
    let durationMs = (now - previous) * 1000.0
    let severity: UInt8
    if durationMs >= 250.0 { severity = 3 }
    else if durationMs >= 100.0 { severity = 2 }
    else if durationMs >= 33.0 { severity = 1 }
    else { return }
    JerkgramJankProbe.shared.recordFrameGap(timestamp: now, durationMs: durationMs, severity: severity)
}
```

Startup patch: inject one `JerkgramJankDisplayLink.shared.start()` call into AppDelegate's existing launch path. `start()` is idempotent and keeps exactly one display link scheduled in `.common` mode.

- [ ] **Step 4: Run focused tests**

```bash
python3 -m unittest tests.test_jerkgram_build141_jank_probe1 -v
```

Expected: core/display-link tests PASS; Settings/profile/chat tests may still be RED until later tasks.

- [ ] **Step 5: Commit**

```bash
git add scripts/apply_jerkgram_build141_jank_probe1.py tests/test_jerkgram_build141_jank_probe1.py
git commit -m "feat: add bounded Build141 frame hitch recorder"
```

---

### Task 3: Instrument Settings/profile and add hidden report retrieval

**Files:**
- Modify: `scripts/apply_jerkgram_build141_jank_probe1.py`
- Test: `tests/test_jerkgram_build141_jank_probe1.py`
- Materializes: `GhostBaseSettingsController.swift`, `GhostBaseProfileFullscreenBackground.swift`

**Interfaces:**
- Consumes `JerkgramJankProbe.shared` public API from Task 2.
- Produces hidden long-press report action while preserving `.aboutValue(1, 1, strings.jerkgramVersion, JerkgramReleaseIdentity.displayVersion)` as the visible Version row.

- [ ] **Step 1: Add RED tests for the exact existing owners**

Fixture must contain the current Build139 release-bound row:

```swift
.aboutValue(1, 1, strings.jerkgramVersion, JerkgramReleaseIdentity.displayVersion)
```

and the Build120 profile call:

```swift
synchronousLoad: true,
completeOnly: true
```

Assert patching:
- does not alter those two avatar arguments;
- wraps the existing profile-background update owner in `begin(.profileBackground)` / `defer { end(...) }`;
- sets Settings context when the About/Settings controller is visible and returns to `.other` on disappearance/deinit using existing lifecycle ownership;
- attaches exactly one `UILongPressGestureRecognizer` for the Jerkgram Version row/report action;
- keeps normal tap behavior unchanged;
- builds report/copies clipboard only inside the gesture handler;
- does not create a visible Debug row/section.

- [ ] **Step 2: Run tests and verify RED**

```bash
python3 -m unittest tests.test_jerkgram_build141_jank_probe1.JankProbeSettingsProfileTests -v
```

Expected: FAIL on missing instrumentation/report gesture.

- [ ] **Step 3: Implement targeted Settings/profile hooks**

For Settings, use the existing GhostBase Settings controller/list lifecycle. Add a private long-press handler whose only expensive operation is on `.ended`:

```swift
@objc private func jerkgramHandleJankReportLongPress(_ gesture: UILongPressGestureRecognizer) {
    guard gesture.state == .ended else { return }
    UIPasteboard.general.string = JerkgramJankProbe.shared.makeTextReport()
}
```

Attach it only to the rendered Version row node after that row becomes available; set `cancelsTouchesInView = false` so normal taps/scrolling are unchanged. The source marker is `BUILD141_JANK_REPORT_LONG_PRESS1`; the patch must reject more than one attachment site.

For profile background, add only scoped region timing and a bounded update counter around the existing Jerkgram-owned update/request owner. Do not move work between queues and do not change image/video/blur/cache behavior.

- [ ] **Step 4: Run focused tests**

```bash
python3 -m unittest tests.test_jerkgram_build141_jank_probe1.JankProbeSettingsProfileTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/apply_jerkgram_build141_jank_probe1.py tests/test_jerkgram_build141_jank_probe1.py
git commit -m "feat: instrument Settings profile jank path"
```

---

### Task 4: Instrument outer chat text-input path without touching TelegramCore semantics

**Files:**
- Modify: `scripts/apply_jerkgram_build141_jank_probe1.py`
- Test: `tests/test_jerkgram_build141_jank_probe1.py`
- Materializes: `submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift`

**Interfaces:**
- Uses `JerkgramJankRegion.chatTextInput` and `noteTyping(_:)`.
- Does not add a TelegramCore dependency on the probe.

- [ ] **Step 1: Add RED fixture for Telegram 12.9.2 `ChatTextInputPanelNode`**

Use the upstream owner at `submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift` and anchor the patch to the existing text-node delegate/update owner reached when text changes. Assert exactly one scoped `begin(.chatTextInput)` token per update owner and one bounded call counter.

Also assert that `ManagedLocalInputActivities.swift`, Postbox transaction code, and TelegramCore files are not modified by this Build141 patch.

- [ ] **Step 2: Run focused test and verify RED**

```bash
python3 -m unittest tests.test_jerkgram_build141_jank_probe1.JankProbeChatInputTests -v
```

Expected: FAIL on missing chat-input instrumentation.

- [ ] **Step 3: Implement only the outer UI instrumentation**

At the text-change/update owner:

```swift
let jerkgramJankToken = JerkgramJankProbe.shared.begin(.chatTextInput)
defer { JerkgramJankProbe.shared.end(jerkgramJankToken) }
JerkgramJankProbe.shared.noteTyping(true)
```

Clear typing from the existing input-end/empty-state path; do not create a timer merely to clear it. If the existing state does not expose a reliable end signal, leave the flag as “recent input active” in the report and rely on region timing rather than adding observers.

Do not instrument Postbox or Activity Ghost internals in phase 1. If DEVICE-RUNTIME capture shows the outer input region is long, the next bounded pass can instrument one enclosing/inner owner with evidence.

- [ ] **Step 4: Run focused tests**

```bash
python3 -m unittest tests.test_jerkgram_build141_jank_probe1.JankProbeChatInputTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/apply_jerkgram_build141_jank_probe1.py tests/test_jerkgram_build141_jank_probe1.py
git commit -m "feat: instrument Build141 chat input jank path"
```

---

### Task 5: Add verifier and canonical Build140→Build141 wiring

**Files:**
- Create: `scripts/verify_jerkgram_build141_jank_probe1.py`
- Modify: `scripts/install_jerkgram_v12w_build133_probe_hook.py`
- Modify: `.github/workflows/build.yml`
- Test: `tests/test_jerkgram_build141_jank_probe1.py`

**Interfaces:**
- Canonical source order becomes Build140 identity → Build141 Jank Probe apply → Build141 verifier → existing Build133 runtime-repair verifier → native Type1 diagnostics → Bazel.

- [ ] **Step 1: Add RED wiring/verifier tests**

Assert `SOURCE_ORDERED` contains exactly once and in this order:

```python
"verify_jerkgram_build140_identity.py",
"apply_jerkgram_build141_jank_probe1.py",
"verify_jerkgram_build141_jank_probe1.py",
"verify_jerkgram_v12w_build133_runtime_repair1.py",
```

Verifier tests must reject:
- more than one `CADisplayLink(`;
- missing fixed capacities;
- `UserDefaults`, `JSONEncoder`, `FileHandle`, or network calls in probe hot-path source;
- missing hidden Version long press;
- mutation/removal of `synchronousLoad: true` or `completeOnly: true` in the Build120 profile owner;
- changes to filtering/history owners;
- visible `.debugResearch` insertion caused by Build141.

- [ ] **Step 2: Run test and verify RED**

```bash
python3 -m unittest tests.test_jerkgram_build141_jank_probe1 -v
```

Expected: FAIL on missing verifier/wiring.

- [ ] **Step 3: Implement verifier**

`verify_jerkgram_build141_jank_probe1.py` reads materialized sources and enforces the contracts above. It prints only compact GREEN diagnostics; it must not mutate source.

- [ ] **Step 4: Wire current installer**

In `install_jerkgram_v12w_build133_probe_hook.py`, insert the two Build141 entries immediately after `verify_jerkgram_build140_identity.py`. Keep all existing Build140 Premium Icons / Download Boost2 / No Ads / identity order unchanged.

- [ ] **Step 5: Wire workflow preflight**

Add both scripts to `.github/workflows/build.yml` `py_compile`, and add:

```bash
python3 -m unittest tests.test_jerkgram_build141_jank_probe1
```

beside the current Build137/Build140-era regression gates, before the canonical materialization hook runs.

- [ ] **Step 6: Run complete preflight**

```bash
python3 -m py_compile \
  scripts/apply_jerkgram_build141_jank_probe1.py \
  scripts/verify_jerkgram_build141_jank_probe1.py
python3 -m unittest tests.test_jerkgram_build141_jank_probe1 -v
python3 -m unittest tests.test_jerkgram_v12zd_build137_performance1 -v
python3 -m unittest tests.test_jerkgram_build137_performance2 -v
```

Expected: all PASS.

- [ ] **Step 7: Materialization verifier pass before any full build**

Against a freshly prepared Official Telegram 12.9.2 tree, run the existing canonical installer, then:

```bash
python3 scripts/verify_jerkgram_build141_jank_probe1.py
```

Expected: GREEN, exactly one display-link owner, profile synchronous-load contract preserved, no forbidden hot-path persistence.

- [ ] **Step 8: Commit**

```bash
git add \
  scripts/verify_jerkgram_build141_jank_probe1.py \
  scripts/install_jerkgram_v12w_build133_probe_hook.py \
  .github/workflows/build.yml \
  tests/test_jerkgram_build141_jank_probe1.py
git commit -m "build: wire Build141 jank probe diagnostics"
```

---

### Task 6: Build once, then capture DEVICE-RUNTIME evidence

**Files:**
- No source change unless compile/verifier reveals a real integration defect.

**Interfaces:**
- Produces one installed probe build and two copied text reports.

- [ ] **Step 1: Run canonical CI build after all source/verifier gates are GREEN**

Do not start a full build while source-contract or materialization verification is failing.

- [ ] **Step 2: Settings torture capture**

On device:
1. Open Jerkgram Settings with animated avatar active.
2. Scroll top↕bottom rapidly for 30–60 seconds.
3. Reproduce at least one visible freeze if possible.
4. Open About and long-press Jerkgram Version.
5. Paste the copied report back into the development chat.

- [ ] **Step 3: Chat typing capture**

On device:
1. Open a representative active chat.
2. Type continuously/re-enter input until the known FPS collapse occurs.
3. Long-press Jerkgram Version and paste the new report.

- [ ] **Step 4: Interpret without speculative fixing**

Classify each severe hitch as:
- long overlapping instrumented main-thread region → that owner is on the critical path;
- frame gap with no matching region → expand instrumentation one enclosing layer next;
- repeated call-count growth across the same interaction → investigate duplicated callback/subscription/update ownership;
- no UI-region attribution despite visible freeze → investigate compositor/video/GPU with the next evidence pass.

No optimization patch is made until one of these evidence paths identifies the next bounded owner.

---

## Self-review checklist

- Spec coverage: frame timing, bounded buffer, Settings/profile, chat input, hidden report, preservation constraints, patch-chain integration, verifier, and device protocol are all mapped to tasks.
- No placeholder implementation steps: every task names exact builder files, source owners, APIs, commands, and expected RED/GREEN outcome.
- Dependency direction: shared state lives in neutral JerkgramCore; TelegramUI owns CADisplayLink; no TelegramCore → TelegramUI dependency is introduced.
- Type consistency: `JerkgramJankContext`, `JerkgramJankRegion`, `JerkgramJankRegionToken`, and `JerkgramJankProbe.shared` names are consistent across Tasks 2–5.
- Scope remains diagnostic: Build120 avatar policy and Build137 performance behavior are explicit preservation gates.
