# Build149: remove repeated background preference reads

## Device evidence from Build148

User reports first15 seconds of Settings stutter, chat list smooth, another15 seconds of Settings stutter settling near the end, later repetitions smooth. Report v3/build148,84-second capture,dropped0,26 slow events,19 throttled events.

Measured background preferences:28 calls,6 >=16.7ms,max120ms. Exact nested intervals:767–800ms(33ms),23538–23619ms(80ms),29075–29143ms(68ms),54928–55049ms(120ms). The latter is nested in54928–55056ms background/layout/data, so that call's layout is almost entirely the settings loader. This is direct evidence of elapsed delay in loadEnabled, not proof of which UserDefaults internal operation caused it.

Background resolve max<1ms, apply max5ms; header max58ms,sections max88ms,panes-and-tail max11ms. These other delays remain. The late120ms call occurs after subjective settling, so the loader is a proven individual hitch contributor, not an established complete explanation for the cyclic freeze. High process CPU, peak RSS and player destruction do not establish the remaining cause.

## Bounded implementation

The reviewed three-owner preference delta still has the same parent hashes. Only Display/GhostBaseGlass.swift and SettingsUI/GhostBaseSettingsController.swift outputs change; the avatar transform output is identical. Build148 P0 delta, all five regression locks, pinned upstream13 and secondary synchronizer ownership are unchanged.

GhostBaseGlassStyle now holds the three remaining child preferences alongside the existing master/animated snapshot. loadEnabled returns all four child values with the master gate under one lock. Lazy bootstrap reads defaults once; warmed repeated calls contain no defaults access. Explicit import/account reload reads outside the snapshot lock, retains the generation guard, and publishes every field together. Controller state projects the five profile keys before publishing all values atomically. Existing two-argument setter callers remain source-compatible through optional child arguments that retain current values. Default values, disabled master behavior, animation/blur policy and quality remain identical.

No changes to primary timebase, video playback policy, renderer ownership, animation, blur strength, signing, secrets or Stable history. Header/sections are not altered in this patch. Diagnostics remain v3 with the existing bounds and opt-in export.

## Verification

New source contract failed on Build148's UserDefaults loader, then passed with the memory snapshot. Fresh bounded P0→preferences replay,28 contracts, hashes/function survival, five locks, repeat-apply refusal, Python compilation and git diff check PASS. [Full legacy suite results](jg13-build149-suite-results.md):477 tests,20 failures,12 errors, identical failing names to Build148 baseline; NOT GREEN.

Extended native CI component executes the actual full preference owner and actual loadEnabled struct with a counted defaults boundary. It checks10000 warmed background/transition reads, all-child immediate toggles, master OFF/ON restoration, import defaults, missing-key defaults, stale refresh versus live publication, and overlapping account refresh restoration. No local Swift toolchain; native component/app compilation awaits CI. No runtime performance fix claim.
