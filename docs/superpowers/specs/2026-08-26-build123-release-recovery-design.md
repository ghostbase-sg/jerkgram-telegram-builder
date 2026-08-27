# Build123 Release Recovery Design

## Scope

Build123 fixes the fifteen runtime and UI regressions reported after Build122 without changing the Official Telegram 12.9.2 baseline (`6ad963e5b62d354da79040f388ae2b9132fb17b8`). The release remains a deterministic overlay chain and must materialize cleanly from that baseline.

## Architecture

### Settings and runtime state

Introduce one per-account settings owner. The UI, import/export, and runtime features read the same account snapshot. When an account becomes active, the snapshot is atomically projected to the legacy global and app-group keys still consumed by extensions and existing Telegram owners. Individual toggles persist only their changed key on a serial queue; they must not enumerate and mirror the complete `UserDefaults` dictionary on the main thread.

Import validates and stages all account payloads before committing. A successful import refreshes the active runtime projection once. A failed import preserves the previous settings, history, and retention state.

This contract applies especially to Scheduled Send and one-time/timed media retention, eliminating a UI/runtime split where a disabled toggle can leave an enabled global value behind.

### Portable message snapshots

Create one portable message snapshot/builder shared by deleted-message recovery, protected-channel forwarding, Forward Without Author, and edit history. A snapshot contains text, text entities, caption entities, supported media references, grouping metadata, source peer identity, and an observation timestamp.

For protected sources, normal portable forwarding appends the channel title and a public link only when the link can be resolved safely. Forward Without Author omits attribution. The action is offered from ordinary message/media context menus based on reconstruction support, not Telegram's server-side `.forward` permission.

Existing secret-chat and paid-media restrictions remain intact. Unsupported media must fail visibly instead of enqueuing a broken outgoing message.

### Edit history

History records become backward-compatible versioned snapshots. New versions preserve `MessageTextEntity` data, including text URLs and custom emoji file identifiers, plus the real edit/observation timestamp. History rendering restores text entities and resolves inline premium emoji through Telegram's existing entity/media pipeline. Old string-only records remain readable.

History entries use actual timestamps and Telegram-style date grouping. Entity-only edits are recorded. Deleted-message reconstruction preserves embedded links and formatting.

### Profile glass surfaces

Glass state is passed explicitly from the profile screen owner into edit controls and header surfaces; child nodes must not infer it from optional `UserDefaults` values.

The description expansion fade uses the current glass surface instead of `itemBlocksBackgroundColor`. Common Groups receives the same single rounded readability surface as neighboring profile cards. Links removes the full-height outer glass plate and retains the Build115 luminance-based row readability treatment, with one consistent set of horizontal insets.

### Authorization and profile actions

Safe/Ghost login is visible on the phone-entry screen both for the first account and while adding another account. The experimental Jerkgram-injected Get Link control under groups/channels is removed without removing Telegram's standard username rows or message-link actions.

### Settings UI

All internal Jerkgram settings pages use a shared component language: compact glass sections, clear hierarchy, consistent switch/action states, descriptive status text, and no per-row heavy blur. The root section structure remains recognizable. Time Machine receives the same redesign, including filter controls, dated results, readable previews, and empty states.

### Responsiveness and diagnostics

Toggle persistence and archive work must not perform file or bulk-default operations on the main thread. Export/import runs asynchronously with progress and completion/error feedback. Bounded signposts cover cold-start initialization, settings commits, and archive transactions so a remaining device-only hang can be localized.

## Verification

Each layer has a verifier that first fails against Build122 and then passes against Build123. Verification covers state ownership, no bulk main-thread mirroring, entity preservation, protected portable forwarding, dates, profile glass ownership, Links sizing, Groups surface, login visibility, Settings component usage, and Build123 workflow identity.

The final gate is a clean materialization from Official Telegram 12.9.2, the full repository test suite, Swift warning gates, macOS CI, and a focused device checklist for cold start, toggles, one-time media, protected forwarding, history, profile editing, and Links with one and many items.
