# Telegram 13.1.2 migration implementation

Prepared 2026-11-01 from builder17ff4f1. Implementation complete for bounded source review; independent review and real macOS native gate pending. No commit, push, app build, new build number, dependency/toolchain change or BOTBRIDGE change was performed.

## Genuine source evidence

Target is official `279f89e4d4f63f17227bf877dc3d8990f22ecd58`, app13.1.2. All40 changed text files were acquired directly from exact-ref official raw GitHub through the connector and checked against compare.json Git blob SHAs. Additional unchanged parents (including AccountContext old parent separately), ancillary ignore files and existing pristine physical files were checked against the complete old index. No feature output supplied any clean parent.

`candidate/source-provenance.json` identifies every fetched target blob. Complete target tree metadata was derived from the old full index plus41 official compare entries, including tlottie gitlink. Its tree SHA is exactly `eed199f66d25696d0e4d4506469866139eb7828b`. Official commit API metadata was serialized, timezone candidates accepted only on exact SHA equality; the resulting commit object hashes exactly to the official target. `candidate/import-genuine-metadata.py` preserves this check. No invented commit or relabeled old commit is used.

Two fresh local replays use a genuine sparse target projection: real verified target HEAD, complete genuine index/tree metadata, skip-worktree on physically absent files, pristine selected files, initially clean git status. They are explicitly NOT complete deployable checkouts. Missing upstream blobs/dependencies remain missing. Production prepare still fetches/checks out the full exact target and asserts HEAD, app version, unchanged Xcode27.1/Bazel9.2.0, plus target tlottie92df98dc209bc39b1e567ec74a8c86a0af5239de. Existing rlottie override is unchanged.

## Sequential regeneration and scope

`candidate/regenerate.py` replays the original chain using saved original inputs, verifying every old parent/output digest against its original manifest before three-way merging the corresponding feature delta onto the actual target-derived prior stage. It completed twice. Original reconstructed final equals historical TASK C replay across363/363 physical files. Old task-a/b/c, replay-source and upstream-git were never modified.

`candidate/original-digests.json` preserves original inputs. Historical stable patch remains exactly c6449542039d11cd351b0f32454e50013c53b1fcfe45a5130109a892facb30cf. Active stable port delta/effective patch and downstream affected contracts were rebased. Unchanged patch sections retain original bytes. Target pins are coherent across all active upstream-tagged contracts, three terminal materializers, preparation, configuration and active workflow display metadata. External A/B/C generators now use reviewed target boundary directories, verify the chain's actual parent/output digests, and identify old feature commits as historical provenance.

The authoritative exact owner parents/outputs (old and target) and original/new patch digests are in builder `docs/migrations/telegram-13.1.2-stage-chain.json` and candidate/stage-chain.json. Sequence includes identity as a separate boundary:

