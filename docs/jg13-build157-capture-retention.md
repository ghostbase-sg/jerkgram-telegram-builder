# Build157: bounded full-session diagnostic retention

## Evidence and scope

The supplied Build156 v7 capture lasted approximately195 seconds. Its timeline
contained193 utility samples,193 main-queue pulse rows,96 slow spans,12 route
rows and18 auxiliary/lifecycle rows. The512-row ring had already dropped10
earlier rows. Slow examples stopped at63236ms. The32-key table rejected137
later measurements. This is a diagnostic-retention defect, not proof that
keyboard work was cheap or that the freezes are fixed.

Only JerkgramPerformanceDiagnostics.swift changes relative to Build156's
materialized production sources. The canonical expanded patch still has11
owners; pin f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838 and all5 regression locks
remain. UI calls, renderer ownership, primary timebase, playback policy,
animation and blur quality are untouched. Product1.1.0Beta1, bundle
com.jerkgram.ios, short version13.0; build157.

## Fixed storage contract

- Utility sampling remains1Hz with one pending main pulse and600s cutoff.
  Five-second telemetry blocks retain sample counts and maximum sampled CPU,
  peakRSS, thermal state and main-queue wait; they are NOT averages. Waits
  retain submission/completion timestamps and the route at submission. At
  most120 blocks cover the whole session.
- Fixed29 operation summaries count all completed measured calls, with
  separate main/worker counts and maxima, regardless of example retention or
  the legacy timing table. Inclusive nested spans overlap and must not be
  summed. These are synchronous span timings, NOT async completion latency.
- Detailed real-operation examples are worst-per-operation plus worst per
 20-second window, with separate input/send and other pools: at most29+60
  candidate slots, de-duplicated by sample identity. Main-thread examples take
  priority over worker examples in a scheduling window; per-operation thread
  aggregates remain complete. Generic legacy examples share the96-example
  total and can be evicted in favor of real-operation evidence, with an
  explicit counter. Examples are sampled evidence, not every slow call.
- The dynamic timing table remains strictly32 keys. A separate whitelist of
  exactly63 fixed production stages aggregates measurements that overflow
  that table. Unknown labels remain rejected and counted; there is no
  unbounded-key escape hatch.
- Telemetry blocks, unique detailed examples, start/stop boundaries and
  auxiliary ring rows together stay within512 retained timeline rows.
  Auxiliary floods cannot evict critical telemetry/details/boundaries.
  Discarded auxiliary rows are counted. Numeric aggregate tables have the
  fixed bounds above; report summary/header rows are not ring events.
- Status distinguishes seconds elapsed from stored blocks/events. Report
  sections are grouped, not globally time-sorted; timestamps are explicit.
  Stop freezes duration and data. Restart resets all summaries/reservoirs;
  stale tokens and old-session pulses remain rejected.

Capture remains opt-in RAM-only, without automatic upload, file/network I/O,
GPU-utilization claims or rendered-FPS claims.

## Verification before publication

Six initial structural contracts were observed RED against156 and GREEN after
implementation. Fresh bounded canonical application, full before/after hashes,
function survival and five regression locks passed53 structural contracts.
The seventh retention contract also observed RED→GREEN for count-only capture
bookkeeping. Independent review found and resolved a missing window-specific
test and capture-time sorting overhead; no Critical/Important findings remain
in the second static review. Native execution is still required.
Repeat apply was refused. Python compilation, shell syntax and source diff
whitespace checks passed. Original native capture, expanded diagnostics and
secondary-timebase tests are unchanged.

Full legacy Python suite:502 tests,20 failures and12 errors; the same32 failing
names as Build156, listed in jg13-build156-suite-results.md. NOT GREEN.

The new native CI gate executes actual Swift storage/aggregation with only the
monotonic clock and timer scheduling controlled. It exercises180/600 simulated
seconds, full-session operation totals, late keyboard/send/history examples,
peak-preserving telemetry, known overflow stages,5000 auxiliary events, a real
worker thread, stop/restart/stale tokens, and600 seconds of all29 slow labels
after the legacy96-example pool and dynamic32-key table are filled. Existing
tests execute real utility timer expiry and refresh-owner invalidation.
An early larger spike followed by a late smaller span explicitly requires the
window reservoir; input/history in the same window cannot consume one another's
slot, and a longer worker cannot replace its main-thread example. A100000-span
fixture verifies exact totals/one stable example under a generous10s CI overhead
ceiling. That is not a device-performance claim. Reference-counted retention
avoids sorting or formatting unselected candidates during capture.

Native execution and application compilation are pending CI; no local Swift
toolchain is available. No device performance improvement or beta-release
readiness is claimed by this diagnostic change.
