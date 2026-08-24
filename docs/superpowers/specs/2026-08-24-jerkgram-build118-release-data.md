# Jerkgram Build118 Time Machine, Release Data, Retention, and Runtime Polish Specification

## Status and evidence baseline

Build117 compiled and installed successfully. Device testing established:

- the Settings/self-profile route no longer exposes the custom history panes;
- ordinary user profiles still expose those panes;
- the complete profile report follows Telegram's RU/EN language;
- the live `@JerkgramApp` About row resolves and opens correctly, but is visually too small;
- numeric peer routes remain working;
- Share and Widget remain unusable and Broadcast still ends as `Finished`;
- the copied extension report still contains only the `app` process and resolves the selected App Group to a path ending in `/Documents/AppGroup`;
- competing ESign-distributed clients show the same extension failures, strengthening the process-local signing-topology diagnosis;
- presence history renders impossible rows such as an observation at `12:50:03` marked online until `12:39:57`.

Official Telegram 12.9.2 is the only API and behavior reference. The clean reference commit remains `6ad963e5b62d354da79040f388ae2b9132fb17b8`.

## Goals

Build118 must move the project toward a public release by delivering a real, safe data portability flow and closing the confirmed presence-history presentation defect. It also improves the About credits and converts the extension limitation into explicit release information rather than another unverified fix claim.

The deliverables are:

1. user-facing export and import of Jerkgram settings and structured histories;
2. versioned Archive v2 with stable event identifiers and Archive v1 migration;
3. component selection, record counts, per-component sizes, and total archive size;
4. transactional import preview with duplicate and conflict reporting;
5. per-account defaults and per-chat retention/privacy rules, including explicit unlimited modes;
6. Jerkgram Time Machine search over existing deleted, edited, and recovered records without a second payload copy;
7. exact edit diffs and a local “since last opening” change summary;
8. correct semantic presence history, including legacy-record rendering;
9. one consistent profile glass material across the confirmed profile, editing, shared-media, links, and report surfaces;
10. larger live cards for `@JerkgramApp` and `@JerkgramCommunity`;
11. honest extension compatibility status for the current ESign topology;
12. the normal release gates: semantic RU/EN localization, storage transparency, signer neutrality, strict verification, and one canonical Build118 artifact.

## Storage ownership and retention rules

Build118 introduces one account-scoped policy owner rather than adding more scattered `UserDefaults` switches. Every policy key begins with the exact Telegram account peer ID. Chat overrides add the exact chat peer ID. Display names, usernames, phone numbers, account slots, and localized strings never participate in policy identity.

Each account has these defaults:

- history retention: `30 days`;
- recovered-media byte limit: `1 GB`;
- Secret Chat archival: disabled.

History retention supports `Do not save`, `7 days`, `30 days`, `90 days`, and `Forever`. Recovered-media storage supports `Do not store media`, `250 MB`, `500 MB`, `1 GB`, `2 GB`, `5 GB`, and `Unlimited`. Duration and byte limit are independent. Therefore `Forever + 1 GB`, `30 days + Unlimited`, and `Forever + Unlimited` are all valid and have different behavior.

`Forever` disables age pruning for the affected records. `Unlimited` disables recovered-media byte-budget eviction. Selecting both disables automatic age and byte-limit deletion for that scope. The UI must present a localized confirmation explaining that this can fill device storage. An out-of-space or write failure keeps the structured/text fallback, records a bounded error state, and never crashes or silently claims that media bytes were saved.

Per-chat rules inherit the account defaults until the user creates an override. A chat override can independently change history retention, media limit, and whether capture is enabled. Secret Chats are excluded before capture unless the account-level Secret Chat switch is explicitly enabled; individual Secret Chats can still be disabled through a chat override.

The `Data and Backup` page exposes:

- account defaults grouped by Telegram account;
- chat-specific overrides with search;
- current structured-history size and recovered-media size;
- cleanup for one chat, one data type, one account, or expired data;
- a destructive confirmation that names the exact account, chat, component, record count, and bytes to be removed.

Cleanup and pruning are serialized with capture/import writes. They operate on `(accountPeerId, chatPeerId, eventId)` and never delete another account's records. Expiry uses the event observation/capture time. Byte-budget eviction removes oldest recovered-media bytes first while retaining the structured event and text fallback until its history-retention rule expires.

