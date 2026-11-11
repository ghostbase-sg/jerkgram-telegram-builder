# Beta 2 combined release — integration record

## Current status

Work in progress. This records the combined release requested by the user, including recovery, Local Premium (TASK A) and local Saved Messages tags (TASK B). It does not announce an available IPA or successful device recovery.

- Product baseline: Telegram 13.1.2, official pin `279f89e4d4f63f17227bf877dc3d8990f22ecd58`.
- Latest published baseline checked during this continuation: builder `33fffd93b5d3cc207a5ce2492b43292fe09ea6b8`, Build178, Actions run `41512083073`, successful compilation. The user reports repeated launch crashes on that app.
- Current local branch: `dev/beta2-local-premium-tags-179`.
- Local recovery prerequisite commit: `ce7fc4cc67a8dc036c51aa33de762e5e29ddabec`.
- Separate TASK A commit: `5d9910a9206ea2977dbc0146946b9a5dc52daf73`.
- TASK B commit, final HEAD, publication and CI: pending. Build179 / `1.2.0 Beta 2` remains selected from the verified Build178 remote baseline; the parent must recheck allocation immediately before publication. The common artifact is `Jerkgram-1.2.0-Build179-BETA2`.

No separate recovery IPA is planned. The common app build follows final source/native preflight. After launch, monitor the initial few minutes only, as requested; the user will report later build failures.

## Recovery included in the local base

See `2026-11-05-beta2-recovery.md` for exact source evidence and limitations. The local base contains the explicit bot-progress Postbox codec, effective Default Folder disable with stored preferences retained, scoped stronger dark material on the main Settings Jerkgram card, Media & Stories footer grouping, and Beta 2 identity. Native/device recovery has not been established by portable tests.

## TASK A: owners and settings semantics

Native owners are `SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift` and `TelegramPresentationData/Sources/JerkgramStrings.swift`. The home row beside Backups pushes `.localPremium` through the existing navigation owner. Its icon is `PresentationResourcesSettings.premium` using the existing Settings renderer and official `Item List/Icons/Premium` resource; no new icon renderer or asset.

| Group / control | Existing authority retained | Default and scope |
| --- | --- | --- |
| Appearance / App Icons | `jerkgram.LocalPremium.AppIcons` | false; device global |
| Media / Download Boost | `jerkgram.DownloadBoost.Mode` | off; account scoped; existing off/medium/maximum values |
| Messages / No Ads | `jerkgram.SponsoredContent.Remove` | false; account scoped |
| Messages / Translation | `jerkgram.EnhancedTranslation` | true; account scoped; existing feature marked as needing work |

Old entry points remain for runtime verification. A read-only appearance refresh reloads canonical state when returning between aliases. There is no migration, independent settings store, `isPremium` switch, extra-account feature or Default Folder advertisement. Translation behavior is unchanged.

TASK A source review: compliance PASS / quality PASS, no findings. Focused portable suite: 17 passes and one native skip. Composed gates: 171 passes and 24 native skips (nested counts, not runtime measurements). Exact stage31 apply/reapply/reverse and six-parent corruption refusal checks passed on the 415-file proof snapshot. Native/full-checkout/app gates remain pending.

## TASK B: storage and server boundary

Telegram's official Saved reaction tags use a Premium domain. The official `messages.updateSavedReactionTag` and `messages.sendReaction` documentation lists `PREMIUM_ACCOUNT_REQUIRED`; the exact server response for an actual non-Premium account has not been probed here. Source evidence and original API links are recorded in the completed Saved Tags audit.

Jerkgram local tags use a separate Postbox index, not official reaction attributes or tag mutation APIs. Ordinary authorized message-by-ID reads may load the content of an already indexed Saved message. That is not tag synchronization.

Accepted storage owners: `Postbox/Sources/LocalSavedTagsTable.swift` and the existing patched `Postbox/Sources/Postbox.swift`. The account-local database isolates records; metadata pins the self peer. Relations use the current Saved message's complete `(peerId, namespace, id)`, with cloud namespace and positive ID validation, never a forwarded source ID.

The binary table has definition, membership, reverse ordered, cloud-ID, time and thread indexes. Revision invalidation uses the existing preferences mechanism in the same transaction. Pages contain at most45 entries; no whole-history scan or 500-result reaction search. Admission bounds are256 definitions,16 tags per message,100000 total edges and1000 selected input IDs; overflow rejects additions without evicting existing tags. Names are trimmed/NFC, at most64 graphemes and256 UTF-8 bytes.

Task2 storage review: compliance PASS / quality PASS, no findings. Seven portable tests pass; one native SQLite test is skipped on Linux. Required-native mode fails closed. The prepared SQLite fixture includes reopen, pagination and100000-edge measurements; it has not been executed on macOS. Large deletion remains one O(n) Postbox transaction with bounded memory: acceptable queue latency is unproven.

