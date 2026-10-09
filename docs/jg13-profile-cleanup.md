# Bounded profile/gifting cleanup

Base builder: `4bc1548dc91306e76b97f694d017eb8af7932ed5`.
Branch: `dev/jg-1.1.0-beta1-upstream13`.
Upstream remains pinned to `f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838`.
Product version/build unchanged: Jerkgram 1.1.0 Beta 1 / Build143.

Canonical chain: immutable Stable delta → existing Beta follow-up →
`patches/jg13-profile-cleanup.patch`. Seven whole-file before/after hashes guard
the new delta. Both materialization and final source verification run its contracts.

## Owner map / evidence

All profile paths below are under
`submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/`.

| Area | Owner / source-confirmed behavior | Minimal delta / risk |
| --- | --- | --- |
| Settings + PeerInfo lifecycle | `PeerInfoScreen.swift`, `GhostBaseProfileFullscreenBackground.swift`: one scene created in node init; only window detach/deinit previously released secondary output; no controller-visible gate | Controller appearance + app-active gate, source/secondary disposal when inactive; medium |
| Cold avatar | Background helper `avatarEntrySignal`; `submodules/AvatarNode/Sources/PeerAvatar.swift` executes image generation inline when synchronousLoad is true, before downstream deliverOn | Deferred subscription on concurrent queue; asynchronous native avatar generation, preserve completeOnly and 360px source; medium |
| Disk avatar | Background helper `apply(.avatar)` synchronously loaded disk image and sampled tint | Disk read/decode/tint in worker signal; medium |
| Warm avatar | Final identity-keyed RAM entry still followed by a new avatar subscription | Return after cached image/tint and animated identity setup; retain bounded existing caches; medium |
| Number confirmation | `PeerInfoSettingsItems.swift` constructs `.phone` Info/Action items; `ListItems/PeerInfoScreenInfoItem.swift` embeds `submodules/ItemListUI/Sources/Items/ItemListInfoItem.swift` opaque background over existing glass section | Opt-in hides only child background; `PeerInfoScreenItemSectionContainerNode.swift` owns existing scene tint/material; native text, layout, actions, separators retained; low/medium |
| Seasonal Gifts | `submodules/TelegramUI/Components/Gifts/GiftOptionsScreen/Sources/GiftOptionsScreen.swift`: synthetic catalogue, DeletedGiftsStickers subscription, seasonal filter/category/ribbon | Remove only local seasonal additions/UI/subscription. Keep server catalogue, transfer/resale, normal/Stars/profile/received/API/storage paths. Retired raw filter -5 routes to all; low/medium |

Existing canonical patches touch the profile helper, parent, section, Settings and
GiftOptions. InfoItem wrapper and ItemListInfoItem were clean pinned upstream files.
No legacy installers were replayed. No new renderer/player/per-row blur.

## Verification and limits

- Target-only original fixtures matched current canonical hashes; unmodified
  upstream owners fetched at the pinned SHA. No full Telegram tree was cloned.
- Red/green structural contracts; whole-file hash tamper rejection; target-only
  canonical replay; Python compilation and bounded diff checks.
- Relevant existing follow-up avatar LRU/dedup and metadata/helper tests retained.
- Final checks: 6/6 new contracts, 4/4 relevant prior tests; seven-owner canonical
  replay passes and duplicate application is rejected by the before-hash gate.
- Materialized Swift diff and staged non-patch files pass whitespace checks.
  The serialized patch retains stock whitespace in context/removal lines;
  treating it as new source text triggers generic Git whitespace warnings.
- Focused review: no established Critical/Important regression; structural tests
  cannot prove queue execution, appearance cancellation/resume, or video reattachment.
- No Swift compiler/SDK/device in this environment. Full-tree preflight not run.
- Application gating is app-wide; individual multiwindow scene activity has not
  been audited. No new scene-specific architecture is introduced here.
- No Bazel/IPA build, new CI run, push, or publication. Push on this branch would
  automatically start a build, which this request explicitly forbids.

Status: **PATCHED, NOT COMPILED / NOT RUNTIME TESTED**.
Source costs are proven; actual causes of observed freezes/heating are not.
Device checks still needed: Settings tab slider, animated avatar, cold/warm profiles,
rapid open/close and interrupted transitions, background/foreground, glass off/on,
phone-card contrast/actions, normal gifting/transfer/resale and absent Seasonal UI.

## Authorized build follow-up

User authorized CI on 2026-10-09 after the source-only cleanup. Build143 run
`37910647947` completed successfully; next build is Build144. Product remains
1.1.0 Beta 1, upstream/bundle version remains 13.0. Configuration, Bazel buildNumber
and workflow artifact names are aligned. Cleanup source commit: `98e2ac1`.
