# TASK B — Local default chat folder

## Intent / baseline

Official Telegram13.1.1 fb0e62ba8a147f0821da6aa63c09da7d79a10111. TASK A committed65a6913995b5a6ee752072fde427dd6ac72c8019, native gate40891009533GREEN24/24; evidence successor0479229c181007ca0c13bf38f9b94543c051397a. User requests native custom-default-folder UX for nonPremium, per account, OFF stock, limits unchanged, separate TASK B commit. No global Premium, no unrelated feature unlocking.

## Approaches / decision

1. Bypass only the native UI checks: insufficient. Order is sent to messages.updateDialogFiltersOrder; official API docs reserve All Chats reorder constructor for Premium. No live nonPremium rejection code is inferred.
2. New Jerkgram picker/startup-only override: duplicates existing native reorder UX and disagrees with visible/swipe/repeated-Chats-tab ordering.
3. Chosen bounded local presentation order, stored in current account Postbox, applied through native reorder and list presentation. Server order remains compatible (All Chats first when represented), custom-folder relative reorder still synchronizes. Actual Premium and OFF retain native code paths. Local choice survives app relaunch and cannot cross account database/logout lifecycle.

## Canonical preference

Jerkgram → Interface: Unlock Default Chat Folder / Разблокировать папку по умолчанию, default OFF for a new opt-in feature. Canonical GhostBaseSettingsState scoped key jerkgram.UnlockDefaultChatFolder; bounded policy cache updated on activation/actual delta, no style/wallpaper invalidation or page projection writes. Footer says use normal folder reorder, choice local to this account/device, limits still apply.

## Native storage and policy

Separate Codable local order preference under PreferencesKeys.jerkgramDefaultFolderOrder (unique reserved key0x4A470001, confirmed absent from pinned/current PreferencesKeyValues). Keep synchronized ChatListFiltersState filters/remoteFilters unchanged in representation. Store bounded≤256 unique IDs including All Chats0; no global folder ID, no AccountManager-wide ID, no persisted UserDefaults selection.

Engine exposes local presentation-filter signal and a scoped order-commit method, shared by native header and folder-settings Done. Real peer Premium and current canonical toggle are checked on the account's native state; do not use a default-false entitlement snapshot to override an unknown real Premium account. Setting changes switch presentation once through a disposed/account-filtered event signal, never polling. A changed preference during pending reorder cannot install stale enhanced state.

For enhanced nonPremium, normalize requested order against current actual folder IDs, retain0, remove duplicates/foreign IDs, append newly added folders in native order. Server-compatible order has0first if the original synchronized state represented0. The local overlay only affects existing visible/allowed folders; preserve max-folder and chats-per-folder gates and native click/context disabling. Unavailable/hidden/count-limited configured default resolves to All Chats; it must not make another folder newly accessible by changing the limit checks.

Prune deleted IDs inside native account filter-update transactions, both interactive overloads and central updateChatListFiltersState (covers incoming server order/deletion/full synchronization). If the saved first custom ID disappears, reset first/default to0, not the next custom; prevent later numeric ID reuse resurrecting a deleted choice. Do not clear from a transient uninitialized/empty projection. Authoritative membership removals prune independently of whether a folder screen is mounted. Local-only preference never participates in outbound API serialization.

## Presentation/startup

Active13.1.1 owner is HorizontalTabsComponent, not legacy ChatListFilterTabContainerNode. Reuse native header reorder and folder settings editor. Both read the same effective local order and commit through the same method; only native editor default-first Premium rejection and two All-first coercions are capability scoped. Do not alter shared isPremium parameters (also govern tags/color/counts).

Read local preference before existing one-shot root initialization. Effective first valid folder drives startup and available/swipe/repeated-Chats-tab order coherently. Keep initializedFilters and preserve user's later selected folder; no foreground/deep-link enforcement. On missing selected local default explicitly choose .all and avoid the native negative predecessor-range edge at index0. OFF branch retains native behavior. Concrete chat/deep-link/notification navigation remains untouched; verify on device.

## Verification / deliverable

### Builder-check resolutions

The core signal must expose a coherent presentation snapshot, not only [ChatListFilter]: local preference loaded/readiness, known actual Premium, applicable native limit, allowed IDs computed BEFORE local permutation, active policy generation and effective/default-missing state. Root and editor consume that snapshot; do not combine projected ordinals from one policy with newly read limits from another. Preserve the locked suffix/hidden exclusion so local reorder cannot move a previously locked folder into an allowed slot.

Capture policy generation at drag/reorder start and reject an obsolete local commit inside its transaction. Completion still leaves native reorder mode and disposes progress if the proposal is rejected. Do not reinterpret an old enhanced drag as a stock RPC after OFF. With OFF or real Premium, use original generic native reorder closures unchanged.

The root initializedFilters one-shot cannot be consumed before the local preference and needed known policy snapshot have loaded. A nil/empty transient view must not destroy saved IDs; use native cached state/readiness, not network polling. Delete cleanup uses old→new authoritative membership, including both interactive overloads and central state writer, independent of toggle/UI lifetime. Enhanced missing selection/default chooses All before the native predecessor-index expression; OFF remains native.

Exact current owners restored before edits, compare clean pinned API signatures and actual TASK A outputs (not pristine over an already patched owner). TDD pure production-order policy fixtures executed on macOS: OFF/ON/Premium, account databases, normalization/dedup, cap256, hidden/limited/missing/deleted/ID reuse, save/server separation, setting race, no-op updates. Source integration checks cover both reorder surfaces and unchanged limit blocks; native fixtures do not claim network/UIKit end-to-end success.

Dependent idempotent TASK B stage after TASK A, exact parent/after hashes and reverse parent view. Run prior gates before applying each new stage, verify A survival on reverse view, keep old patches immutable. Separate TASK B commit before glass work. Source-only macOS preflight may run; one combined IPA after B+glass source gates and actual latest successful build-number check.

Runtime: toggle OFF restriction; ON reorder/default/relaunch/change/delete/All; two accounts/logout-login; limited/hidden folder; external chat deep-link/notification and return; A translation and App Icons/Download Boost/No Ads/Ghost/deletion/edit/transcription/protected-content navigation. Device iPhone14Pro/iOS26.7.1. No app/device success from compile.

## Evidence

task-b/UI-AUDIT.md and STORAGE-AUDIT.md,15pinned blob-verified sources. Official https://core.telegram.org/api/folders inspected2026-10-29. Active native UI gates, synchronized storage, root account reconstruction and direct chat entry owners are identified there.
