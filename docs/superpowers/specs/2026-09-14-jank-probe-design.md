# Jerkgram Jank Probe Design

## Goal

Add a low-overhead diagnostic layer that can identify where severe UI hitches originate in two reproducible scenarios without changing avatar/rendering behavior yet:

1. Jerkgram Settings: rapid repeated vertical scrolling while an animated avatar is active.
2. Chat: beginning/continuing text input when the UI suddenly drops frames and then recovers.

This phase is diagnostic only. It must not change Telegram/Jerkgram rendering policy, avatar loading policy, filtering semantics, persistence semantics, or feature behavior.

## Success criteria

A runtime test must produce a compact report that answers:

- when a hitch occurred;
- frame gap duration;
- current UI context (Settings / Chat / Other);
- whether scrolling, typing, keyboard visibility, and animated-avatar state were active when known;
- which instrumented region(s) overlapped the hitch;
- per-region duration and call count inside the capture window;
- whether the main thread was busy/stalled versus the frame gap occurring without matching instrumented main-thread work;
- bounded CPU/RAM/thermal snapshots sampled outside the per-frame hot path;
- whether repeated scenarios show accumulating callback/subscription/update counts.

The probe is useful if it can narrow the problem to a bounded owner or distinguish a likely UI/main-thread bottleneck from a rendering/compositor bottleneck.

## Non-goals

- Do not optimize Telegram or Jerkgram yet.
- Do not change `synchronousLoad` or the avatar/background pipeline yet.
- Do not add continuous file logging.
- Do not persist one record per frame.
- Do not add global JSON/UserDefaults work to scroll/layout/input hot paths.
- Do not attempt to instrument the whole Telegram codebase in this phase.
- Do not expose a visible Debug menu.

## Architecture

### 1. Frame monitor

Use one lightweight `CADisplayLink` owned by the TelegramUI/Jerkgram diagnostic layer. It records only monotonic timestamps and classifies gaps. Normal frames are not expanded into verbose records.

Initial thresholds:

- `>= 33 ms`: hitch
- `>= 100 ms`: severe freeze
- `>= 250 ms`: critical freeze

The implementation must use actual display-link timestamps rather than assuming a fixed 60 or 120 Hz display. The report may include the observed/target cadence, but hitch classification remains based on elapsed wall-clock frame gaps so it works across ProMotion changes.

### 2. Bounded in-memory ring buffer

All capture data stays in RAM during normal operation.

The buffer is fixed-size and overwrites oldest entries. No unbounded arrays, logs, dictionaries keyed by arbitrary peers/messages, or per-frame strings are allowed. Event payloads should use compact enums/identifiers and numeric timestamps; human-readable formatting happens only when the user explicitly requests a report.

No disk write, `UserDefaults.set`, JSON encoding, clipboard access, or expensive string formatting is allowed in the display-link callback or instrumented hot regions.

### 3. Region instrumentation

Add scoped begin/end timing around a deliberately small set of owners relevant to the two reproductions.

Settings/profile candidates:

- Settings/profile header layout/update owner;
- Jerkgram profile/fullscreen background update owner;
- avatar image/request/update owner around the Jerkgram-added background path;
- animated-avatar/video state update owner if a stable existing owner can be identified without broad refactoring.

Chat/input candidates:

- chat text-input state/update owner;
- Jerkgram activity/typing suppression decision path;
- any Jerkgram settings snapshot or feature projection path reached by input;
- bounded Postbox/transaction boundary only if the first measurements show it overlaps the stall.

Each region records:

- region identifier;
- begin/end monotonic timestamp;
- thread classification (main/non-main where useful);
- call count and aggregate duration for the report window.

Instrumentation must not allocate formatted strings per invocation.

### 4. Context state

Maintain tiny in-memory state flags/counters for:

- current screen context: Settings / Chat / Other;
- scrolling active when observable from the existing owner;
- typing/input active;
- keyboard visible when cheaply available from existing state;
- animated-avatar active when a reliable existing state is available.

If a state cannot be obtained cheaply and reliably from an existing owner, omit it in phase 1 rather than introducing observers purely for diagnostics.

### 5. Stall interpretation

The probe must not claim a root cause automatically.

For each severe hitch it should report evidence:

- frame gap duration;
- overlapping instrumented regions;
- aggregate/call-count anomalies in the preceding capture window;
- main-thread heartbeat/stall evidence if implemented cheaply;
- CPU/RAM/thermal snapshot near the event.

Interpretation rules:

- A long frame gap with a matching long main-thread region is evidence for that owner being on the critical path.
- A long frame gap with a main-thread heartbeat stall but no matching instrumented region means the owner is outside the current instrumentation and the next pass should instrument the enclosing caller/path.
- A long frame gap while the main thread remains responsive and no expensive region overlaps is evidence to investigate render/compositor/GPU/video paths rather than declaring Swift business logic guilty.
- Stable RAM does not rule out CPU spikes, lock contention, synchronous I/O/decode, repeated callbacks, or rendering stalls.

### 6. Accumulation detection

Because the reported issue can appear after repeated interaction, retain bounded counters for selected owners during one capture session:

- calls per second/window;
- active/created timer count where an existing owner can expose it cheaply;
- repeated callback/subscription invocation count for the specific Settings/avatar and Chat/input paths.

The first phase does not add broad global subscription tracking. It only counts already-known candidate owners.

### 7. Report access with Debug UI hidden

Do not rely on a visible Debug menu.

Add a hidden, explicit report action to an existing Jerkgram-owned About/Version surface: a long-press on the Jerkgram version row copies a compact performance snapshot to the clipboard and gives a minimal confirmation. A normal tap and the visible layout remain unchanged.

The report is generated only on this explicit action. Formatting/JSON/text generation and clipboard work are therefore outside scroll/input hot paths.

The snapshot should include a short build/probe version plus the most recent severe hitches and aggregate counters. It must not include message text, peer names, usernames, phone numbers, auth data, tokens, media contents, or other private chat payloads.

If the existing About row cannot safely host a long-press without disturbing its behavior, use another already Jerkgram-owned settings row; do not add a visible Debug section.

### 8. CPU / RAM / thermal sampling

Sampling is supplementary and low-frequency. Do not poll every frame.

- RAM: reuse the existing shared Jerkgram memory sampler where possible rather than adding another competing sampler.
- CPU: sample only at low frequency or around a severe hitch from non-main work where practical.
- Thermal: read only for report context / severe events.

The probe must never make a hitch worse merely to measure it.

## Safety/performance constraints

- One display-link monitor maximum for the probe.
- No continuous disk/file logging.
- No per-frame `UserDefaults` access.
- No per-frame JSON/string formatting.
- No full-history/Postbox scan.
- No network telemetry requirement.
- Fixed memory bounds for all diagnostic buffers.
- No strong retention of PeerInfo/chat controllers beyond existing ownership.
- Invalidation/deinit must stop the display link and release diagnostic state owned by a screen/session.
- Prefer release-safe low-overhead code; the probe may be enabled in the sideloaded/release-like build because the user's visible Debug UI is hidden.
- Instrumentation must be cheap enough that a probe-on build can still be compared against current runtime behavior.

## Build/patch-chain integration

Implement this through the existing builder/patch-chain rather than manually editing the materialized Telegram tree.

Use a dedicated apply script, verifier, and test contract. The verifier must confirm:

- probe owner exists exactly once;
- only one `CADisplayLink` diagnostic owner is introduced;
- ring buffer capacity is bounded;
- forbidden per-frame persistence/string/JSON patterns are absent from the probe hot path;
- report access is hidden and attached to a Jerkgram-owned settings/About surface;
- existing Build137 performance caches/invalidation contracts remain present;
- existing avatar `synchronousLoad` behavior is unchanged in this phase;
- existing filtering/history/runtime semantics are not touched.

The workflow should run the new unit/source-contract test before materialization/build.

## Test protocol

### A. Settings / animated avatar

1. Launch Jerkgram and enter Settings.
2. Ensure the animated avatar is active.
3. Rapidly scroll Settings top-to-bottom and bottom-to-top repeatedly for 30-60 seconds.
4. Reproduce at least one visible freeze if possible.
5. Long-press Jerkgram Version and copy the snapshot.
6. Compare severe hitch timestamps against Settings/profile/avatar regions and call-count growth.

### B. Chat / typing

1. Open a representative active chat.
2. Type continuously and repeat entering/leaving text input until the known drop occurs.
3. Copy the snapshot after the event.
4. Compare severe hitch timestamps against chat input, Jerkgram activity/typing policy, and any instrumented transaction boundary.

### C. Probe overhead sanity check

Repeat a short baseline interaction with the probe enabled and confirm:

- idle CPU does not stay materially elevated due to the probe;
- RAM reaches a stable plateau;
- the probe does not create accumulating timers/display links/callback counts of its own;
- no new visible settings/debug UI is introduced.

## Decision after capture

No optimization patch is allowed from this phase without capture evidence.

The next change should target one bounded owner supported by the report. If evidence points outside the instrumented owner set, extend instrumentation one enclosing layer at a time instead of making speculative performance changes.