Legacy global retention values migrate once into independent account defaults for accounts authorized at migration time. Existing recovered-media behavior migrates to `30 days + 1 GB`. The migration never enables Secret Chat archival.

## Jerkgram Time Machine

Time Machine is a local query/index layer over the existing Jerkgram stores. It must not duplicate message bodies, media bytes, edit snapshots, or profile payloads. The index stores only stable references and searchable fields needed to locate the canonical record:

- account peer ID;
- chat peer ID;
- stable event ID;
- event kind;
- original message namespace and ID when known;
- sender peer ID when known;
- capture/observation timestamp;
- normalized search tokens or an equivalent bounded search key;
- canonical-store locator and availability state.

The ordinary in-chat search receives a localized Time Machine filter surface with:

- Deleted;
- Edited;
- Recovered Media;
- From User.

Filters can be combined. Text search is optional: an empty query with a filter lists matching local changes in reverse chronological order. `From User` uses the exact sender peer ID and Official Telegram's peer-selection/display patterns. Results remain scoped to the current `(accountPeerId, chatPeerId)` and never leak records from another account or chat.

Selecting a result follows one of two typed routes:

- if the canonical Telegram message still exists, open it through Official Telegram's normal message navigation/highlight path;
- if it was deleted or only a local historical version exists, open a local Time Machine detail screen backed by the canonical Jerkgram record.

The local detail screen shows chat, sender, observation time, event kind, original message identity when known, structured text fallback, and recovered-media availability. It does not fabricate a live Telegram message or write the deleted message back into Postbox.

### Edit diff

Edited results show every retained version in chronological order and an exact diff between adjacent versions. Diff input is canonical message text/caption, not a localized rendering. Tokenization preserves Unicode extended grapheme clusters and groups words, whitespace, and punctuation. A bounded Myers/LCS-class sequence diff produces insertions and deletions; an adjacent deletion/insertion span is presented as a replacement. The UI distinguishes:

- removed content;
- added content;
- replacement before and after values;
- unchanged context around the change.

Identical rendered text with different event IDs remains distinct. Entity metadata and recovered-media descriptors are shown separately instead of being flattened into misleading text. Large messages use bounded computation and fall back to line/paragraph-level chunks before grapheme-level refinement.

### Since last opening

Each `(accountPeerId, chatPeerId)` has a local `lastAcknowledgedEventSequence`. When a chat becomes visible, Build118 atomically snapshots the current maximum Time Machine sequence, queries changes after the previous watermark, and renders a small dismissible row equivalent to `Since last visit: 3 deleted, 2 edited`.

The row appears only when there are changes, never schedules notifications, and performs no background surveillance. Tapping it opens Time Machine prefiltered to the captured sequence interval. The watermark advances to the snapshot taken when the chat opened, so events arriving during the current viewing session remain eligible for the next visit. Watermarks are local transient state: they are not exported or imported.

Index repair is deterministic. At Build118 migration, existing canonical records without index entries are scanned incrementally off the main thread. Missing canonical records leave bounded unavailable index entries that can be cleaned; they are never reconstructed from display text.

## Archive format

The public file extension is `.jerkgram`. The file is a ZIP container produced and read with the `ZipArchive` dependency already used by Official Telegram.

The logical layout is:

```text
Jerkgram-<date>.jerkgram
├── manifest.json
└── accounts/
    └── <account-peer-id>/
        ├── settings.json
        ├── deleted-messages.jsonl
        ├── edited-messages.jsonl
        ├── deleted-replies.jsonl
        ├── profile-history.jsonl
        ├── presence-history.jsonl
        ├── gift-history.jsonl
        └── personal-channel-history.jsonl
```

Build118 exports structured records and text metadata only. Photo, video, voice, sticker, animation, audio, and document bytes are not included. A future schema may add media as a separate component that is disabled by default.

`manifest.json` contains:

- archive schema version `2`;
- source Jerkgram version and Build;
- creation timestamp;
- account peer IDs represented in the archive;
- selected components;
- record count and uncompressed byte count for each component;
- compressed archive size once packaging finishes;
- SHA-256 for every payload file.

The importer rejects path traversal, duplicate archive paths, undeclared payload files, missing declared files, checksum mismatches, unsupported schemas, malformed JSON/JSONL, excessive file sizes, and excessive event counts before it mutates local data.

## Stable identity and deduplication

Every exported history record has a persistent `eventId`. Its import identity is the pair `(accountPeerId, eventId)`. Text, captions, names, and other user-authored content never participate in duplicate identity.