The Core facade/lifecycle source gate passed after one scoped concurrency fix. Its owners are `TelegramCore/Sources/TelegramEngine/Messages/LocalSavedTagsService.swift`, `LocalSavedTagsOperations.swift`, `LocalSavedTagsLifecycle.swift`, the existing `DeleteMessages.swift`, and `TelegramCore/Sources/State/AccountStateManagementUtils.swift`. Shared semantic deletion covers direct, replay/global-ID, range/thread/full-history paths before retention branches; edit/refetch updates only actual index metadata changes. Missing content and cache eviction do not remove tags.

The initial review found a check/unlock/publication race in service and provider cancellation. The accepted fix serializes publication and invalidation in one shared Dispatch delivery domain, with inline reentry and callbacks outside state locks. Scoped re-review accepted both findings at source level. Eight focused portable Core tests pass and one native test is skipped; the concurrent next/completion, reentrancy and cancellation fixtures remain unexecuted on macOS.

The native UI source review passed compliance and quality with no findings. A separate native ItemList manager/results screen is discoverable from Saved Messages Search → Local tags, including an empty non-Premium account. Assignment uses the complete current selection or album context, aggregate none/mixed/all state and one typed mutation. Loaded results reuse native ChatListItem rows; unavailable rows retain indexed metadata and exact retry/remove actions. The source contract is one active request, 45 rows per page, three retained windows/135 rows, explicit older/newer cursors, and generation guards on filter/pop/account changes. These are source bounds, not measured runtime behavior.

Stage32 `jg131-saved-tags` is now integrated after stage31 Hub. Its exact 12-owner patch SHA-256 is `e5c307c7717a42977817ef0a666abc938c956efe34011346abb5dfb16fb9cc13`; the manifest and chain carry every before/after hash. The five new owners use absence parents. The existing navigation owner uses its verified official 13.1.2 blob (`69e574487c7e786916ef37bc11d879a811d57f95`) rather than a false new-file parent. Existing Postbox/Core/UI source globs include the new Swift owners; build declaration bytes are unchanged. RU/EN strings stay inside the accepted UI owner.

All paths below are relative to the generated Telegram source:

| Source owner | Change |
| --- | --- |
| `submodules/Postbox/Sources/LocalSavedTagsTable.swift` | New store/index |
| `submodules/Postbox/Sources/Postbox.swift` | Existing transaction facade |
| `submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift` | Existing semantic update hooks |
| `submodules/TelegramCore/Sources/TelegramEngine/Messages/DeleteMessages.swift` | Existing shared deletion hooks |
| `submodules/TelegramCore/Sources/TelegramEngine/Messages/LocalSavedTagsLifecycle.swift` | New lifecycle helpers |
| `submodules/TelegramCore/Sources/TelegramEngine/Messages/LocalSavedTagsOperations.swift` | New typed operations |
| `submodules/TelegramCore/Sources/TelegramEngine/Messages/LocalSavedTagsService.swift` | New service/provider |
| `submodules/TelegramUI/Components/Chat/ChatMessageSelectionInputPanelNode/Sources/ChatMessageSelectionInputPanelNode.swift` | Existing complete-selection action |
| `submodules/TelegramUI/Sources/Chat/ChatControllerNavigationButtonAction.swift` | Existing pinned Saved discovery owner |
| `submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift` | Existing message/album assignment |
| `submodules/TelegramUI/Sources/ChatInterfaceStateInputPanels.swift` | Existing panel callback installation |
| `submodules/TelegramUI/Sources/JerkgramSavedTagsController.swift` | New native management/assignment/results and RU/EN text |

The common source/app entrypoints now materialize BOT → Recovery → Hub → Tags, then run one required Tags composed gate per clean checkout. That gate runs the exact store/Core native fixtures and UI contracts on final Tags source, passes the restored Hub parent to historical body checks, parses all final Swift owners on macOS, and forwards both required flags through exact Hub → Recovery → BOT parent views. Earlier direct BOT/Recovery/Hub native calls were redundant and are removed from those two entrypoints. All their required native coverage remains in the composed chain. Unrelated earlier runner structure is unchanged. The app job still requires successful `source-preflight`.

The workflow trigger now includes `dev/beta2-local-premium-tags-179`; its title, diagnostics and product artifacts describe one combined Beta2 release. Telegram remains pinned to 13.1.2. No old patch or blanket historical manifest regeneration was performed.

Task5 local evidence: exact apply/reapply/reverse against the actual 416-file integration parent (immutable Hub415 plus the existing navigation parent) produces the reviewed 421-file source. All 57 changed/context parent corruptions refuse before any write, including unexpected presence of each new owner; reverse restores all 416 hashes and removes all five new owners. Context guards include the accepted Hub, recovery, App Icons, Boost, No Ads, Translation, build declarations, archive schema/transaction/store and backup UI bytes. No accepted store/Core/UI runtime owner changed during integration.

The portable composed chain passed: 33 unittest invocations, 236 discovered tests, 210 executed passes and 26 explicit skips. These are nested suite counts, not unique behavior or native evidence. Focused new stage/integration checks: 14 PASS. Integration discovery: 21 PASS. Migration/preservation: 11 PASS. Required store and Core commands each fail with the missing native-toolchain message on Linux; the final required-native runner also fails. Required full-source mode rejects the 421-file snapshot even with read-only upstream Git metadata (`.bazelrc` is absent). The original `work/swiftgram-src` symlink target was retained. Native compilation, the 100k-edge measurements, full-app compilation and device checks remain pending CI/device.

