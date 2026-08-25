# Jerkgram Build119 Hybrid UI Implementation Plan

**Goal:** ship Build119 as a genuine, user-visible Jerkgram visual pass on top of the green Build118 baseline without replacing Official Telegram 12.9.2 profile/navigation geometry or regressing the Build118 capture/performance repair.

## Source / owner map

- Official Telegram 12.9.2 remains geometry/API source of truth.
- Materialized Jerkgram Settings owner: `submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift` (legacy path only).
- Jerkgram localization owner: `submodules/TelegramPresentationData/Sources/JerkgramStrings.swift`.
- Build118 Data UI owner: `submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift`.
- Build118 Time Machine UI owner: `submodules/SettingsUI/Sources/Jerkgram/JerkgramTimeMachineController.swift`.
- Final public/resign-ready IPA is produced at `ghostbase-final/GhostBase.ipa` by the legacy finalization chain.
- Build119 must be a late Jerkgram-owned overlay after all Build118 overlays and before Bazel, with final IPA identity stamping/verifying after the existing Build113/114 finalizers.

## Product contract

1. Root Settings gets a compact Jerkgram summary row/surface with Build119 identity and a coherent grouping of Jerkgram feature routes. No universal purple tint, per-cell blur, giant pills, or heavy shadows.
2. Basic Functions no longer exposes `localStarsAmount` as a permanent text field. It exposes a compact Stars value/action row. Editing happens on a dedicated Stars page.
3. Data & Backup gets a compact account/storage policy summary before detailed controls. Export/import remain explicit actions and account-scoped.
4. Time Machine gets a compact summary of loaded results/filter state before filters/results. Existing bounded paging and off-main loading remain intact.
5. About shows Jerkgram, Official Telegram 12.9.2, Build 119, channel and community actions.
6. Profile geometry is not replaced by Build119. No new PeerInfo container/header owner is introduced.
7. Jerkgram-generated Build119 copy follows `JerkgramStrings` EN canonical + RU selection through Telegram presentation language.

## Build identity contract

- Workflow: `Jerkgram 12.9.2 Build119`.
- Artifact: `Jerkgram-build119`.
- IPA: `artifacts/Jerkgram-build119.ipa`.
- Info: `artifacts/Jerkgram-build119-info.txt`.
- The final public/resign-ready IPA must contain exactly one main app whose `CFBundleDisplayName == Jerkgram` and `CFBundleVersion == 119`.
- All bundled `.appex` Info.plists are stamped to `CFBundleVersion == 119` as part of the same final identity step.
- Publisher independently re-opens the final IPA and rejects any embedded build other than `119`; filename/metadata alone is insufficient.

## TDD / implementation order

### Task 1 — RED contract
Create `tests/test_jerkgram_v12h_build119_hybrid_ui1.py` before production files. It must fail on the Build118 baseline because Build119 overlay/publisher/workflow wiring does not exist.

### Task 2 — Build119 Settings overlay
Create `scripts/apply_jerkgram_v12h_build119_hybrid_ui1.py` and `scripts/verify_jerkgram_v12h_build119_hybrid_ui1.py`.

The patch must use exact owner/function boundaries and assert occurrence counts. It may extend legacy `GhostBaseSettingsPage` because that enum is the current materialized route owner, but all new public components/markers/files use `Jerkgram*` naming.

Implement:
- `case stars` + localized title/route;
- root Jerkgram Build119 summary route;
- Basic Functions Stars value disclosure; remove permanent root `.input(...localStarsAmount...)`;
- dedicated Stars page containing enable state, current balance summary, and the numeric editor;
- Build119 About identity/channel/community copy;
- semantic EN/RU Build119 strings.

### Task 3 — Build119 Data / Time Machine polish
Patch the copied Build118 Jerkgram controllers late, without changing storage/query semantics:
- add a summary entry type backed by existing Telegram ItemList primitives;
- Data summary reflects current account policy/account ID;
- Time Machine summary reflects loaded result count and active filter count;
- preserve `Queue.concurrentDefaultQueue().async`, `eventPage(limit: 250)`, load-more behavior, account scoping and retention logic.

### Task 4 — Genuine build identity
Create `scripts/jerkgram_finalize_build119_identity.py` and `scripts/verify_jerkgram_v12h_build119_final_ipa.py`.

Run identity finalizer only once, after the existing Build114 public/resign-ready finalizer. It edits plist identity only; it must not rerun the Build114 finalizer on an already-finalized artifact.

Create `scripts/jerkgram_publish_build119_artifact.py`; publisher verifies embedded identity again and byte-copies the already-finalized IPA.

### Task 5 — Canonical chain
Update `scripts/bazel_build_probe_official.sh` so Build119 apply/verify runs immediately after the final Build118 source verifier and before Bazel. Add final Build119 identity+IPA verifier after existing Build114 finalization.

Update `.github/workflows/build.yml`:
- py_compile Build119 scripts;
- workflow/artifact names = Build119;
- publish with Build119 publisher.

### Task 6 — Preflight / diff scope
Before moving the main branch:
- run/inspect Build119 contract;
- verify no Build118 performance source is rewritten;
- verify no Build119 patch targets PeerInfo header/container geometry;
- verify workflow references only files that exist;
- compare work branch against `4ea428f4d182aaa6f92708bfcd5533489dfeb190` and inspect scope.

### Task 7 — CI and artifact gate
Fast-forward `Jerkgram-12.9.2` only after source contract is green. Let one full GitHub Actions run compile/package Build119.

If green, download the workflow artifact and independently inspect `Payload/*.app/Info.plist` for `CFBundleVersion=119`, `CFBundleDisplayName=Jerkgram`, bundle topology, hash and artifact naming.

## Runtime gate

Compile/artifact success does not prove visual smoothness. On-device Build119 test remains required for:
- cold launch and rapid typing/scrolling/chat switching;
- Settings root + Stars editor + Data & Backup + Time Machine + About;
- RU/EN switching with Telegram language;
- Share/Broadcast/Widget regression status;
- profile fullscreen/native header/Premium/Gifts/shared media geometry;
- deleted/edited/recovered capture and Time Machine paging.