| Order | Stage | Owners | Regenerated patch SHA256 |
| --- | --- | --- | --- |
| 1 | `jg13-stable.product` | 266 | `925f0ce20910afa9fc6023922ef17ab5cfea78dd7839f3cf9662305399a5747f` |
| 2 | `jg13-beta1-followup` | 4 | `0394a0bd3dcd84ae887d4ee372294e7d0076511880c0c6a684e5a0b615ca5b1a` |
| 3 | `jg13-profile-cleanup` | 7 | `bed41b756e081bab65878f3d0567c72b3ae5b2314b8716f9d780eb9f699e7335` |
| 4 | `jg13-profile-p0-diagnostics` | 8 | `7cbd829d58713f800c4ff98ca9feaf8a011c2e22df0751671390b2e5f9f2c337` |
| 5 | `jg13-profile-preferences` | 4 | `4d9a9efdb184a2c9dc0ee453b948405e70bd799d1058d15bec2f6a98be8d489c` |
| 6 | `jg13-expanded-diagnostics` | 11 | `1e7baba6519194976912ccdb6cd6fe7bdcd103c241913ebd1c9a1beb11e0f0c7` |
| 7 | `jg13-deleted-reply` | 3 | `c1298fe01f2fc0f6d155e0c8990d5d007d4ca206b0704fa9dee1bfdf96a796c1` |
| 8 | `jg13-portable-copy` | 4 | `d903da9003903829358e92079f14b2f7dc81f80bad3835e307a6da33f74c8d0a` |
| 9 | `jg13-release-ui` | 1 | `1696c1ac12d6612554489e65bf740d2999a5ecda0e5dcf46a5abf6791711b5ec` |
| 10 | `jg13-premium-icons` | 3 | `eee479febdace7c0f21a64c66063efa6b987454ffd2a0fe80d07ffc1d5f14ed6` |
| 11 | `jg13-download-boost` | 4 | `d482d34d91266adcc8919565dc68ab1c5895c756c7b3ff03976cc21c69998d22` |
| 12 | `jg13-sponsored` | 5 | `ad42ecad4358a3a3ecdfada3cef30e94dfd8fa0dcef3aa9a6fdac551f93096c0` |
| 13 | `jg13-profile-capture` | 2 | `473ff6eb07bc58c9c30d1f3291057b246d54e308bc6c541b744cadfc77d4391a` |
| 14 | `jg13-stars-gift` | 4 | `bc15d87d5d7d4415c18e873dcab82ca040c3e754a84e01959f9b8c895556edc4` |
| 15 | `jg13-history-backend` | 1 | `27574607ab34b1e086261432da0aabc184aa8e2d734fdec453c1e1f243fda5f1` |
| 16 | `jg131-ui-repair` | 4 | `114de6dc0db4e86985df0a1352c31839e1f744c53cf80c1d9ee5474eb99e38bf` |
| 17 | `jg131-ui-type-compat` | 1 | `2f96e672ba91e48bf6482d23df228899490cb2db25ea957713dbc751a3e95dc8` |
| 18 | `identity` | 2 | `a090900906473df2aa592540f5dcba497d2cec20666844df3d066b5aecf2fcdb` |
| 19 | `jg131-profile-polish` | 4 | `e1bbb676161da6dc16e87e84a8db2695289317e6091b2b3a3648c7b8354fec17` |
| 20 | `jg131-profile-metadata` | 4 | `0dab43126da5fd172fa7e8088c99c46451ab3bc6dbe14bb47dd87636e5f7326b` |
| 21 | `jg131-excluded-history` | 24 | `e16933559d669fc543b486f20423c5d322ca551b3475aebf0fab1fd43199b387` |
| 22 | `jg131-settings-transparency` | 31 | `73d4f1bb16e277b12ae73b5c3dc35344829c035d2c4c780ba1b764f13280e23b` |
| 23 | `jg131-performance-followup` | 6 | `59e3d6133b562fce8ecf26b0e279006b3e37803378db1923d218243ce848f4a8` |
| 24 | `jg131-translation` | 19 | `95a2966d61c2fc614840cec47c6718bc7d8626d0bd6c6a15be4278bd60bcf515` |
| 25 | `jg131-performance-wave1` | 23 | `016c04e3b88232c3da01417b487c45aea12c1ad95928cf9fecde91ef413007d6` |
| 26 | `jg131-translation-repair` | 28 | `5eb14dc44677a9823fac67109d980162df4d8b06627ba0a80f81057d7a784227` |
| 27 | `jg131-default-folder` | 7 | `ffeb31549f183c6987709c03bdd9b3a71751b820f1797e63efba2ffe26b48097` |
| 28 | `jg131-settings-glass-expansion` | 4 | `12360a65c13aa745a0760f312b193b1a3456b966b6d968ab94e273e115c4b628` |

## Explicit media merge decisions