New records receive their ID once when captured and retain it through every export, import, and re-export. Existing records without IDs receive a deterministic migration ID derived from stable structural fields such as account, peer, message namespace/ID when applicable, event kind, event timestamp, and a structural discriminator. The migration does not hash the user-authored text to decide identity.

Import behavior is:

- same `eventId` and byte-equivalent canonical record: duplicate, skip;
- same `eventId` but different canonical record: conflict, do not overwrite silently;
- different IDs with identical text: preserve both;
- new ID: merge into the destination history.

Conflicts are reported before confirmation. Build118 does not offer a destructive “replace all histories” operation.

Archive v1 is accepted and migrated to v2 in memory before preview. Its history events are grouped by their embedded `accountPeerId`. A legacy root settings snapshot is eligible only when the v1 archive resolves to exactly one account and that exact peer ID is authorized locally; otherwise legacy settings are marked ambiguous and disabled rather than copied across accounts. The original imported file is never modified.

## Account isolation and matching

Every exported component, including settings, belongs to exactly one Telegram account peer ID. Build118 does not place account-scoped settings or histories in a shared root payload.

The export screen groups components by the Telegram accounts currently present in the client. Multiple accounts can be exported in one archive, but each receives its own directory and component totals. The same message identifiers or equal content observed through two accounts remain two independent records because their account peer IDs differ.

Before import, each archived account peer ID is matched only to the identical Telegram peer ID among the accounts currently authorized in Jerkgram. Build118 never guesses by display name, username, phone number, account slot, or current active account, and it never maps an archived account to a different Telegram account automatically.

The preview classifies every archived account as:

- matched: eligible for component preview and import into the same Telegram account;
- unavailable: that Telegram account is not currently authorized, so all its components remain disabled and local data is untouched;
- already current: matched normally; duplicate detection still runs per component.

Accounts present locally but absent from the archive are untouched. Importing one account cannot create deleted messages, histories, or settings under another account.

Current legacy Jerkgram preferences stored without an account scope are migrated once on Build118 startup. Their effective values are copied into a separate typed settings snapshot for each account already authorized at migration time, preserving the previous behavior while allowing the accounts to diverge afterward. The legacy keys become read-only compatibility input and are not used as the new source of truth. A subsequently added Telegram account starts from explicit Jerkgram defaults.

## Settings snapshot

Each `accounts/<account-peer-id>/settings.json` is a typed snapshot of the actual Jerkgram preference values for that account at export time. It includes all supported Jerkgram toggles and bounded scalar choices such as send style, feature switches, protection options, recovery options, appearance selections, and other semantic Jerkgram settings.

It does not include Telegram account authorization, auth keys, tokens, Keychain material, session credentials, notification credentials, signing identity, provisioning data, transient caches, sandbox paths, or debug dumps.

It does include the typed account retention defaults, Secret Chat archival choice, and per-chat overrides because these are user-authored Jerkgram settings. Imported overrides retain their exact archived account and chat peer IDs and are eligible only when the archived account matches the identical authorized local account. Time Machine visit watermarks, temporary index-repair progress, free-space errors, and cleanup previews are transient state and are not exported.

Before import, the UI lists settings changes separately under each matched account and shows only values that would change, using localized transitions such as `Off → On` or the corresponding old and new enum values. History components merge independently. Settings are applied only if the user keeps that account's Settings component selected and confirms the settings changes explicitly.

Application is staged: every selected component is decoded and validated first, a rollback snapshot is prepared, and only then are writes performed. Any write failure restores the pre-import snapshot. A successful settings import triggers the existing settings update path so observers refresh without requiring a restart where the current architecture supports live updates.

## Export UI

Jerkgram Settings receives a localized `Data and Backup` / `Данные и резервная копия` page with Export and Import actions.

The Export screen groups rows by Telegram account and selects every safe component for every currently authorized account by default. Each row shows:

- localized component name;
- record count where applicable;
- calculated uncompressed size;
- an enabled selection control.

The footer shows the total selected size. Calculation and archive creation run away from the main thread and expose loading/progress/error states. The final screen shows the exact compressed file size and opens the native system export/share flow using Official Telegram's existing `legacyICloudFilePicker` and system activity-controller patterns.

No export button becomes active until size calculation and validation complete. Temporary files are bounded and disposed after the system handoff finishes.

