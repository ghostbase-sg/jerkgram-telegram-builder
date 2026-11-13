# Build181 candidate — history, Wallet, local native appearance

## Baseline and scope

- GREEN Build180: published `fbefb07215542ab2d453a62d03d30336a67b1668`, successful Actions43258189305, reconfirmed November13. Telegram13.2 `24638bc69bd083981b178dd1e7f921eebbf7fc46`.
- Candidate branch `dev/beta2-history-appearance-followup`; visible release restored to **1.2.0 Beta 2**, build181.
- Existing32baseline +4accepted successors remain byte-identical. Wave2A.1 stays integrated. Wave2A.2 remains an independent requested checkpoint.

## Changes and concrete owners

| Finding | Implementation | Evidence/limits |
|---|---|---|
| History seed was `live.pts - unread`, zero unread terminated `.noCandidate`; old terminal records prevented deeper work. | `TelegramCore/State/JerkgramBotReplayPolicy.swift`: v2 isolated earliest non-empty cursor (pts1/date1), one-time upgrade from v1; retain server continuation cursor across bounded32-page/120-second windows. | Actual policy/controller fixtures cover zero unread,24,600 returned messages across2windows,32k policy bound, migration and logout. Native execution pending macOS. Never writes the live authorization cursor. |
| History network requests occupied `AccountStateManager` custom-operation slot until reply/timeout. | `State/JerkgramBotBridgeHistory.swift` and `State/AccountStateManager.swift`: retain request lease, timeout, authorization/generation fences and serialized Postbox commits; request lifetime independent of live operation queue. | Native fixture asserts live operation completion while history RPC remains pending. Not an iPhone timing measurement. |
| Wallet benefits/legal panel opaque black. | `WalletScreen.swift`: existing scoped panel `0x1c1c1e`, alpha0.45; text/layout retained. | Visual contrast still requires user device review over actual wallpaper. |
| Local status/colors require strictly account-local storage and rendering. | `JerkgramLocalAppearanceSettings/Store.swift`: account Postbox key`0x4A470004`, stable recordID/own peer/environment, active context generation, real botInfo guards, keyed Int32/Int64/Bool codec. | Caught and corrected unpublished collision with Saved Tags key`0x4A470003`. No global Premium flag or server setters. |
| Native controls and previews should remain native. | Existing `PeerNameColorScreen/UserApperanceScreen.swift` gains explicit local mode; existing EmojiStatusSelectionController, palettes, pattern renderer, settings renderer. Small native pushed entry controller only coordinates local switches/duration. | Entry icon uses upstream `PresentationResourcesSettings.yourColor` (native Brush settings icon/renderer); no new icon renderer or asset. Default native mode retains existing Premium/API behavior. Local mode returns before network setters; native picker tap and long-press preview route through the local callback (including expiry). Native picker data/search remove only local selection locks through its explicit local mode; ordinary callers default to false. Gifts/purchases excluded. |
| Own appearance needs presentation-only propagation. | AccountContext, PeerInfoData/Screen, ChatListController, ChatTitleView, ChatMessageItemImpl/ReplyInfoNode, ChatHistoryListNode. | Own-ID plus active record guards; cached peer pair; no Postbox peer mutations, no per-frame store I/O, history rebuild only on render token changes. |

## Builder and regression gates

New exact successors `post180-history-wallet` (5owners) and `post180-local-appearance` (17owners). Parent hashes, complete overlay hashes, deterministic apply/reapply, reverse to GREEN and corruption refusal are mandatory. Applying an existing exact prefix completes the remaining stages; all missing stages preflight on private owner copies before real writes.

Local source projection verifies the accepted source boundary and both new overlays; it is **not a genuine full checkout**. Linux has no Swift/xcrun: native fixture execution and UIKit module compilation are explicitly pending. CI requires genuine upstream checkout, every historical gate, both optimization modes for actual codec/controller/store fragments, and full app compilation.

Appearance matrix: A enabled/B disabled/C different status/bot excluded; A→B→A and A→bot→A; stale picker generation; foreign peer/record; own server peer refresh; independent expiry; relaunch; logout queued write rejection;10000 repeated projections without boundary reads or peer copies. Facades replace transport/scheduling/Postbox subscription boundaries; actual store, policy and pinned keyed codec compile verbatim. This is component evidence, not device runtime evidence.

## Device acceptance still required

1. Bot account: compare oldest visible chat/message dates and total coverage; receive new messages while replay runs, close/reopen and continue pagination. Do not relog or clear local data solely for this test.
2. Telegram servers control history returned by `updates.getDifference`. The earliest non-empty cursor does not prove all2025history is available. Zero pts/date are excluded to avoid documented PERSISTENT_TIMESTAMP_EMPTY/DATE_EMPTY. `messages.getHistory` is user-only; do not claim a server restriction bypass or cloud recovery guarantee.
3. Wallet legal/benefits readability over light/dark wallpaper; no global theme darkening.
4. Local Premium → Profile Appearance: native emoji/palette/pattern picker, apply, expiry, reset; self Settings/profile, own chat author/reply/header where native UI shows those fields.
5. Account A/B/C/bot switch/relaunch/logout matrix; other users and bots visually unchanged. Appearance remains local, not included in existing backups, no cloud sync.
6. Typing/navigation and sustained use: previous Wave2A.1 remains, but device performance is **NOT VERIFIED**.

Protocol reference: [updates.getDifference](https://core.telegram.org/method/updates.getDifference), errors DATE_EMPTY and PERSISTENT_TIMESTAMP_EMPTY. Server/device acceptance of historical coverage remains pending.
