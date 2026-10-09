# P0 profile performance: bounded source audit / diagnostic handoff

Status: **PATCHED, NOT COMPILED**. Actual P0 cause: **UNKNOWN / NEEDS FOCUSED AUDIT on device**.
No animation, blur quality, background, playback policy, stock geometry or actions disabled/changed.
No build, push or CI dispatch authorized for this session.

## Provenance and scope

Builder parent: b192c2c9fcdf434666a7c4288837651d1927ac10; remote published parent aa47856794a6dfe58f5e2c607c5504d6c4e98348 (same tree).
Official Telegram pin: f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838.
Build144 CI 37924326552 completed GREEN; not a runtime result for this delta.
The 19.4-second recording shows different avatar/account configurations in Swiftgram and Jerkgram; recording build number is not established. It supports reported UI stalls, not controlled attribution to animated playback or glass.

Only 15 target Swift owners were materialized. No broad source/history/Swiftgram audit.
`P/` below means `submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/`.

## Active script chain and generated runtime code

`.github/workflows/build.yml` → `scripts/build_jg13.sh` → `scripts/materialize_jg13.py`:
clean pinned source → `jg13-stable.product.patch` → `jg13-beta1-followup.patch` → `materialize_jg13_profile_cleanup.py` → new `materialize_jg13_profile_p0.py`.
Each stage checks full expected owner hashes, not markers. New stage requires exact parent hashes and refuses reapplication. Legacy profile installers are not invoked by this source-based chain. Python does not execute in the iPhone client; regression can originate in its generated Swift.

| Owner / function | Frequency, thread and custom work | Repetition / lifetime / disposal |
|---|---|---|
| P/PeerInfoScreen.swift: containerLayoutUpdated, updateData | Main; layout/scroll/data. Invokes custom background and avatar owner refresh. Settings uses self-profile scene, unlike Chat List. | One background owner constructed in init. Appearance gates active state; disappearance deactivates. Whole layout/data spans now measured; native work inside spans must not be attributed wholly to Jerkgram. |
| P/PeerInfoHeaderNode.swift: update | Main; repeated header/layout updates call avatar transition update. | No additional owner constructed by this transition path. |
| P/PeerInfoAvatarTransformContainerNode.swift: updateTransitionFraction | Main; custom keepVideoAlive branch calls play on repeated transitions when animated background is enabled. | Static call path reaches NativeVideoContent → V2 play → resetMediaDataStarvation/updateInternalState. Repeated call is proven; cost/cause of P0 is not. Stock fraction-zero branch also calls play. No deduplication patch without measured evidence. |
| P/GhostBaseProfileFullscreenBackground.swift: update/apply/refreshAnimatedVideoOwner/setSceneActive | Main state/layout; resource/representation preparation on concurrent queue, main delivery. Owns image/effect/tint stack and secondary display layer. | Stack persistent. stateKey/loadKey guards; RAM64/disk48/tones96 bounds. MetaDisposable replaced/cleared; secondary disposable cleared and layer flushed when inactive. Observers init-only, removed in deinit. No layout-time image processing found. |
| submodules/AvatarNode/Sources/PeerAvatar.swift: representation signal | Resource worker path; asynchronous load, complete-only final representation at360. | Bounded background source subscription. Cold availability/decode time not measured; cannot label cache as culprit. |
| submodules/AccountContext/Sources/UniversalVideoNode.swift: registerSecondaryVideoLayer | Main; weak keyed secondary registry. | Idempotent registration; disposable unregisters on main. Retention/cleanup under actual transitions still needs device evidence. |
| submodules/TelegramUniversalVideoContent/Sources/NativeVideoContent.swift: play/addSecondaryVideoLayer/removeSecondaryVideoLayer | Main forwarding to native player(s). | No independent fullscreen UniversalVideoNode or AVPlayer added. Primary round-avatar playback must be checked separately from secondary detachment. |
| submodules/MediaPlayer/Sources/MediaPlayerNode.swift: secondary output mutations | Main; idempotent layer add/remove, state and V2 callback. | Remove flushes and clears timebase. No demonstrated growing layer set. |
| submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift: play/updateInternalState/updateSecondaryVideoRenderers | Main playback/state and synchronizer mutations; data queue copies samples to ready secondary targets. Existing timer60Hz while playing/seeking,5Hz otherwise. | Extra output processing is source-confirmed. No proven leak/deadlock/heating cause. Existing weak timer/deinit invalidate remain intact. Diagnostics observe play counts, mutations, timing and detached-but-playing state; do not alter playback. |

