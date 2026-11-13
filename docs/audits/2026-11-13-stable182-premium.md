# Stable182 unified Local Premium

GREEN181 source-based Telegram13.2 retained. One global master `jerkgram.LocalPremium.Enabled` lives in the existing Settings UserDefaults owner; individual setting scopes unchanged. Lower-level `JerkgramLocalPremiumPolicy` in existing Postbox source is a bounded runtime projection, not a second persistent store. OFF is default; it preserves every saved individual value. No global isPremium change.

## Registry

| Feature | Individual owner / storage | Effective runtime owner |
|---|---|---|
| App Icons | ThemeSettingsAppIconItem / existing global UserDefaults | JerkgramAppIconAccess.isLocked: master AND stored unlock; entitled native account preserved |
| Download Boost | GhostSettings / existing account-scoped UserDefaults, cached mode | JerkgramDownloadBoostSettings.mode; FetchV2 subsequent scheduling recomputes effective parameters, in-flight requests retained |
| No Ads | GhostSettings / existing account-scoped UserDefaults, cached bool | SponsoredContentPolicy; existing AdMessages contexts observe policy, generation-fence old replies and refresh stock/local presentation |
| Translation | GhostSettings / existing account-scoped UserDefaults, bounded policy cache | JerkgramTranslationSettings.enabled; master change invalidates generations/cancels enhanced admissions and notifies UI |
| Emoji Status | existing account Postbox appearance preference0x4A470004, emojiEnabled | active own-peer store + native PeerInfo status picker tap/longpress; local save before server setters |
| Name/Profile/Reply Colors and Background Emoji | same account preference, colorsEnabled group (existing actual feature setting) | native UserAppearanceScreen local mode + own-peer presentation projection |
| Local Saved Tags | existing account Postbox tag store0x4A470003; new individual availability bool in existing scoped Settings namespace | public Postbox presentation/mutation APIs + service + chat UI; metadata/deletion maintenance and durable memberships retained while OFF |

Global master matches existing global App Icons scope and does not merge individual per-account stores. Appearance remains stable recordID + own peerID + environment, active context/generation, real TelegramUser.botInfo. Bot accounts have no enabled appearance controls/overrides. Independent Ghost Mode/Backups/accounts untouched.

## Native UI and state propagation

Ghost Mode source has independent switches rather than an invented dedicated master. Existing Protected Content aggregation/effective checks provide the actual supported pattern: retain individual values, gate runtime and disable subordinate native rows. Shared policy publishes after releasing its lock. One top switch never opens an editor. Individual toggles stay stored/disabled while OFF.

Removed extra Jerkgram Profile Appearance editor/factory/navigation route (former file is now a comment-only stub). Normal Settings/My Profile header status action and native PeerInfo appearance entry are used. The upstream EmojiStatusSelectionController receives explicit local session mode, generation and normal native animations. Tap/longpress expiry consume local sessions even if revoked/stale; they cannot fall through into server API setters. UserAppearanceScreen applies only through account-local store in local mode. Turning master OFF stops effects immediately, and OFF→ON never revives a stale picker callback. Existing Premium purchase-disabled flag cannot suppress explicitly unlocked local picker entry; ordinary native Premium behavior remains.

## Verification

Four local source/actual-fragment assembly checks PASS; required native matrix pending macOS. Actual cached policies, real appearance store/settings codec and native picker completion method compile via the pinned Postbox codec harness at -Onone/-O. Includes master OFF/ON, individual boost/noAds, A/B/bot, stale callback, no peer DB mutation and account-local projection. Exact stage apply/reapply/reverse/refusal verified within combined chain. Full app compile and iPhone acceptance pending.

Device: master OFF restores native capabilities; ON restores saved feature choices. Enable Emoji Status then use normal profile status; enable colors then normal profile appearance. Test A→B→A and A→bot→A, relaunch and expiry. Selected app icon is retained as native installed choice; master controls future Premium icon access rather than destructively resetting the chosen icon.
