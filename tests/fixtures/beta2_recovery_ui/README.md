# Beta 2 recovery policy and UI gates

Run `python3 tests/test_jg131_beta2_recovery_ui.py` from the builder checkout.
`JG_BETA2_UI_SOURCE=/absolute/final/source` selects the final composed source,
including in Task 3 CI. No immutable-before checkout is needed by the runner.
`JG_BETA2_UI_REQUIRE_NATIVE=1` makes a missing Swift compiler fail the gate.

Portable assertions cover every disabled policy boundary, the concrete main
Settings `.ghostbase` override and its reconciliation/layout forwarding, same
section Media footer identity, retained storage/state, and byte-identical native
folder consumers, shared theme/accessibility owners and unrelated Settings pages.
`baseline.json` contains SHA-256 evidence taken from immutable Build 178
`recovery/before` at builder `33fffd93b5d3cc207a5ce2492b43292fe09ea6b8`;
upstream is `279f89e4d4f63f17227bf877dc3d8990f22ecd58`.

With Swift available, the runner compiles in both `-Onone` and `-O` and runs:

- The complete production foundation block (including its real UserDefaults
  cache), snapshot/proposal types and the complete production snapshot,
  proposal transaction and prune functions extracted verbatim from the selected
  owner. No policy implementation is copied into fixtures.
- Stored true, missing/default false and stored false; repeated cache/account
  activation updates; stale active/enabled flags; premium unknown/free/paid;
  native order, hidden folders, limits and entitlement projection.
- Current-generation and stale-generation proposals completing with native
  filters while writing neither order domain; disabled prune making no order
  read/write; retained saved order and UserDefaults values.

`shell.swift` provides synchronous value signals, account/view data, and an
in-memory transaction boundary with read/write observation. This lets the real
production closures execute without an app target. It is not Postbox storage,
its binary codec, a real transaction/queue, network, or SwiftSignalKit scheduling.
The JSON bytes are a local fixture retention probe only. UserDefaults fixture
keys are restored at process end. The native fixture has not compiled or run on
the Linux worker because Swift is absent; mandatory macOS execution is pending.

Static UI guards complement the native policy fixture. They do not prove UIKit
type checking, rendering, contrast, Dynamic Type, theme navigation, accessibility
runtime behavior, screenshots, retained-account device launch or app build.
The dark 0.44 value and Jerkgram card scope follow the recovery specification;
no screenshot approval is claimed.
