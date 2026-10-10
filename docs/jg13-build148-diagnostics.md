# Build148: correlate remaining entry freezes

Scope: diagnostic expansion, not a performance fix. Runtime root cause remains unknown.

Canonical seven-owner P0 delta retains all parent hashes and five regression locks. Only three final owner hashes change: profile background/probe, PeerInfoScreen and RAM capture. Build147 preference snapshot and Build146 secondary synchronizer ownership are retained exactly.

Settings detail boundaries:

- `bgPreferences`: loadEnabled only, ending before the disabled-effect guard.
- `bgResolve`: background source resolution and state-key construction, ending before equality guard.
- `bgApply`: changed-source application only.
- `header`: synchronous header.update only.
- `sections`: regular/editing item creation, section updates and removal inside the non-media-only block.
- `panesAndTail`: remaining layout after sections, including panes, selection panels and final scroll/navigation bookkeeping. This is intentionally not a claim to measure pane.update alone.

These six extra summary keys are Settings-only to retain the32-key limit alongside existing peer/Settings/worker counters. Peer baseline counters remain. Timings nest; do not sum them or subtract unrelated maxima.

Slow completed spans >=16.7ms emit stage, local owner sequence, startMs, endMs and durationMs on the capture timeline. No peer/account/resource identifiers are added. One event per stage per second, at most96 events per capture; suppressed count remains visible. Existing limits512 lines,32 timing keys,600 seconds, opt-in Start/Stop/Share/Copy,1Hz utility CPU/peak-RSS/thermal and one pending main pulse remain. No added timer, stack sampling/suspension, disk write or upload.

Main-queue pulses now include submission/completion offsets. This permits interval correlation; it still does not attribute a delayed pulse to a particular function or GPU load. A freeze outside measured boundaries remains possible. A span beginning before capture start is excluded from the new slow-event timeline.

Local validation: clean bounded canonical apply followed by preference delta, all27 structural contracts, unchanged upstream/parent hashes/five locks, repeat-apply refusal, Python compilation and added Swift whitespace checks PASS. Native component and app compilation await CI; no local Swift toolchain is available.

The existing macOS capture test executes the real Foundation/Darwin capture owner and actual probe class with only Logger replaced by a no-op boundary. Added cases check30 stage events versus2970 suppressed repeats,96-event cap, stopped capture, reset and six Settings-only detail keys. Full app build remains required; this component is not UIKit/device profiling.

Device capture after a verified IPA: About → Start; immediately return to Settings, scroll, leave/reopen Settings and continue until the initial freezes settle; About → Stop → Share. Keep this to about60–90 seconds so a single report contains slow and settled phases. Force-terminating the app loses the RAM report, and entering background stops capture. A process cold-start trace is not provided by this opt-in mechanism.
