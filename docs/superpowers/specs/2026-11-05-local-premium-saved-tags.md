# Local Premium Hub and local Saved Messages tags

> Latest user steering: retain this recovery as a reviewed local base. Do not publish or launch a separate recovery IPA. Implement Local Premium (TASK A) and Saved Messages Tags (TASK B) as separate descendant commits, then review and build one combined release. This supersedes the earlier recovery-first delivery order below. Native/device gates remain pending.

## Authority, baseline and sequence

Implements the user's TASK A and TASK B after the separately prepared Beta 2 launch recovery. User has authorized implementation, ordinary design choices, publication and an IPA build. Do not ask for unavailable crash reports/screenshots. Do not begin other Premium capabilities or repair Translation.

Source evidence: `jerkgram-next/beta2/research/premium-settings/AUDIT.md` and `jerkgram-next/beta2/research/saved-tags/AUDIT.md` beside the builder. These distinguish exact official Telegram 13.1.2 pin `279f89e4d4f63f17227bf877dc3d8990f22ecd58` from the patched Build178 owners. Reconfirm the actual accepted recovery parent before implementation. Use a descendant feature branch in the current checkout, preserving the recovery build's branch and immutable source evidence.

TASK A and TASK B are separate product commits. Each requires its own exact source stage, verification and reverse-parent view for historical gates. No global Premium spoof, swizzling, new global observers, polling timer, source model bypass or mechanical Swiftgram transplantation. No implementation is complete merely because CI is green; retain an explicit device matrix.

## TASK A: native Local Premium Hub

Add `Local Premium` / `Локальный Premium` beside Backups on the reachable Jerkgram `.home` page, through the existing page enum and native `openPage` push. The dormant `.root` is not a substitute. Reuse the existing controller/state, list rows, glass admission and back navigation; no modal or copied settings hierarchy.

Use the actual official `PresentationResourcesSettings.premium` tile, whose bundled glyph is `Item List/Icons/Premium`, through the existing settings icon helper/resource renderer. Do not create a renderer or asset, draw a diamond, or substitute SF Symbols/emoji/collectible artwork. This is the canonical Telegram Premium Settings resource; the source name alone does not prove it is diamond-shaped.

Three groups:

| Group | Controls | Persistence contract |
| --- | --- | --- |
| Appearance / Внешний вид | Existing App Icons toggle | `jerkgram.LocalPremium.AppIcons`, device-global bool, existing direct setter |
| Media / Медиа | Existing Download Boost picker and same-section explanation | `jerkgram.DownloadBoost.Mode`, existing account-scoped `off`/`medium`/`maximum` values and default |
| Messages / Сообщения | Existing No Ads toggle; existing Translation control marked `Needs work` / `Требует доработки` | Existing account-scoped `jerkgram.SponsoredContent.Remove` and `jerkgram.EnhancedTranslation`, same setters/defaults |

Reuse `GhostBaseSettingsState` and `jerkgramPersistChangedSettings`; do not introduce a second settings store or migrate App Icons into account scope. Retain old entry points as aliases for the first release unless the existing refresh semantics cannot safely keep them coherent. Opening a page never writes settings. Aliases must read the same current state when returning/reopening; an old controller snapshot must not revert unrelated changes.

Unique native entry IDs: distinct groups and at most one info row per section. No Default Folder row/claim, extra-account feature or common Premium switch. A short RU/EN footer explains local scope without implying Telegram entitlement. Do not silently expand backups. Verify all four existing settings' values and consumers remain unchanged, including account switching and invalid Boost values.

## TASK B: independent local tags

Telegram's documented Saved reaction-tag mutations are Premium operations. This audit did not make live entitlement probes. Keep official reactions, stats, caches, pending actions, API calls and entitlement checks unchanged. Local mutations never invoke `messages.sendReaction` or `messages.updateSavedReactionTag`.

### Durable authority and identity

Implement dedicated account-local Postbox tables and transaction methods, following real current schema/table-ID allocation. Do not use a single JSON/defaults dictionary, evictable ItemCache, transient message attributes or raw arbitrary cloud custom tags as authority. The latter enters an unsupported cloud hole-fetch path; official reaction search also truncates at 500 and is unsuitable.

Logical data:

- Tag definition: opaque stable string ID, normalized display name, order and explicit version. Names: trim whitespace, normalize canonically, reject empty/control-only names, at most 64 grapheme clusters and 256 UTF-8 bytes. Reject normalized duplicate names with localized feedback. Emoji may be part of the name; no premium media dependency.
- Unique membership: current full Saved `MessageId` plus tag ID. Never use the original forwarded message ID, album grouping or globallyUniqueId.
- Reverse index: tag ID, message timestamp, namespace and message ID for deterministic keyset paging, plus direct Saved cloud numeric-ID lookup for uncached global deletions. Store thread metadata where semantic deletion requires it.
- Transactional counts/revision; rename updates one definition and does not rewrite memberships. No live association eviction or age limit.