The final whole-branch review subsequently found I1: the store allocation check
ignored the runner's explicit parent and depended on private sibling BUILD
evidence. The scoped correction honors `JG_SAVED_TAGS_BEFORE`, follows unchanged
Postbox source directory symlinks, and reads the selected source BUILD or a
checked-in, hash-verified official declaration. A real isolated child regression
now passes without sibling research or SDD inputs and rejects allocation/key,
sink, glob and fixture corruption. Focused reruns: eight portable store tests
pass, one native test skips, and five runner integration tests pass; required
native mode still fails closed on Linux. Earlier composed/stage counts above
remain historical evidence. Scoped final re-review is pending; no runtime owner,
stage patch, workflow, native result or release state changed in this correction.

Whole-branch review, TASK B commit, remote SHA mapping/publication and Actions run/status remain parent-owned and pending. The detailed Task5 source/command/hash record is in `.superpowers/sdd/2026-11-05-local-premium-saved-tags/task-5-report.md` until the parent records publication evidence here.

## Explicit limitations

- Local tags have no cloud synchronization and are not included in current Jerkgram backups. Account removal or reinstall can lose them; this must be disclosed in RU/EN UI.
- Initial filtering selects one tag. Messages can carry multiple tags. Text search within the local filter is unavailable initially and must be stated explicitly.
- Missing/offline content does not prove deletion: retain its indexed row, cursors and retry/removal capability.
- Source snapshots and read-only Git metadata are not a full checkout. Portable results do not establish Swift compilation, native Signal/network behavior, device rendering or acceptable latency.
- No FPS, heat, Settings latency or successful retained-install recovery claim is made without device evidence.

## Added feature cost map (static bounds, not measured latency)

| Owner / event | Startup / idle | Settings / profile / typing | Active work |
| --- | --- | --- | --- |
| Local Premium Hub | No new timer or launch observer | Existing native controller; canonical state refresh on appearance; no profile/typing hook | Existing settings reads and change-only setters; no new store |
| Tag catalogue | Service created by active Saved UI; revision observation only while subscribed | No Settings/profile/keyboard observer | At most256 definitions; scalar revision through the existing preferences view |
| Selection / assignment | No periodic task | User action only; no per-cell query | One Postbox transaction, at most1000 raw selected IDs, at most16 relations per message; aggregate counts rather than1000 asynchronous transactions |
| Local results | No prefetch/launch subscription | No ordinary chat-history or typing rewrite | Reverse-index page at most45 rows; ordinary content reads for those IDs only; at most3 retained windows/135 rows and one active request |
| Confirmed deletion hooks | Event-driven global update cost exists even with tag UI closed | No rendering/typing hook | Metadata/catalogue/index lookups in the existing transaction; bounded input chunks, writes proportional to affected edges |
| Large tag/history deletion | No idle work | Shared Postbox queue may remain occupied while deletion runs | O(affected edges), bounded memory, one atomic transaction; native100000-edge queue latency remains unmeasured |

The delivery fence can wait for an already executing callback during teardown; callbacks must remain short and must not synchronously wait for teardown on another thread. Native UI delivery uses asynchronous main-queue delivery. The scoped concurrency fix review passed; actual queue scheduling and cancellation execution remain subject to the native gate.

## Required iPhone acceptance matrix

Target: iPhone14 Pro, iOS26.7.1. No crash report or screenshot is required from the user to proceed.

| Area | Check after installing over the retained app | Status |
| --- | --- | --- |
| P0 recovery | Repeated launch, retained accounts/history, bot account navigation and relaunch; do not delete app data | Pending device |
| Settings | Default Folder absent/inactive despite retained old preference; intended Gram card contrast; Media & Stories footer; Beta2 identity | Pending device |
| Hub | Native pushed route beside Backups; canonical icon; RU/EN and light/dark/large text | Pending device |
| Existing settings | Change App Icons/Boost/No Ads via old and new entry points, return and relaunch; Translation behavior unchanged | Pending device |
| Tags CRUD | Empty catalogue discovery, create/rename/delete, duplicate/invalid names and quota errors | Pending native/device |
| Assignment | One/multiple messages, mixed/all/none tag state, multiple tags and two Saved copies of the same source | Pending native/device |
| Complete filter | More than500 indexed messages, both pagination directions, offscreen results; window remains bounded | Pending native/device |
| Missing content | Offline unavailable row, explicit retry/remove; no loss of relations or pagination | Pending native/device |
| Lifecycle | Edit/reaction/refetch retains tags; confirmed cached/uncached/global/thread/range deletion cleans only affected edges | Pending native/device |
| Isolation | Account switch/removal, delayed network completion, pop/filter change, relaunch persistence | Pending native/device |
| Performance | Comparable first/repeat Settings, profiles, typing, heat; large indexed deletion queue latency | Unmeasured |

Final publication record must include exact TASK B commit, remote HEAD, complete changed-file list, mandatory native/source results and Actions URL/status. A green CI is not device runtime success.
