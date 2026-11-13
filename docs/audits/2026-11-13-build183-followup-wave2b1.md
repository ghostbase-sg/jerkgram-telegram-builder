# Build183 pre-release: runtime feedback and Wave2B.1 follow-up

## Baseline / scope

Verified green product: Build182, Telegram13.2, published84412f4409878a4dccd34f6e84083c873e7457d0,
Actions43475263544; local6491020. Branchperf/build182-wave2b1-ui-jank.
Telegram pin24638bc69bd083981b178dd1e7f921eebbf7fc46, toolchain/signing/bundle unchanged.
Build183 retains `1.2.0 Stable`, artifactSTABLE. Existing stages are immutable;
post182-wave2b1-followup and post182-wave2b1-identity are exact successors.
The user subsequently declined manual recording/tests. This supersedes the
attachment's request for a diagnostic DEV IPA and user capture protocol. No new
recorder/readiness/signpost/frame implementation is included. Delivery has no
requirement for another user diagnostic session.

## Fixes and owners

| Owner / symbols | Observed evidence / patch | Verification limit |
|---|---|---|
| SettingsUI/GhostBaseSettingsController: GhostBaseSettingsEntry.toggle/downloadBoost, equality, item, localPremium entries/state signal | `enabled` previously read global policy only in item construction, outside entry equality. Native diff omitted unchanged children; stale callbacks stayed disabled until reopen. Entry now carries enabled, equality includes it, native item consumes snapshot; only Local Premium subscribes to existing policy notifications. No setting values reset. Native ItemListSwitchItem's disabled overlay is reused. | Actual enum native fixture exercises equality, stable ID and defaults; device appearance not claimed. |
| SettingsUI/JerkgramGramEditorController; TelegramPresentationData/JerkgramStrings | Preview previously always used saved amount, even OFF. OFF now subscribes to native tonContext balance, shows native formatter or loading ellipsis instead of stored zero. OFF root summary says real balance. Switch commits immediately; amount editing retains existing autosave. | Existing wallet/native scalar fallback and account isolation unchanged. Real wallet balance availability depends on native data; never invent a balance. |
| TelegramUI/ChatSearchTitleAccessoryPanelNode: Item/ItemView, updateLocalSavedTags/openLocalTagEditor | Local tags now reuse the actual Telegram tag-shaped ItemView, native counters/background/selection/context menu, and SavedTagNameAlertController. Existing local membership/filter/store identity remains. Icon uses native reaction file where available; plain-text tag fallback reuses existing text component. Native cloud entry retained for genuinely Premium users. | This is native presentation with local persistence, not server tag entitlement unlock or cloud sync. |
| TelegramUI/JerkgramSavedTagsController: native session presentation | Main entry now uses native Telegram ActionSheet and native saved-tag naming alert instead of the separate custom ItemList catalogue. Assignment uses existing selection summary/transaction API; rename/delete available from native chip context menu. Existing store limits and account ownership remain. | Account switch/logout stop dismisses sheet/prompts and cancels work; source checks and independent review cover stale UI paths. |
| TelegramUI/PeerInfoScreen/GhostBaseProfileFullscreenBackground: JerkgramProfilePerformanceProbe.begin/end/summary | Old OFF path still updated per-stage dictionaries, read clocks, formatted timing strings and called Logger. Add a capture gate at begin and summary; end ignores inactive sentinel0. Native rendering/playback/layout bodies unchanged. | One narrow source-proven overhead fix, not proof this caused all observed jank. Native fixture compares real old/new probe bodies: 1000 OFF spans have zero timing/report/logger calls after patch; ON behavior retained. One existing capture-state lock read still remains per begin. Cheap lifetime counters remain. |

Six source owners total, plus identity delta in the already-owned strings file.
No Telegram sync, messages/replies, server Premium flag, graphics quality or FPS
policy changes. All functional tests and performance changes remain in one IPA.

## Earlier device evidence used

Saved project reports refer to already supplied captures:
- Build151 текст(7).txt: settings.headerPhonePreference1516 calls/max210ms,
  thermal2; preference cache fix entered Build152 and remains in baseline.
- Build154: main-queue wait958ms, history synchronous281ms, chat layout162ms;
  no complete main cause established. History changes occurred afterward.
- Build155/156 evidence describes row rebuilds up to102ms and long main waits.
These are historical results, not fresh Build182/183 traces. Raw original captures
were not found in the audit workspace; secondary reports are explicitly identified
as such. No request to re-record them. Do not transfer old timings to new owners or
claim previous fixes prove current responsiveness.

## Automatic checks

Focused regressions fail against exact Build182 sources and pass against candidate
sources. Mandatory macOS test compiles the actual Settings enum (including every
equality arm/default associated value) and real old/new profile probe bodies with
explicit Foundation/Logger/capture facades. Facades prove call/branch behavior, not
UIKit FPS or device thermal performance. Current baseline bot/Premium/GRAM and
exact-stage apply/reapply/reverse/corruption gates remain in one combined runner.
Linux local checks cannot substitute for Swift/UIKit compilation. Independent
review checked API signatures/module imports, then found and prompted fixes for
both stale name-alert/sheet lifetimes during account switching.

One product CI is planned after final source review. Successful compilation is not
runtime success. No additional release, milestone or user capture is planned.

### Final local review

Combined source/component runner completed successfully on the final six-owner
projection; native cases explicitly skipped on Linux. Shell syntax, Python compile,
workflow YAML and whitespace checks passed. A second independent review of the
reduced scope found no blocking issue, confirmed the inactive sentinel is not used
by rendering logic, and qualified the optimization as stage/summary work only.
Mandatory native execution and full app build are pending the one published CI run.
