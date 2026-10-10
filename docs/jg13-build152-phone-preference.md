# Build152: measured header phone-preference delay

Build151 device report `текст(7).txt`: the user reports freezes again after restart, with the second Settings visit becoming smooth only around 20 seconds. The report does not prove a complete freeze cause or a client-wide fix.

81-second capture, dropped=0. `settings.headerPhonePreference`: 1516 calls, max 210 ms, 350 slow calls; header avatar and cover stages stay below the integer millisecond resolution. Scroll-header: 1465 calls, max 159 ms, 351 slow calls. Parent navigation: 1468 calls, max 159 ms, 354 slow calls; scroll panes max 0 ms. Background preferences max 0 ms and transition/play max 2 ms.

The instrumented phone stage wraps the existing synchronous UserDefaults read of `jerkgram.Appearance.HideOwnPhone`. Repeated 75–115 ms spans occur during the first and second Settings visits and align with parent header spans. This is a measured contributor. The 96 slow-event budget is exhausted around second 36, with 1025 suppressed events overall: absence of later spans cannot prove recovery. Thermal state is 2 throughout; timing differences between runs cannot be attributed exclusively to source changes. After leaving Settings, queue waits reach 321 ms; route identifiers are insufficient to attribute these to a specific chat. Layout/sections/data delays remain separately unresolved.

## Change

Extend the existing locked Display preference snapshot with HideOwnPhone, default false. The header reads the cached value inside the same diagnostic stage. Privacy is independent of the glass master gate. Settings synchronously project the changed key and publish the current value; existing import/account hooks reload it outside the hot lock, guarded by the existing generation check. Older partial publishers preserve the current phone value. No additional observer, worker, timer or playback policy change.

Canonical preferences delta now has four exact owners: Display snapshot, avatar consumer, Settings publisher and the header consumer. P0 patch and manifest remain unchanged. Upstream pin, five regression locks, product and bundle identities are preserved. Build advances to 152.

## Validation

New phone structural contract fails against the Build151 materialization and passes against Build152. Fresh bounded P0 plus preferences materialization and replay pass all 31 contracts; hashes, function survival, five locks, repeat-apply refusal, source git diff check and Python compilation pass. Full legacy suite: 480 tests, 20 failures, 12 errors, identical failing names to the Build151 baseline; see the suite report. Existing tests and verifier remain enabled.

Native fixture executes the actual Display owner behind a counted defaults facade. Added checks cover 10,000 memory-only phone reads, immediate toggles, master independence, legacy publisher preservation, account/import reload, missing false default and rejection of stale refresh overriding live privacy. Native execution awaits CI. Build151 complete job log independently confirms capture strict 32-key cap, secondary synchronizer/legacy detach component PASS, preferences component PASS and IPA metadata VERIFIED; COMPILED, NOT RUNTIME TESTED. Build152 is not yet compiled or runtime tested at preparation time.
