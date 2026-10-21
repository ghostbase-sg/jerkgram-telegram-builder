# Build166 — sponsored suppression and profile screenshots

Official source of truth: TelegramMessenger/Telegram-iOS
`f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838` (13.0).
Product parent: Build165 `4ebb1bd8873d3cf07082034a28cd977e15fef91e`,
GitHub IPA build39570812722 succeeded. App Icons Build164 has user-reported device
acceptance. Download Boost is preserved, without claiming new device evidence.
Version remains1.2.0 Beta1 / telemetry `1.2.0-beta.1`; only build becomes166.

## Historical No Ads evidence

The12 September2026 source-based Build140 series survives on
`dev/build133-runtime-repair`, `dev/build141-jank-probe` and subsequent historical
12.9.4 experiment branches. It is not an ancestor of the current13.0 product branch.
Commits: `c9b9c8e` patcher, `f730ae2` verifier, `eaa5581` synthetic tests,
`01f8226` build-chain hook, `f0085fa` corrected actual12.9.2 chat owner.
Files: `scripts/apply_jerkgram_build140_no_ads1.py`, corresponding verifier/tests,
`scripts/install_jerkgram_v12w_build133_probe_hook.py`.

Old runtime-source owners were ChatHistoryListNode.swift and
GalleryUI/Items/UniversalVideoGalleryItem.swift. The former replaced the complete
ad UI signal with an empty signal; it did not remove construction of the chat ad
context or prove absence of requests. The latter removed creation/subscription of
the video ad context and cleared scheduling. Tracking APIs were not patched.
The initial owner shape was wrong and was repaired in `f0085fa`; synthetic tests
initially failed to catch that real source mismatch. Verified evidence is source,
Python fixtures and intended hook ordering. No historical Swift compile, on-device
ad suppression, request trace or impression trace is established by that evidence.

Build166 does not transplant the historical UI filtering patch.

## Current13.0 producers and surfaces

All paths below are under `submodules/`.

| Surface / responsibility | Exact owner | Build166 behavior |
|---|---|---|
| Messages API, local ad cache, conversion | TelegramCore/Sources/TelegramEngine/Messages/AdMessages.swift | Filter only CachedMessage.MessageType.sponsored before toMessage constructs a Message |
| Classification | TelegramCore/Sources/ApiUtils/AdMessageAttribute.swift | Unchanged: sponsored and recommended are distinct |
| Chat context construction | TelegramUI/Sources/ChatControllerNode.swift | Unchanged; not restricted to channel namespace |
| Fixed and inter-post history entries | TelegramUI/Sources/ChatHistoryListNode.swift and ChatHistoryEntriesForView.swift | Unchanged; consume already-suppressed context state |
| Bot header panel | TelegramUI/Sources/ChatControllerContentData.swift; ChatControllerNode.swift | Same central context, so sponsored header is absent |
| Video timed ads | GalleryUI/Sources/Items/UniversalVideoGalleryItem.swift | Same context with messageId; schedule receives no hidden sponsored messages |
| Ad media opened fullscreen | GalleryUI/Sources/Items/ChatImageGalleryItem.swift and UniversalVideoGalleryItem.swift; ChatItemGalleryFooterContentNode.swift | Render only existing visible ad messages; not additional producers |
| Sponsored search peers | TelegramCore/Sources/TelegramEngine/Peers/AdPeers.swift | Enabled setting returns single empty result before request |
| Search rows and visibility | ChatListUI/Sources/ChatListSearchListPaneNode.swift | Unchanged; ordinary search still executes normally |
| View / click | AdMessages.swift; ChatHistoryListNode.swift; gallery/search owners above | Unchanged, driven by actual visible entities |
| Report | TelegramCore/Sources/TelegramEngine/Messages/ReportAds.swift; TelegramUI/Sources/ChatInterfaceStateContextMenus.swift | Unchanged |
| Server hide / channel restriction | TelegramCore/Sources/TelegramEngine/Peers/ChannelAds.swift | Unchanged; no entitlement-controlled call added |

Exactly two real app producers were found: `messages.getSponsoredMessages` and
`contacts.getSponsoredPeers`. No sponsored story producer/consumer was found in
the audited Core/Stories components or generated story API types at this pin.
This is a statement about the pinned implementation, not unknown future types.

One deliberate exception: experimental `immediateExperimentalUISettings.fakeAds`
in ChatHistoryListNode synthesizes ten developer test messages outside the real
server pipeline. It remains unchanged, and is not a real delivered advertisement.
Do not enable that developer fixture to judge real No Ads behavior.

## Lifecycle and Premium boundary