Only stable cloud messages in the current account's self-chat can be assigned initially. Pending messages show a clear unavailable action until acknowledgement. Every asynchronous operation is bound to account record/environment/service generation. Physical account-store lifetime provides isolation; account removal removes its local data. Do not reattach data across accounts or environments.

All custom Postbox Codable adapters use explicit supported fixed-width/keyed primitives, checked ranges and bounded decoding. No synthesized `Int` or raw-enum single-value payloads. Verify actual production Postbox roundtrips; JSON-only fixtures do not qualify.

Admission limits for the first implementation: 256 definitions per account, 16 tags per message, 100,000 membership edges per account, and 1,000 selected messages per atomic batch. These are explicit product bounds, not measured performance claims. Validate before committing and reject additions atomically with RU/EN quota/storage feedback; never evict existing rows. Deletion/removal remains available at quota. Keep disk overhead proportional to accepted data and metadata bounded; do not claim a byte quota without actual schema accounting. If native selection exceeds the batch bound, explain the limit rather than silently truncate or partially apply.

### Native UI and complete filtering

Create/manage native ItemList or text-input alert UI and a clearly labeled `Local tags` / `Локальные теги` entry in Saved Messages. Use the existing native search accessory/result-list components where practical. Context-menu assignment takes the current passed message ID; batch assignment takes the entire selected ID set, with mixed/selected states. Add/remove only the chosen relation, retaining unrelated tags. Creation, rename, deletion, empty-tag management and active-filter deletion must all work for non-Premium accounts.

One selected tag at a time is sufficient; multi-tag assignment remains mandatory. Text search inside the local filter is explicitly unavailable in this first release, with truthful UI; do not silently run a cloud query or scan all history. Cloud tags keep their independent native path.

Use an explicit local filter domain and provider identity; never encode local IDs as a fake `Reaction`. Query the reverse membership index for pages of 45 rows, at most three loaded windows (135 rows), one active load and at most one adjacent prefetch. Each page has earlier/later cursors and a revision. Evict only rendered windows, never stored memberships. Reject stale responses on filter/account changes. Reach every indexed association regardless of viewport or the ordinary chat's loaded history; no total-result cap.

Read only indexed page IDs. Missing message content can use ordinary authorized message-by-ID reads in bounded cancellable batches. An empty/error result is not proof of deletion: retain membership and show unavailable/retry state with usable pagination. Do not fabricate Telegram messages. Native result selection navigates to the current Saved message. No permanent full membership/message array, history scan, filesystem/JSON/defaults access in scroll/layout, or per-cell subscription.

### Edit and deletion semantics

Edits/reactions/content refetch preserve relations. Distinct Saved copies remain independent when the original forwarded source changes or disappears. Confirmed Saved deletion removes only that message's edges and counters, including uncached memberships. Explicit tag deletion removes only its definition/edges, never Telegram history. Deleting the active tag clears the local filter.

Integrate cleanup transactionally at actual semantic single/batch/global-ID/range/thread/full-history deletion owners, including the current patched state replay. A low-level cache removal or failed load must not purge relations. Full/range clears query indexed memberships rather than scan history. Preserve existing deleted-history retention presentation and ordinary history semantics. Document any unsupported semantic path as a release blocker rather than silently leaving orphan relations.

### Backup and locality

Initial tags are local to this installation/account store, are not synchronized and are NOT included in the current Jerkgram backups. State this in RU/EN management UI and release notes. Do not expand archive formats in this task; a new backup component can be separately authorized later. Reinstall/account removal can lose local tags. Do not promise cloud or reinstall recovery.

## Verification and delivery

TASK A: reachable push/icon resource; RU/EN and stable row IDs; same key/scope/default/writes for all four settings; no settings write on open; aliases/back navigation/account switching; no entitlement changes; Translation unchanged.

TASK B: native/storage tests for real persistence, explicit codecs and malformed bounds; uniqueness/rename/delete/multi-tag/batch atomicity/quota; two accounts with overlapping IDs; forwarded-copy identity; edits and every semantic deletion path; unavailable content retained; oldest of at least 1,001 memberships reachable bidirectionally without a history scan; bounded windows/request disposal/stale generations; no local tag mutation network calls; backup limitation and RU/EN owners. Add meaningful measurements for index page cost and loaded-window bounds without requiring an hours-long build.

Exact materialization parent refusal must precede mutation; reapply no-op, reverse-exact and old gates on restored parents. Required macOS source/native checks precede one product IPA build on the accepted base. Monitor only the first few minutes, as requested, and continue other authorized work without waiting for the IPA. Report actual commits, branch/HEAD/upstream/build, owner/file list, local/native/CI evidence, runtime checklist and remaining limitations separately.
