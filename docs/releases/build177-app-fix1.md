# Build177 app preflight fix 1: secondary video observer fixture

## Failure context

App workflow run `41344797195` stopped before Bazel while executing `tests/run_jg13_secondary_timebase.py`. The runner extracts the production `removeSecondaryVideoLayer(_:)` method, which now invalidates `secondaryVideoLayerBoundsObservers`. Its generated `Node` fixture did not define that production field, so the fixture could not compile against the extracted method. This is a fixture-shape failure; no production source, source hash, build identity, or build setting was changed for this fix.

## Change

The fixture now has `secondaryVideoLayerBoundsObservers: [ObjectIdentifier: NSKeyValueObservation]`, matching the production field type. Its fake display layer is an `NSObject` with an `@objc dynamic` bounds property. The generated host Foundation program registers a real KVO observation for a fake layer, mutates bounds and checks one callback, invokes the actual extracted production detach method, confirms the observer dictionary is empty, mutates bounds again and confirms the callback count stays unchanged, then calls detach again to verify idempotence.

Existing synchronizer ownership, legacy manual-timebase, flush, notification, and repeated-detach checks remain. The runner still extracts and executes the production method. The app's build script invocation remains; the source/native workflow now runs this focused runner immediately after the final settings-glass stage, before the combined app build.

## Checks and limits

`python3 -m py_compile tests/run_jg13_secondary_timebase.py` passed. A Python extraction/content check against the fresh Build177 source confirmed that the fixture contains the real extracted invalidation line, the matching Foundation observer dictionary, the KVO registration and callback assertions, and all prior synchronizer/legacy/idempotence assertions. `git diff --check` passed.

This Linux host has no `xcrun` or `swiftc`, so the generated Swift/Foundation KVO program could not be executed here. The fixture uses actual Foundation KVO with an NSObject fake layer; it does not exercise AVFoundation, UIKit, or device playback. The macOS workflow must execute the runner to establish its Swift/KVO result. No native GREEN or Build177 IPA result is claimed by this fix report.
