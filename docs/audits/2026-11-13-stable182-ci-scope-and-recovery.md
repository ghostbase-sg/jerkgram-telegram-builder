# Stable182: compiler scope failure, one product gate, IPA recovery

## Evidence

Failed Actions run: https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/43435343710 (published 4ddfc9c1166698e8ac981848397ed2ed848d053d).
The full app Swift compiler reported `cannot find 'store' in scope` in
`UserApperanceScreen.swift:824`. The local store is declared in the returning
`component.localAppearance` branch; a later server apply condition accidentally
referenced it. Earlier component fixtures omitted that native apply branch;
`swiftc -frontend -parse` checks syntax, not name resolution. Green fixture gates
were insufficient evidence that the app typechecks. No IPA was produced by this
run: compilation failed before link/package.

## Repair

A new exact successor `post181-native-appearance-scope` restores the server branch
condition to `resolvedState.changes.contains(.emojiStatus)`. The local branch keeps
its individual emoji gate, generation protection and local-only update. Earlier
accepted patch bytes stay frozen. Stable182 identity and all optimizations remain.

## Product CI

Previously the reusable historical gate ran before a fresh checkout/build job;
`build_jg13.sh` then repeated almost all historical tests. Normal product builds
now have one job, one pristine pinned checkout, one materialization of all 32
baseline stages plus beta3/post180/post181 successors, and one current Stable182
native/component gate. All exact patch/parent/output hashes and genuine checkout
checks remain fail-closed. Existing configuration generation (including API
credentials) is reused, not replaced. The app compilation and package verification
remain required. Historical feature suites remain available in the separately
invoked `no-ads-native.yml` full regression workflow; they are no longer serial
prerequisites on every product build. This intentionally reduces historical test
coverage per normal build; it does not claim current component fixtures replace
full app compilation or device tests. No claimed time saving until measured in CI.

## IPA preservation

Before packaging, preserve immutable `*-RAW-UNVERIFIED.ipa` plus SHA256, CI commit,
run identity and explicit unverified status. An EXIT trap also preserves a compiled
IPA if Bazel emits it before a later action fails, preserving the original exit
code. Recovery upload runs with `always()`, ignores absent files, retains 90 days.
An existing failed packaging candidate is uploaded separately as
`PACKAGING-FAILED-UNVERIFIED`; successful release artifact still requires success.
Build log is included in always-uploaded diagnostics. No previous IPA is substituted
when compilation creates none. Raw IPA may lack required sideload packaging and is
not a verified release. A forcibly terminated runner cannot guarantee trap/upload.

## Verification

- Focused regression initially RED on all three original cases (native store scope,
  missing raw recovery, duplicated product gates), then GREEN.
- Five focused tests pass: local/server scope separation; raw archive survives
  destructive packaging failure; final verifier failure retains raw and packaged
  archives without success metadata; unchanged build configuration generator;
  workflow gate/recovery wiring.
- Existing package bounded-memory SHA256 tests: 2 pass.
- Current source/component suite passes locally with native tests explicitly
  skipped because Linux has no Swift/xcrun. Mandatory native CI skips remain forbidden.
- Fresh selected-source replay of the new one-pass materializer matches the combined
  candidate for 360 owners. Genuine HEAD/full checkout preconditions mocked only in
  this local projection experiment; all actual stage/hash checks unchanged. CI
  retains the real preconditions. This is source evidence, not a full checkout claim.
- Shell syntax, workflow YAML parsing and git diff whitespace checks pass.
- Full app compilation and iPhone runtime pending the new CI/device run.