1. Stable ChunkMediaPlayerV2: retain the upstream captured seekId and full guarded rotation/rearm block, adding the existing secondaryVideoTargets argument to the fill call. Retain JG enqueueSampleBuffer and secondary targets while extending the fill return tuple to include upstream videoRotationAngle. Preserve both reader rotation checks, final nil tuple member and both audio normalization paths.
2. Stable MediaPlayerNode: retain the feature's outer transform calculation required by secondary layers; use upstream's conditional including externalVideoRotationAngle and clear that override before ordinary state updates. Preserve upstream finite-size/angle transform helper and external override in updateLayout. Ordinary state/timebase handling remains; review fix round1 below additionally forwards external rotation to secondary outputs using each layer’s own bounds.
3. Expanded Chunk diagnostics: keep the upstream three-member fill result signature and append the existing diagnostic begin/defer body. Do not restore the old two-member signature.

The three conflict files and explicit chosen resolution files are under candidate/conflicts and candidate/resolutions. All other merges were automatic three-way merges against verified old parents. No added default arguments hide missing forwarding.

Complete viaDeeplink factory protocol/implementation/call/harness changes, ignoresShortSentMessages account/standalone/manager/service propagation, and postbox bot-storage set/clear signatures and successful transaction completion survive. All33 upstream-changed text owners outside the seven feature overlaps are byte-identical to official target, including official Siri/bot-storage tests and untouched media/wallet fixes. `candidate/diff-proof.json` and old-final-to-new-final.patch prove final differences are exactly seven overlapping feature owners plus versions.json and two product identity owners. The seven feature overlap paths are AccountContext, SharedAccountContext, Account, AccountStateManager, TelegramEnginePeers, ChunkMediaPlayerV2 and MediaPlayerNode.

## Verification performed

- New upstream preservation tests: observed RED on old C (4 tests,8 failures), then GREEN on target. They assert explicit protocol/state forwarding, storage completion/quota path, seek guard, both rotation reader checks, tuple shape, both audio normalization sites and rotation transform guards.
- New metadata/entrypoint tests: observed missing tlottie guard RED, added prepare assertion; observed missing build gate RED, wired final source tests after TASK C in both no-ads-native.yml and build_jg13.sh. Final `python -m unittest discover -s tests -p 'test_jg1312*.py'`:8 tests PASS.
- `python candidate/replay.py replay-1` and replay-2: both strict production stable main (exact genuine HEAD/clean status) plus every actual stage apply and root source verifier PASS; identical403 physical file hashes, matching all reviewed boundary outputs. Configuration's noncredential source transformations and identity substitutions executed; credential/configuration-repository creation intentionally not invoked in this bounded source replay.
- `python candidate/prove-stage-reversals.py`:28/28 actual boundary patches dry-run/apply/output digests, exact reverse restoration (including removed new owners), repeat-delta refusal, corrupt-parent apply/check refusal with no other writes PASS. Transform-only stages use their recorded generated delta for this byte proof; actual production transformations also passed in both replays. Existing terminal materializer fixtures cover production idempotence/patch-tamper and mixed-parent rejection.
- `python tests/run_jg131_settings_glass_expansion.py`: chained C9/B13/A24 plus root diagnostics/history/profile/source suites PASS. Five native test skips and three unavailable-xcrun parse groups are explicitly reported on Linux. This is source proof, not native GREEN.
- Existing real final/wave stage fixtures:8/8 PASS at exact declared wave/Build175 source views, using production reverse views. An initial terminal-C invocation of generic stage discovery reported8 errors because those older stage fixtures require their earlier boundaries; rerunning the exact same8 at their declared source boundaries passes. The other15 terminal A/B/C stage fixtures pass in the chained runner. No fixture or guard was weakened.
- `python candidate/prove-diff.py`: two replay maps equal403/403; original final363/363 identical; pure upstream33/33 changed text owners exact; seven feature overlaps plus three version/identity owners only.
- Python compilation for the three updated external generators; shell syntax checks for build/preparation; `git diff --check`:PASS.

No historical whole686-test suite was run. Detailed logs remain under candidate (preservation-red.log, metadata-red.log, gate-integration-red.log, focused-tests-final.log, replay-1.log, replay-2.log, abc-final.log, stage-tests-correct-boundary.log). Supporting JSON/diff evidence is copied into builder docs/migrations/telegram-13.1.2 for review/publication.

