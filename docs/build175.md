# Build175 — follow-up to device feedback

Base: successful Build174 22370d2c0747fa3055b1d5a9f2e28f84b4ff5c75 on Official Telegram13.1.1. Product1.2.0Beta1 build175.

## Translation downloads
The Apple queue distinguishes explicit manual translation from automatic history requests. Download intent is part of pending/active deduplication: background work cannot inherit manual consent. Before invoking translation the bridge checks LanguageAvailability and rechecks that the active job still has subscribers after that await. Automatic requests need installed models; missing models produce the existing unavailable outcome with original content preserved. On iOS26+ background translation uses installedSource sessions which cannot request downloads, including models disappearing after the check. On iOS18–25 the existing SwiftUI session is gated by an installation precheck; a model uninstall race remains a platform limit. Only the explicitly opened manual translate screen opts into the system model prompt. No external text service or fallback added. Physical Apple cancellation is still not assumed.

## Bot account UI
Main native Settings now omits Ghost Mode and Recent Calls for bot accounts; bot root Calls tabs are omitted both initially and on tab updates. Persisted login identity is honored even when local own-peer bot metadata is partial. User account preferences remain. Header phone/username text joins only nonempty parts, preventing the orphan separator. Account switcher badge is БОТ for Russian packs and BOT for English/fallback. Message history, deleted/edited retention and forwarding code are unchanged.

## Settings and modal surfaces
Appearance custom rows and icon grid consume the already resolved surface theme, while preview chat wallpaper/bubble theme remains native. Preview corner masks use the surface theme. Disabled switch overlay multiplies its existing alpha instead of overwriting it. Stars Earn Stars adaptor receives the resolved theme and drops the duplicate outer fill. Emoji-status popup declines full-window settings backdrop inheritance.

Devices detail inherited a transparent modal fill plus a backdrop covering the full controller including the outer dim region; the native sheet lost its visual boundary. RecentSessionScreen now declines that inheritance and preserves its original native modal fill, rounded boundary, dimming and gestures. Its body uses the original native solid fill, not the avatar inside the sheet; other settings remain under the existing master toggle. No fabricated outlines or generic sheet geometry changes.

## Performance evidence
One immutable blocked-message policy snapshot is taken per history mapping rather than repeated synchronized settings/set reads per eligible message. Existing account scoping and presentation invalidation remain. No persistent snapshot cache, timer or retained chat added.

Primary Swiftgram source/release research is recorded in the local performance-175.md report. Pinned rules_swift already enables whole-module optimization in opt builds; adding the same explicit flag would be redundant. Swiftgram wrapper Osize differs from our O, but size optimization is not proof of lower latency. Build175 makes no speculative optimization flag changes. After successful compilation a nonblocking retained-action query prints only effective Swift optimization tokens, never complete compiler command lines. The raw temporary query is deleted. General progressive lag and Swiftgram parity remain unproven; reduced synchronization is a source-level work reduction, not measured device latency.

## Validation
Local exact-owner source/stage materialization and regression suites pass. New tests exercise download-intent/cancellation production queue on macOS, bot production policy helpers and blocked-message immutable snapshot; UI surface tests pin native owner integration and do not render UIKit. Linux has no Swift/iOS compiler; macOS fixtures, full IPA compilation and device behavior are separate gates. User feedback requires on-device retesting of long typing after transitions, visual sheet boundaries, bot account switching and missing/installed language models. Existing icons/NoAds/DownloadBoost and all preceding six stages remain preserved.

Primary platform references: [Apple language availability](https://developer.apple.com/documentation/translation/languageavailability/status), [non-download session](https://developer.apple.com/documentation/translation/translationsession/init(installedsource:target:)), [Swiftgram source](https://github.com/Swiftgram/Telegram-iOS/tree/e3a392272b182dbf975d4ac5fc33b40a5954d749).
