# Beta 2 recovery: source findings and device checklist

> Latest user steering: retain this recovery as a reviewed local base. Do not publish or launch a separate recovery IPA. Implement Local Premium (TASK A) and Saved Messages Tags (TASK B) as separate descendant commits, then review and build one combined release. This supersedes the earlier recovery-first delivery order below. Native/device gates remain pending.

## Status

Prepared recovery for Build178's repeated launch crash. Actual accepted baseline is builder `33fffd93b5d3cc207a5ce2492b43292fe09ea6b8`, upstream Telegram 13.1.2 at `279f89e4d4f63f17227bf877dc3d8990f22ecd58`. Proposed recovery is Build179, `1.2.0 Beta 2` / `1.2.0-beta.2`. Publication, macOS execution and IPA status must be recorded from actual results; none is implied by this draft.

## Findings and bounded changes

| Priority | Owner / evidence | Defect and impact | Recovery |
| --- | --- | --- | --- |
| P0 | `TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift`, `BotBridgeHistoryProgress`; actual official Postbox Codable adapters | Synthesized `Int` has an unsupported decode contract. Optimized initial writes use Int32; debug writes assert. Failed read leads to a corrupt terminal whose synthesized raw enum requests an unsupported single-value encoder and traps before diagnostics. This explains a source-proven repeat-launch failure path; no device trace was available. | Explicit keyed Int32 wire codec, keyed terminal raw String, checked ranges and centralized bounded corrupt fallback. Preserve schema/key/field names, authorization generation and valid identity. No auth/history deletion or global Postbox changes. |
| P1 | `TelegramCore/Sources/TelegramEngine/Peers/ChatListFiltering.swift` | Hiding Default Folder alone leaves stored-true policy and stale proposals/pruning active. | Compile-time effective capability false at snapshot/readiness/order/proposal/transaction/prune boundaries. Retain preference bytes and native reorder/entitlement/server behavior. |
| P2 | `SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift` | Experimental control still advertised; Media & Stories explanation has its own section rather than its control's section. | Remove Default Folder control/hint; move Download Boost footer from section 1 to section 0, preserving native text layout and other footers. |
| P2 | `TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift` and `PeerInfoScreenItemSectionContainerNode.swift` | Jerkgram main Settings card shares low-alpha glass with all sections. “Gram” location is ambiguous because the app cannot open for a screenshot. | Scope dark alpha 0.44 to Settings' `.ghostbase` section, carry through live theme reconciliation. Neighboring/profile dark alpha 0.26 and light alpha 0.18 remain. This area/value is an executor assumption, not measured contrast approval. |
| P2 | `TelegramPresentationData/Sources/JerkgramStrings.swift`, builder identity/package configuration | Settings and telemetry still identify Beta 1. | Shared constants become Beta 2/build179; keep upstream/bundle version 13.1.2. Propagate only proven identity-dependent manifest hashes; preserve accepted feature patch bytes. |

## Evidence boundaries

The codec regression pins full official Postbox encoder/decoder, PreferencesEntry and MurMurHash32 sources. It prepares separate old/fixed `-O` and `-Onone` executables: real legacy bytes, old failure subprocesses, every terminal, malformed fields and repeated prepare/read/write. The transaction/account shell is not a real database or device account. Portable checks do not establish Swift compilation, UIKit correctness or retained-install recovery.

Local Task1: three portable tests passed, one native test skipped because Swift/macOS tooling is absent. Required-native mode correctly fails when that toolchain is absent. Independent source review approved both compliance and quality.

Local Task2: six portable tests passed, one native test skipped. Four targeted old-source checks failed for the intended prior behavior. Its native policy shell covers disabled/stored-true/stale-proposal/no-write semantics in both optimization modes; it is not binary persistence proof. Independent Task2 review approved compliance and quality without findings. Final integration gates are recorded separately.

Local integration: terminal stage 30, patch SHA256 `8f37710d67cd65ff9a866189a24a25fb4189ab8ed037a877bfdbbd76999a6bdc`. All415 actual owner files pass exact apply, no-op reapply, exact reverse and corrupt-last-parent rejection with no partial writes. Separate179 identity staging copies preserve the frozen178 evidence. Composed portable gates discover177 cases:154 executed passes and23 native skips. Eleven migration-chain tests, seven stage tests, four integration tests and two release-UI checks on their correct historical view pass. The final source verifier passes through recovery→BOT→C→B→A and the preceding stages. These counts include nested gates and are not independent runtime measurements.

The portable composed command uses `JG_BETA2_SOURCE=../jerkgram-next/beta2/recovery/integration/source python3 tests/run_jg131_beta2_recovery.py`, with read-only external upstream Git metadata for historical blob checks. That metadata does not turn the415-file source snapshot into a complete checkout: `--require-full-source` correctly rejects missing tracked input `.bazelrc`, and `--require-native` correctly rejects this Linux environment. Release CI runs both requirements on its clean full official checkout. The app job depends on successful macOS source/native preflight. The bounded source-job timeout is20minutes to include old/fixed real codec compilation in both optimization modes.

Do not use old JSON/Any codec fixtures as proof of Postbox persistence. Historical positive Default Folder tests must run on exact reversed parent views; final recovery tests must run on the disabled final tree. No native gate may silently skip in release CI.

## iPhone acceptance matrix

Target supplied by user: iPhone 14 Pro, iOS 26.7.1. Do not request a crash export or screenshot as a prerequisite to recovery.

| Check | Action | Expected result / evidence still required |
| --- | --- | --- |
| Retained crash-loop install | Install recovery over the existing app without deleting it; launch repeatedly | Opens with existing accounts/history intact. This is the primary recovery acceptance test. |
| Existing bot account | Open retained bot account, navigate Settings, return, relaunch | No repeated launch crash; existing bot/history state remains. No token in reports. |
| Bot login | After retained recovery works, use normal bot account login if needed | No crash on auth completion. Do not delete the existing account just to test. |
| Folder disable | Open with previously enabled Default Folder preference, then both folder reorder surfaces | Native selection/order/limits; no Default Folder switch; retained local preference not applied. |
| Material | Main Settings Jerkgram card and neighboring cards; theme changes and push/back | Only intended dark card stronger. Check light/custom theme, transparency/master flags, Reduce Transparency and Low Power separately. |
| Footer | Media & Stories in RU/EN, normal and large text | Explanation belongs to the control group with no clipped/doubled gap. |
| Identity | Settings/About and existing telemetry version fields | Beta 2 and real recovery build agree. |
| Performance | Cold/repeat Settings, own/other profile, typing, idle heat | Record elapsed times and visible stutters; no claimed improvement without comparable device observations. |

Local Premium Hub and local Saved tags are follow-up TASK A/B with separate commits; this recovery does not claim to include them. Translation behavior is unchanged. Do not infer runtime success from a green source gate or IPA build.