## Historical snapshot and unchanged identity

source_snapshot_sha256 is unused by scripts/tests. Git history proves digest6499b01… was introduced with the13.1.1 migration in commit950894f, alongside source_snapshot_format='git archive tar'. Its recorded role is the historical13.1.1 export, not a newly produced13.1.2 archive. Preserve its value and annotate this provenance; the historical archive itself was not reacquired or rehashed, so its original export digest is not independently reverified here. No current archive digest is guessed. Jerkgram1.2.0 Beta1/Build176 remain unchanged; no next number selected and latest successful IPA must be rechecked before a future build.

## Remaining authoritative checks

Independent source/merge review is pending. Real macOS clean full-target checkout plus native source gate is pending. Official Siri/bot-storage tests were preserved but not executed locally. No full app/extensions typecheck/link, dependency fetch, device deep-link/state/storage/media tests, translation quality test or settings navigation runtime matrix is claimed. Native fragments/parse are not whole-app compatibility and compiler success will not prove runtime behavior. These are the concrete remaining verification risks; no known local source failure remains in the bounded gates.


## Independent review repair — round1/5

Review requested one P2 integration repair: upstream Chunk sets externalVideoRotationAngle rather than ordinary player state, so retained JG secondary outputs missed rotation. Verified in source, then fixed in the canonical stable MediaPlayerNode resolution input and regenerated every stage from pristine parents. No other feature owner/API was needed. Changes are confined to MediaPlayerNode.swift plus its focused source contract and derived exact patch/hash evidence.

The node now applies external rotation to each registered secondary layer using that layer.bounds.size. Attachment applies the known angle immediately, including attachment when primary bounds are empty. A bounds-change observation recomputes geometry after the secondary mirror lays out or resizes. updateLayout refreshes secondary outputs before its existing primary-empty-bounds early return. Ordinary state rotation/aspect/timebase/synchronizer paths are unchanged.

Observation lifetime is exactly one token per registered layer: duplicate attachment still returns before allocation; captures of node/layer are weak; removal invalidates/removes the token; helper checks that the layer is still the registered instance before touching it. No asynchronous callback queue is introduced. Transform writes change the affine transform, not bounds, so this observation does not recursively fire from its own update. This adds one event-driven KVO token and one guarded transform recomputation per secondary bounds-change notification, plus registration/external-angle/layout events. No timer, polling, global observer, decoder, source subscription or per-frame work was added. AVFoundation/UIKit notification/layout behavior remains native/device-unverified.

Pre-fix source, source-chain JSON and migration diff are preserved in candidate/fix-round1. Scoped source-fix.patch and fix-proof.json show the exact repair; stage owner records change only for MediaPlayerNode at Stable and P0 boundaries. Source-provenance and old historical feature inputs remain untouched.

Observed RED: new test_external_rotation_tracks_secondary_attachment_and_own_bounds failed because the secondary rotation helper/path was absent (5-test preservation run,1 failure). After repair: preservation5/5 PASS; final focused migration/preservation9/9 PASS. The check covers own bounds/angle, attachment and bounds-event routing, weak captures,1:1 token registration, removal invalidation, registered-instance lifetime guard and rotation before primary-empty-layout return. No native geometry fixture ran because this host has neither Swift nor xcrun; textual/source contracts are not native runtime proof.

Required updated proofs only: both strict production replays PASS and remain403/403 equal; full28-stage dry-run/output/reverse/repeated-delta/corrupt-parent no-write proof PASS; original final363/363 and pure official33/33 unchanged; exact seven feature overlaps plus three version/identity owners remain the final scope. git diff --check PASS. Replay includes required root source checks; unrelated historical suites were not rerun. Updated canonical stage-chain and support evidence replace the previous digest records. No commit/push/app build was performed. Fix frozen for scoped re-review.
