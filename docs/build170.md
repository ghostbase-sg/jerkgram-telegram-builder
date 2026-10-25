# Build170 — prepared changes

Base: `b988bc6304f1adcc80e737747f44241234502305`, branch `dev/telegram-13.1.1-168`, Telegram 13.1.1.

## Included

- Bio card: mask at actual content bounds, including rounded lower corners; footer stays outside the rounded card. Name/surname fields regain conditional translucency.
- Account-scoped “Полупрозрачность всех настроек” switch, off by default. Shared legacy/component settings hosts and identified bespoke settings controllers reuse a snapshot of the existing blurred settings backdrop. Master glass switch still applies. Theme/appearance updates refresh snapshots; failed capture falls back to opaque surfaces. Other users’ profiles and chats stop inherited settings styling.
- Mutual Contact from Telegram’s mutual-contact flag for another non-bot user.
- Offline approximate registration year/range with an estimate label; valid server registration month/year takes precedence. No external runtime requests. Estimates exist only within observed ID bounds; bots/deleted users are excluded. See data provenance in `files/patches/jg131-registration-data-provenance.md`.
- Account-scoped “Оставлять чаты после исключения” switch, off by default. On a known member→kicked/Removed transition while enabled, keep the original account Postbox dialog in the normal list and preserve locally loaded history and display metadata. Actual excluded membership stays unchanged. A static “Вы были исключены из этого чата” footer replaces the composer; sending/reactions/votes and adding poll options are guarded. Explicit deletion clears the local marker/history before server operations, and rejoin restores normal membership behavior. No separate archive screen or duplicated message event store.
- Four exact source patch stages, hashes, source verification, native fixtures and Build170 workflow integration. Previous source gates run on the exact preceding contract; new gates run after final stages.

## Limits and evidence

All prepared source/materialization checks pass locally. Native Swift fixtures are skipped locally because no Swift compiler is installed. Full iOS type checking, IPA compilation and device validation have NOT run for Build170. UIKit translucency/corner geometry and bespoke/theme-preview coverage require device checks; generic host coverage is not proof that every custom overlay participates.

Native retained chats show already loaded history from Postbox, including existing media records. Missing/inaccessible attachment bytes cannot be recovered after server access is revoked; ordinary Telegram cache behavior still applies. The new switch must be enabled before exclusion. Per-chat capture disable prevents future retention; this switch is independent of sidecar archive duration/media limits. Previously retained chats remain retained until explicit deletion or rejoin. Last known title/avatar/legacy-group count are kept. Successfully loaded recent channel participants are stored in a bounded account-specific snapshot (up to 4096 loaded members), served offline after exclusion, and cleared on explicit deletion/rejoin. This is not a complete or current server roster; group membership/metadata/history already absent locally cannot be reconstructed.

The user corrected the excluded-history design: a separate side archive did not meet the requirement. It was replaced with native dialog retention. The earlier sidecar message capture, event kinds and archive screen were removed. Independent review found no concrete Important/Critical defect in the initial native revision; the participant snapshot addition also received focused review with no concrete Important/Critical defect reported. Native peer merges, restart/rejoin, roster rendering, interactions and footer behavior remain unproven until compiled/device-tested. The stale-settings-backdrop review defect was also corrected.

This document records local preparation evidence. Publication, CI and device results must be reported separately.

## Device checks after a successful build

1. Profile > Edit: inspect bio’s two lower corners and the footer below; edit/save a multiline bio. Verify name/surname translucency with glass on and stock backgrounds with glass off.
2. Enable settings translucency in Jerkgram Appearance. Visit settings and subsections: notifications/exceptions, privacy, language, appearance/themes, wallpaper grids, data/backup. Toggle it off, then on. Change light/dark theme and avatar/backdrop, return to an already opened section, and verify the background updates. Switch accounts and check isolation. Check text readability, scroll and rotation.
3. Profile color and Chat Automation cards should retain their correct backgrounds. Recheck Stars/TON/gifts and chat scrolling from Build169.
4. Check mutual/non-mutual/self/bot profiles. Check registration label is explicitly approximate and absent outside the estimator’s supported range.
5. Enable “Оставлять чаты после исключения” in Jerkgram Data and Backup BEFORE testing in a disposable basic group and supergroup. Load history, media and participants, then have an administrator remove this account while the chat is open and while it is closed. Verify that the same chat remains in the normal list after restart, title/avatar/known members/history render, and the exclusion footer replaces the composer. Try sending/reply/edit, reactions and poll voting/add-option. Check account isolation, voluntary leave, disabled toggle, explicit deletion followed by refresh/restart (must not resurrect), rejoin and a subsequent kick. Verify cached-only participant/media limitations are understandable.