No custom synchronous avatar disk read/decode/tint processing found in the current hot layout path: prior cleanup already moved preparation off-main. No update → settings-notification feedback loop found: notification posts are tied to actual preference changes. No proven accumulating workers, renderer owners or subscriptions. Cancellation/dispose exists but does not prove an already-running worker finishes immediately.

## Diagnostic-only delta and interpretation

Canonical delta: `patches/jg13-profile-p0-diagnostics.patch` and full-hash manifest. Only four owners instrumented: background helper, screen, avatar transition, V2. Five locked phone-card/gifting owners retain exact hashes. Original functions survive. Native timer/render/playback behavior unchanged.

Log tag: `JerkgramProfilePerf`. Fixed seven-stage count/max-ms/slow counters; one summary on inactive/deinit, not every frame. No new timer, observer, worker or cache. Pinned Telegram Logger.log evaluates its nonescaping autoclosure synchronously; disk logging is queued. Device logger configuration must enable retention/export; this audit does not assume the installed app does so.

- `layout`, `data`, `background`, `transition`, `play`: max main-thread wall time and calls ≥16.7ms. Large layout/data spans include stock work; narrow background/play span is stronger attribution. Overlapping spans are not additive CPU time.
- `sub/dispose/sourceSlot`, `outputSlot`: custom retained source slot and secondary ownership, not total MediaBox subscriptions or native decoders. Inactive should retain neither. Completion is not itself a disposal; counts describe slot ownership.
- `created/destroyed/live`: compare repeated open/close; Settings retaining one controller is normal, not by itself a leak. Deinit summary precedes probe destruction; next summary sees its destroyed increment.
- `readyWallMs`: first-ready latency includes fetch/decode/queue/main delivery, NOT isolated decode CPU time. `ram` helps distinguish warm hits.
- Secondary-mutation `outputs` and helper `output` identity connect the background to native player's `primary`. Mutation timing includes synchronizer work. Helper detach timing alone excludes queued native removal.
- `detached-playing` after60 existing timer ticks means native player is playing with zero secondary targets; correlate with inactive scene and primary-avatar visibility before calling it offscreen leak. Main stalls make60 ticks longer than one wall-clock second.

Device cases: Settings open/close10 times then Chat List; foreign A/B/C open/close; cold/warm static and animated, no avatar; background toggle off; application inactive. Compare owner identities/counts and max spans around stalls. CPU/GPU/decoder utilization still requires runtime profiling; these counters alone cannot establish GPU cost or an eliminated regression.

## Preflight / next gate

Target apply/verify enforces four exact before/after hashes, function-name survival and five regression-lock hashes; retained cleanup tests check persistent stack, worker/cache, lifecycle, phone-card and normal Gifts. A separate contract checks installer order and bounded owner set.
No functional performance fix is claimed. Stop at device diagnostics/build authorization rather than speculative play/lifecycle changes. No Swift/UIKit compilation is available in this environment; Python/structural tests are not a substitute.

Executed preflight: Python compilation of six touched scripts/tests; fresh target-only patch replay; 6 cleanup +5 P0 +4 focused follow-up tests PASS; repeated apply rejected by exact parent hash; four final owner hashes/function-survival and five lock hashes PASS; materialized/source diff whitespace checks PASS. Focused read-only review found no important issue. Full upstream materialization, whole-project verifier suite, Swift component tests requiring xcrun, Bazel/IPA and device profiling were NOT run.

## Superseding diagnostic capture (user approval, Build145)

User subsequently approved visible About Start/Stop/Share/Copy and full CI build. Canonical P0 delta now has six owners: original four plus Settings controller and public TelegramCore diagnostic capture. Existing imports/BUILD glob suffice; no dependency or UI architecture rewrite.
Ring512, timing groups32, utility sampling1Hz, one pending main-queue pulse, generation-guarded restart, ten-minute utility-side cutoff even if UI hangs, background notification stop. Collects process CPU (100%=one core), peak RSS bytes (not current memory), thermal state, main-queue wait, source-ready wall latency, cache/tint/gradient/wallpaper operation timing tagged main/worker, profile lifecycle/secondary mutation summaries. No file/network writes, account/message/phone values or GPU-utilization claim. Report stays in RAM until new recording/process exit, visible in About and via standard Share/clipboard.
About does not start capture automatically and UI subscribes only to session start/stop, not every frame/sample. Added observer disposes with About signal; session observer removed on stop; sampler cancels. Probe logging remains bounded. Share has iPad popover anchor. Runtime UI export still requires device validation.
Preflight: fresh guarded apply and 6 cleanup +5 P0 +3 capture source tests PASS; py_compile PASS; five lock hashes unchanged. Independent review rechecked cutoff fix and found no important issue. Whole Python suite result and named failures/errors are in `jg13-performance-suite-results.md`; it is NOT GREEN. CI/device results must be recorded separately.