## Import UI

Import opens the native document picker and accepts `.jerkgram` plus compatible v1 archives. After security-scoped access is acquired, the archive is copied to a controlled temporary location and inspected without mutating stores.

The preview shows:

- source Jerkgram version and Build;
- creation date and archive size;
- accounts represented;
- exact archived-account to local-account matches, without cross-account fallback;
- every component with its size and record count;
- new, duplicate, and conflict counts;
- settings changes as old-to-new values;
- any unsupported or omitted components.

All compatible components start selected. A conflict blocks final import until the conflicting component is deselected; Build118 does not guess which record is correct. The confirmation action states exactly what will be merged and whether settings will change. Completion reports imported, skipped, and unchanged totals.

## Presence-history correction

The confirmed root cause is semantic. Telegram maps both `userStatusOnline(expires:)` and `userStatusOffline(wasOnline:)` into `.present(until:)`. Official Telegram determines the meaning by comparing `until` with the reference timestamp; the Jerkgram logger currently labels every `.present` value as online.

Build118 normalizes presence events relative to their observation timestamp:

- `until >= observedAt`: online observation, with a valid end timestamp;
- `until < observedAt`: exact last-seen observation, never “online until”;
- `.recently`, `.lastWeek`, and `.lastMonth`: approximate states with their hidden flag preserved.

The rendered history remains ordered by observation time and distinguishes observation time from server-reported last-seen time. Existing stored records are corrected at render/migration time without deleting the history. Exact last-seen information takes precedence over a redundant approximate observation for the same effective state, and consecutive semantic duplicates are compacted without merging genuinely distinct events.

The UI no longer presents impossible ranges. A corrected row is equivalent to `Observed 12:50:03 · last seen 12:39:57`, localized through `JerkgramStrings`.

## Profile glass parity

The Build117 device screenshots establish the custom profile-report cards as the material reference. The desired result is not a bare transparent list and not a second blur per row. Build118 centralizes the reference material in one narrowly scoped profile-glass surface helper:

- transparent pane/root background so the existing fullscreen wallpaper/avatar scene remains the single backdrop owner;
- 16-point card radius;
- dark appearance fill equivalent to black at alpha `0.075`;
- light appearance fill equivalent to white at alpha `0.035`;
- no per-cell `UIBlurEffectView`;
- separators, highlights, accessibility contrast, and native scrolling geometry retained.

The helper is enabled only when Jerkgram Glass is enabled. Turning Jerkgram Glass off must restore untouched Official Telegram colors, masks, corner fillers, and layouts.

The confirmed surface owners are corrected as follows:

1. profile/channel sections: `PeerInfoScreenItemSectionContainerNode` owns the common card, while scoped child item backgrounds and surviving stock corner fillers are cleared only inside that card;
2. profile editing: `PeerInfoHeaderEditingContentNode` and its text-field groups receive the glass-enabled state and use the same card material instead of the independent stock editing background;
3. Files, Music, and Voice: list-mode `PeerInfoVisualMediaPaneNode` replaces the opaque `listBackgroundView.tintColor = itemBlocksBackgroundColor` presentation with the common card material while preserving native list layout and playback/download interaction;
4. Links: list mode receives a real rounded common-material group surface rather than merely clearing its root background;
5. custom History, Presence, Gift History, and Personal Channel panes continue using the same reference material through the shared helper instead of maintaining a divergent hardcoded copy.

The fix is owner-based, not a global color replacement. Media grids, avatar/video-avatar rendering, tabs, native navigation controls, fullscreen transition geometry, and GBGlass-off behavior remain unchanged.

## About credits

The About page shows two dedicated, larger live credit cards:

- official channel: `@JerkgramApp`, avatar, title, username, and bounded latest-post preview;
- community: `@JerkgramCommunity`, avatar, title, username, and a bounded live subtitle appropriate to the resolved peer.

Both peers are resolved through `TelegramEngine`, retained as `EnginePeer`, and opened through canonical Telegram navigation. The cards use a dedicated large credit presentation with a larger avatar and at least an 88-point row height instead of the current compact peer row. Loading, offline, empty, and unavailable states are semantic RU/EN strings and never fabricate peer metadata.

## Extension release behavior

Build118 does not claim that Share, Widget, or Broadcast are fixed. Current post-ESign evidence shows a process-local `/Documents/AppGroup` path and no cross-process diagnostic records. The system Broadcast UI also collapses the extension error to `Finished`, so changing only `NSError.localizedDescription` is not a reliable visible surface.