ChatControllerNode constructs AdMessagesHistoryContext for the eligible peer;
activation remains owned by the existing chat lifecycle. Initial cached ads are
read from the account Postbox item-cache collection `cachedAdMessageStates` by peer,
with a five-minute validity check. They are separate from normal stored history.
Activation resolves InputPeer and requests getSponsoredMessages. The optional
request bit0 means messageId is present (video/gallery), not Premium suppression.
Response bit5 maps to recommended; bit12 maps to canReport. Photo/content media,
entities, URLs, sponsor metadata, duration and delay fields are parsed normally.
Raw cache contents and its write/remove behavior remain unchanged.

Both cached and fresh results call the same toMessage mapper. Build166's guard
returns nil for sponsored when enabled, before author/message/media construction.
The existing compactMap removes only those nil results. Recommended entries retain
their native IDs, data and rendering. Context State continues to emit/completely
resolve, including an empty list when no displayable entries remain. History UI
receives the stock tuple and creates no suppressed row, spacer or panel. Normal
history IDs, indices, unread state, pagination and jump code are byte-identical.

Gallery contexts use the same mapper with server start/between delays and message
duration. Empty state clears the existing schedule normally. A bot header consumes
the same context's first message. No separate hide/render-node patch is necessary.

Search producer early-returns before getSponsoredPeers, while normal global search
and non-ad recommendations keep their original paths. There is no broad URL/network
filter or ordinary-message scan.

The audited chat, gallery and search producers do not have a client Premium fetch
gate. Client Premium checks control close/remove versus upsell UI. ChannelAds.swift
sends account.toggleSponsoredMessages / channels.restrictSponsoredMessages and
mirrors server-confirmed flags; channel restriction has its own boost-level gating.
Those requests/flags are untouched. Server eligibility and exact Premium response
policy cannot be proven from client code alone; no claim is made that every Premium
request always returns empty. Build166 never changes account Premium, authentication,
request entitlement or API flags.

## Suppression choice and tracking

Skipping getSponsoredMessages entirely would also remove the response's explicit
recommended type. Therefore conversion is the earliest safe shared suppression
point preserving the requested distinction. Metadata requests and existing raw-cache
reads remain; hidden messages do not become visible media/download nodes.

View requests remain `messages.viewSponsoredMessage`; click requests remain
`messages.clickSponsoredMessage`, with media bit0 and fullscreen bit1. Reporting,
normal URL handlers and ordinary message views are unchanged. A suppressed entity
never reaches the owners that trigger those ad impressions/clicks. Displayed
recommended entities retain their stock interactions/tracking. No fake view, click
or hide request is generated. No extra timer, poll or observer was added; current
activation/disposal/cache-refresh lifecycle remains unchanged.

Ordinary promotional text manually sent by a bot/channel is a normal message and
is deliberately not classified by words or URLs. Suggested Posts, Paid Messages,
service/system messages, pinned messages, channel recommendations, Premium upsell,
Business UI and Boost UI are not removed by this capability.

## Settings and performance

Jerkgram → General / Основные функции → Remove Sponsored Messages / Убирать рекламу.
Default Off, per account, using existing changed-settings persistence and synchronous
runtime projection. New canonical scoped key:
`jerkgram.account.<peerId>.setting.jerkgram.SponsoredContent.Remove`.
No global-value migration: a missing account key means Off even when another
account's global active projection is true. RU/EN labels/footer use JerkgramStrings.
Footer explains Premium status and reopening chat/media or refreshing search.

The policy uses an NSLock-protected32-account cache. A cold context/query reads only
one scoped Boolean; UI changes update the cache. Existing contexts snapshot the value
at initialization. Changes apply on reopen/new context and new search query/refresh;
there is no live reconstruction of a displayed history or active ad schedule.
No defaults/file/JSON work is added per ordinary message or scroll/render item.

## Separate profile capture fix

Two owners in TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources:
PeerInfoScreen.swift and PeerInfoAvatarTransformContainerNode.swift.
The former wraps only setLayerDisableScreenshots' existing native predicate;
the latter applies the same decision to NativeVideoContent.captureProtected.
The native peerInfoIsCopyProtected helper is unchanged because it also governs
forward/copy and forum shared-media semantics.

The existing chat capture contract is reused: AllowScreenshots AND
AllowScreenRecording must both allow capture (existing default true). Either Off,
including master bypass Off, restores native protection. No independent preference
or profile observer was introduced. The shared hot-settings snapshot is reused.

Embedded video content is recreated when effective capture protection changes.
When a copy-protected peer is capture-enabled, its profile video uses the existing
profileVideo second identity field `jerkgram-capture-allowed`; stock protected/off
and all ordinary unprotected identities remain nil. This avoids reusing an immutable
protected renderer retained by another subscriber in UniversalVideoContentManager's
ID-keyed holders. It does not change resource/file IDs or transfer/storage.
Fullscreen avatar-gallery owners and shared-media panes are unchanged. Reopen a
profile after changing the capture settings; no immediate live refresh is promised.

## Production files and chain

No Ads changes exactly five runtime source files:

1. TelegramCore/Sources/TelegramEngine/Messages/AdMessages.swift.
2. TelegramCore/Sources/TelegramEngine/Peers/AdPeers.swift.
3. New TelegramCore/Sources/Utils/JerkgramSponsoredContentPolicy.swift.
4. SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift.
5. TelegramPresentationData/Sources/JerkgramStrings.swift.

Profile capture changes only the two profile files named above. Existing Core/UI
source globs include all files; no Bazel target/framework is added.

Canonical chain: current materialization → release UI → App Icons → Download Boost →
sponsored stage → profile capture stage → identity → root verification → native tests
→ Bazel/IPA. New scripts/payload/manifests/tests are scoped to these two deltas.
Download Boost's runtime code, payload and manifest are unchanged; its verifier now
peels the exact sponsored Settings/Strings descendant to recover original bytes.
Release UI verification similarly passes reviewed final profile hashes through the
existing descendant-verification contract. Root independently requires both stages.

## Verification evidence

Local: py_compile, exact source root verifier, new4 tests, App Icons2, Download Boost2,
release UI2 pass. New stages validate complete before/after SHA256s, exact anchor
counts, upstream pin, canonical single call/order, reverse restoration, unrelated
locks, repeat rejection, every owner/lock tamper and sponsored atomic parent failure.
No marker-only success condition. Sponsored locks25 unrelated owners; capture locks6.
No Ads/profile sources were also reviewed independently. No blocker remains.

Native runner executes the actual policy, actual mapper guard, per-account cold/
cached/persisted/default/eviction behavior, immutable context snapshot, actual profile
helper over18 native×paired-toggle combinations, actual node-recreation condition and
actual capture identity suffix. It does not emulate the full network/UI/renderer.
Local clean end-to-end materialization/configuration was also repeated in a separate
checkout and passed. The macOS gate independently rematerializes clean pinned source, runs all canonical
source/regression checks, parses the five changed existing Swift owners and runs
No Ads/profile, App Icons and Download Boost native fixtures before full Bazel.
The normal Build166 workflow calls that reusable macOS preflight as a required job:
`build-probe.needs = source-preflight`. Even while runners are queued, no Bazel/IPA
job can start unless the native/source preflight finishes successfully. Final CI
links/results are supplied in the delivery response; queued is not green.

An additional broad standalone discovery run found pre-existing failures on BOTH
unchanged Build165 (99tests) and Build166 (103tests):

- test_jg13_performance_capture: test_bounded_session_and_shutdown,
  test_internal_capture_actions_and_export_remain_available,
  test_timing_and_native_output_routed_into_capture (obsolete diagnostics shapes).
- test_jg13_profile_cleanup: test_scene_lifecycle and
  test_full_hash_gate_rejects_marker_preserving_tamper (requires stage/final-owner env).

The canonical staged invocation separately passes its current diagnostic contracts
and supplies final-owner context. The old standalone failures remain disclosed;
those tests were not silently rewritten as part of No Ads. An additional new isolated About fixture error caused
by reading absent profile files was fixed: the About-only fixture may omit all
profile files; root verification still unconditionally requires the profile stage.
Thus broad standalone discovery is not claimed green.

## Required device matrix and remaining uncertainty

| Case | Procedure / expected observation |
|---|---|
| Off | On non-Premium, find real sponsored channel post, bot header, search row and video overlay where available; stock display, tap/open, scroll and pagination |
| On | Reopen same chat/media, refresh search; sponsored entity absent, no gap; adjacent messages, pagination, unread, jump-to-message remain correct |
| Toggle | Off→On→Off; reopen chat/gallery or issue a new search; existing contexts intentionally retain old snapshot |
| Persistence | Relaunch; On remains hidden, Off restores normal delivery; account B remains defaultOff when only A enabled it |
| Non-ad entities | Ordinary private/group/supergroup/channel posts, service/pinned, comments, paid/suggested/recommended content survive |
| Media | Photos, documents, video overlays and ad links when Off; gallery/playback/streaming normally |
| Capture enabled | Both existing capture overrides On; screenshots in protected channel profile and protected-user profile, including animated avatar |
| Capture disabled | Either override Off or master Off; reopen profile and verify stock capture protection; unprotected/self profiles remain normal |
| Capture transitions | Reopen same avatar after On→Off→On; inspect actual captured image/video, including overlapping profile/gallery navigation |
| Regression | App Icons Build164, Download Boost modes, Settings navigation, uploads, ordinary message links and copy/forward behavior |

Still unverified on device: actual screenshots/SpringBoard privacy compositor,
all live server ad formats/delays, actual impression/request traces, scroll position
under the user's history, memory/performance, account switching and overlapping
video renderer lifecycle. Compilation is not device acceptance. No Translation,
emoji/reactions/effects or additional Local Premium feature is included.
