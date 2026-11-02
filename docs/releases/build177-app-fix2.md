# Build177 app compiler fix 2: explicit admission capture

Failed app run `41346030214`, job `124967107346`, reports `Translate.swift:180`: weak `self` differs from implicitly captured strong outer closure at line 162; compiler requests an explicit `self` capture list. Baseline builder is `8e16c783b7f0e958e1881f3e58c11c1e533678d9`.

The admission request Signal generator now reads `return Signal { [self] subscriber in`. This makes its existing strong capture explicit across the nested Dispatch closure and weak timer capture. `DispatchWorkItem { [weak self, weak job] in`, timeout cleanup, cancellation, queueing, deduplication and limits are unchanged. Fresh source comparison proves exactly one source file and one line changed.

## Capture fixture and compiler evidence

The existing native policy/admission test already extracts production code with pinned SwiftSignalKit. A new independent native gate extracts the complete actual `JerkgramTranslationAdmission` class verbatim, composes the exact pinned Signal/Disposable/Subscriber/Atomic implementations and compiles with `swiftc -swift-version 5 -warnings-as-errors -typecheck`. It imports real Foundation/Dispatch, so Apple's imported closure capture attributes participate. Only unrelated text/entity and payload-size dependency shapes are supplied; no admission methods are modeled. This focused compile test precedes the existing lifetime/runtime test in the existing translation runner, which runs before the heavy app build.

Exact official `Signal.swift` was fetched with the GitHub connector from TelegramMessenger/Telegram-iOS at `279f89e4d4f63f17227bf877dc3d8990f22ecd58`, `submodules/SSignalKit/SwiftSignalKit/Source/Signal.swift`. It is byte-identical to the existing fixture (SHA256 `f3d6dd93315e8cf4821f92e7fe8dd47ab2aaf636a0e2697fea43a0a897e17c12`). Its initializer is `public init(_ generator: @escaping(Subscriber<T, E>) -> Disposable)`; it has no `@_implicitSelfCapture`. The diagnostic concerns the nested Dispatch capture context, not a fabricated Signal attribute. The new portable contract checks explicit outer `[self]` together with unchanged weak timer captures.

## Files and hash deltas

Builder files changed: `tests/test_jg131_translation_core.py`, `patches/jg131-translation-repair.patch`, `patches/jg131-translation-repair.sha256.json`, `docs/migrations/telegram-13.1.2-stage-chain.json`.

Translate output SHA256:
`1289237c2f91f0cd154a4b36c6fbb39dfb2ca3ea50fdabeb94d15565ec2367c5`
→ `fc71c063661ef363716332cf69561612bde4cdc34e719c956366252d38b84585`.

Terminal TASK A patch SHA256:
`5eb14dc44677a9823fac67109d980162df4d8b06627ba0a80f81057d7a784227`
→ `9bdd9e5c477699049763e590a023a5c25a2cedb4fd7f37d2d2fc25342cf8ca0a`.

Only that owner after-hash and stage patch digest changed in migration provenance. All parent hashes, historical old-before/old-after evidence, other owners, and downstream B/C patch/manifest files remain exact. The generic generator refused a pre-existing unrelated `JerkgramStrings.swift` stage-chain/boundary mismatch (stage-chain after `a087315349ae772a26840c206e0ce5d65b58ceed054d16d51303072db65b4ef4`, terminal manifest/boundary after `e6da4e5c2540fbedf070b992219bd631ad26e65c14d215c3acabdcf78d569768`). Therefore the reviewed terminal patch was updated in place at exactly one added line, with strict parent restoration and all final gates rerun, rather than regenerating unrelated owners or stages.

## Review copies and immutable baseline

`build177/appfix2-before` is the complete source snapshot copied before edits from published `build177-source`. The fresh edited copy is `build177-appfix2-source`. Published `build177-source` and historical `task-a` are untouched. The stage 26 reviewed `after` boundary receives only the same Translate change; its `before` boundary is untouched. Candidate `stage-chain.json` and `regenerated/jg131-translation-repair.{patch,sha256.json}` mirror the controlled terminal update. `APP-FIX2.patch` is the complete builder diff against `8e16c783...` for review.

## Verification and limits

Portable regression was RED on immutable `appfix2-before` (explicit outer capture missing), then GREEN on fresh edited source: 9 tests, 2 native skips. The final TASK C runner passed through restored TASK B, TASK A and all historical source gates using `JERKGRAM_SETTINGS_GLASS_SOURCE` and `JG13_SOURCE` pointing at `build177-appfix2-source`. This exercises exact terminal patch reversal/parent hashes and unchanged downstream ownership. Python compile checks and `git diff --check` passed.

This host has no Swift compiler or xcrun. The CI app compiler failure is the native RED evidence; new native typecheck and all native runtime tests remain PENDING macOS CI. No native GREEN, app build, IPA, runtime behavior, commit, push or build dispatch is claimed.

## Review round 1: compiler gate sensitivity

The dedicated native gate now matches the app's warnings-as-errors policy. In the same fixture it first requires the verbatim fixed production admission to typecheck, then derives the original version by removing only the unique outer `[self]` capture. That version must fail compilation with the weak/strong self capture diagnostic and explicit-capture guidance. Both variants use Swift version 5, actual Dispatch imports, and exact pinned Signal dependencies. This proves fixture sensitivity when run with the pinned macOS compiler; both native outcomes remain PENDING on this Linux host.

The portable core suite was rerun successfully (9 tests, 2 native skips); Python compilation and diff whitespace checks pass. `APP-FIX2-ROUND1.patch` contains only changes since the reviewed working diff: the native gate correction and this report update. No production source, patch owner, manifest, or stage-chain hash changed in this review round.