The extensions remain in the artifact for compatible signing environments. Jerkgram Settings exposes a bounded localized compatibility status derived from the shared-container classification:

- `shared`: extensions may use shared account data;
- `processLocal`: current signature isolates extension data;
- `missing` or `other`: extension storage is unavailable or unsupported.

The UI must not state that an extension works merely because it is bundled. Existing bounded/redacted diagnostics remain, but Build118 adds no blind App Group selector change and no claim of runtime success. A real functional fix requires a signing topology that gives the main app and each extension coherent application-group entitlements and containers.

## Limits and safety

- Maximum aggregate event count per portable archive remains 100,000. Runtime stores may retain more only when user-selected retention permits it; indexing and UI remain paginated/bounded.
- The importer enforces bounded manifest, settings, per-component, and total extracted sizes before allocation or decoding.
- JSONL is processed incrementally where possible; the main thread never decodes or writes a full history archive.
- Temporary extraction uses a unique directory and rejects paths escaping that directory.
- No localized string is stored as a semantic setting value.
- No full sandbox UUID path is exported or displayed.
- Import never changes Telegram authorization state.
- Unlimited retention and unlimited recovered-media storage are explicit user choices, never defaults.
- Out-of-space failures preserve structured/text fallbacks and expose an actionable localized error.

## Verification and release gates

Fixture and integration tests must prove:

- stable event IDs survive export/import/re-export;
- every event and settings snapshot remains isolated by Telegram account peer ID;
- an archive containing two accounts cannot duplicate one account's data into the other;
- unavailable archived accounts remain disabled and cause no writes;
- legacy global Jerkgram settings migrate once into independent per-account snapshots;
- identical text with different IDs is preserved;
- matching IDs are skipped only when canonical records match;
- conflicting records never overwrite silently;
- Archive v1 migrates to v2;
- settings snapshot round-trips real toggle and enum values;
- account defaults and per-chat retention overrides round-trip without crossing account peer IDs;
- the default policy is 30 days, 1 GB, and Secret Chat archival disabled;
- every finite duration expires only eligible records and `Forever` skips age pruning;
- every finite media budget evicts oldest bytes while preserving structured fallbacks and `Unlimited` skips byte-budget eviction;
- `Do not save` prevents capture before payload persistence;
- chat/type/account cleanup reports and removes only the selected scope;
- Time Machine indexing stores references instead of duplicate payload bodies or media bytes;
- deleted, edited, recovered-media, author, combined, and empty-query filters return only the current account/chat scope;
- live results use canonical message navigation and deleted-only results use the local detail route;
- Unicode edit diffs classify insertion, deletion, replacement, and unchanged context deterministically;
- identical text with different event IDs remains visible as distinct Time Machine events;
- “since last opening” counts exact event IDs in the captured sequence interval, advances its watermark atomically, and is never exported;
- settings preview reports exact value transitions;
- component and total sizes match generated payloads;
- malformed, oversized, path-traversing, or checksum-invalid archives are rejected before writes;
- presence online/offline semantics match Official Telegram behavior and legacy impossible rows are corrected;
- profile/channel sections, profile editing, Files, Music, Voice, Links, and custom report panes use the one reference glass material when enabled;
- Jerkgram Glass off restores Official Telegram surface ownership and colors;
- profile glass adds no per-row blur views and preserves native list interaction/geometry;
- both About peers resolve through typed Official APIs and use canonical navigation;
- all new visible text is semantic RU/EN localization;
- extension status is classified and redacted without a false success claim;
- the active workflow publishes exactly one success artifact named `Jerkgram-build118` containing `Jerkgram-build118.ipa` and its info file;
- final materialized-source verifiers run after all Build118 overlays and before Bazel.

Device acceptance requires both an update over Build117 and a clean install. Compile green is not runtime proof.

## Non-goals

- exporting binary media bytes;
- exporting Telegram credentials or complete Telegram databases;
- destructive replacement of all histories;
- reconstructing deleted messages as live Postbox messages;
- background notifications for Time Machine summaries;
- a second copy of canonical history payloads for search;
- fabricating Telegram peers or access hashes;
- copying proprietary competitor or Whitegram code;
- claiming ESign extension compatibility without a shared runtime container;
- broad legacy GhostBase renaming unrelated to this functional build.