CI 37944805574 / remote499a82d: FAIL before Bazel, extracted avatar-cache test missing actual capture owner dependency after timing instrumentation. Full job113868207714 log read; all materialization/source checks before component fixture passed. Fix: prepend real Foundation/Darwin capture owner to cache fixture, without stubbing/removing diagnostics or weakening cache assertions. Build145 has no IPA from this run; retries retain145.


## Build145 device evidence and Build146 ownership compatibility

User crash IPS (2026-10-09 19:56:13 +0300) confirms com.jerkgram.ios / 13.0 / 145, main-thread SIGABRT from an uncaught AVFoundation exception in AVSampleBufferVideoRenderer.setControlTimebase. App addresses are unsymbolicated; exact instruction/exception reason is not in the IPS. Removal from UIView/ASDisplayNode hierarchy appears below the timebase setter. User reports 2/3 self-profile openings crashed before activating capture.

203-second capture: main queue wait max896ms; Settings layout max292ms; transition max169ms versus play max2ms; CPU max221.7% (100%=one core); peak RSS1104871424 bytes (not current RSS). No monotonic custom profile owner accumulation shown: Settings owner reused, six peer owners deinitialized. These measurements do not prove GPU utilization, cache causality or complete absence of leaks.

SOURCE CONFIRMED ownership defect: MediaPlayerNode.removeSecondaryVideoLayer wrote controlTimebase=nil before notifying V2 to remove the renderer; V2 had attached the same output to AVSampleBufferRenderSynchronizer. The update path also queued direct secondary timebase writes. AVFoundation removal is asynchronous (Apple removeRenderer(_:at:completionHandler:) documentation).

Build146 canonical delta explicitly marks V2 outputs as synchronizer-owned before signals/attachment; manual secondary timebase writes are retained only for the legacy backend. Primary Telegram timebase code, play/pause/seek policy, animation and blur quality are unchanged. No new video/render owner. Exact whole-file hash gates now cover seven owners; five regression locks remain unchanged.

Additional bounded preferences/alpha spans split the unaccounted avatar transition cost. They are diagnostic evidence collection, not a speculative performance fix. Original capture ring/timing bounds remain512/32.

Target: Build146, product1.1.0Beta1, bundle13.0/com.jerkgram.ios; upstream f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838 unchanged. PATCHED, NOT COMPILED at local preflight. Device crash/performance outcome UNKNOWN until runtime retest.

## Post-Build146 preference hot-path delta (2026-10-09)

User reports no profile crash in this retest, but repeated Settings entry still freezes before settling. The 385-second report has Settings preferences10087 calls/max361ms/slow436 and transition10224/max361ms/slow437; play max2ms and alpha below1ms. Layout max510ms and background max186ms remain broader unexplained spans. Ring512 dropped349 events; retained CPU/RSS/main-wait timeline does not include every initial peak. No custom owner accumulation is demonstrated. These are device observations, not a claim of complete crash elimination or fixed performance.

Bounded source finding: updateTransitionFraction repeatedly invoked loadEnabled(), reading profile defaults on the transition path. New canonical `materialize_jg13_profile_preferences.py`/`jg13-profile-preferences.sha256.json` stage follows P0 and changes exactly three owners: Display preference snapshot, avatar transition read, Settings state publication. Warm reads use the existing NSLock and two in-memory booleans; master glass AND animated background semantics and all play/pause branches are retained. Initial lazy values still read defaults once; this is not a claim of zero startup I/O. Only the two changed preference keys project synchronously before controller snapshot publication; other keys retain deferred persistence. Existing frozen account/import hooks reload both projected values. Generation reserved at refresh entry rejects older refreshes after newer setters or account/import refreshes. No new observer, queue, timer, player or automatic capture/upload.

Fresh bounded replay: 18 existing +8 new structural contracts PASS; exact parent/final hashes, function survival and five regression locks PASS; repeated apply refused before writes; materialized diff-check PASS. Independent review caught stale refresh races; revised structural checks failed before the correction and pass afterward. Final re-review found no critical/important issue. Native component test extracts actual snapshot owner with only a counted UserDefaults boundary and exercises warm read count, toggles, master gate, account/import-style reloads, setter-during-refresh and deterministic overlapping refreshes (older finishes first). No local Swift toolchain: component execution, full source/native build and device performance are NOT VERIFIED. Full Python discovery remains NOT GREEN; see the suite report. No IPA or new CI run is produced by this source checkpoint.
