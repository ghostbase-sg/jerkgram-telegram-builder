# TASK B — default chat folder

Baseline: TASK A code `65a6913995b5a6ee752072fde427dd6ac72c8019`, evidence
`0479229c181007ca0c13bf38f9b94543c051397a`; Official Telegram 13.1.1
`fb0e62ba8a147f0821da6aa63c09da7d79a10111`.

## Behavior

Jerkgram → Interface → Unlock Default Chat Folder / Разблокировать папку по
умолчанию is an account-scoped opt-in, default OFF. ON permits a nonPremium
account to choose its startup folder through the two existing reorder screens.
The choice is local to this account/device. Actual Premium and OFF use the
existing native save closures. Folder count, chats-per-folder, tags, colors and
sharing entitlements remain native.

The native synchronized order cannot reliably represent this nonPremium
default: the [official API](https://core.telegram.org/api/folders) reserves
moving All Chats for Premium. A separate bounded Postbox preference therefore
stores the presentation order. The synchronized representation keeps All first
when it was already present; local-only All movement does not queue a sync.
No server rejection or successful nonPremium RPC has been observed here.

## Source map

Seven owners are recorded in `patches/jg131-default-folder.sha256.json`:

| Owner | Responsibility |
| --- | --- |
| TelegramCore/ChatListFiltering.swift | Bounded order, policy generation, coherent preferences/peer snapshot, transaction validation, deletion pruning |
| TelegramCore/TelegramEnginePeers.swift | Scoped snapshot and reorder facades |
| TelegramCore/SyncCore_Namespaces.swift | Local preference key 0x4A470001 |
| SettingsUI/GhostBaseSettingsController.swift | Canonical toggle and local-choice explanation |
| ChatListUI/ChatListController.swift | Native header reorder, one-shot startup and unavailable selection fallback |
| ChatListUI/ChatListFilterPresetListController.swift | Native editor reorder and completion cleanup |
| ChatListUI/TabBarChatListFilterController.swift | Effective order and its matching snapshot; original unread calculation retained |

The snapshot computes allowed custom IDs before permutation and keeps locked
folders in their native suffix. Startup waits for the local read and, when
enabled, known actual entitlement. A proposal captures the account database
lifetime and policy generation at reorder entry; obsolete proposals complete
without a stock-save fallback. Authoritative membership removals prune local
IDs inside all three native writers, independently of toggle and UI lifetime.
Removing the configured first ID resets the default to All, preventing later
ID reuse from restoring it. Ordinary navigation is not forced back to default.

## Verification

`python3 tests/run_jg131_default_folder.py` passed on Linux: 13 TASK B tests
(one native Swift fixture skipped), then all 24 TASK A tests (three native
fixtures skipped) and previous source contracts on exact restored parent
views. The stage applied twice to a fresh TASK A replay without further
changes; all seven parents matched that replay. Native Swift parsing is
unavailable on this Linux host. These are source checks, not an app compile.

Independent task review passed at source scope; its report is preserved beside this document. macOS native verification remains pending. No IPA
was built for this task. Device coverage still required: ON/OFF, both reorder
screens, relaunch/offline, deletion/ID reuse, two accounts/logout-login,
hidden/limited folders, notification/deep-link entry and subsequent navigation.
Device target: iPhone 14 Pro, iOS 26.7.1. Translation/backend quality and UIKit
behavior are not established by extracted Foundation fixtures.
