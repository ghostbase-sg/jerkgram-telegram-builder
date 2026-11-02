# Build178 CI fixture correction 1

## Observed failure and diagnosis

The parent task supplied actual macOS run `41508152653`, native job `125492680075`: four native fixture failures; the official checkout key scan passed (33,625 tracked inputs / 33,732 product files) and the app job was skipped. This report does not claim those native failures have passed after correction.

Read the actual native drivers in `tests/test_jg131_botbridge1_history.py` and `tests/test_jg131_botbridge1_diagnostics.py`, shared fixture files, production tuple validation/storage boundaries, and the Task1/Task3 requirements in `docs/superpowers/plans/2026-11-02-botbridge1.md`.

- Lease/storage drivers extract private production types verbatim. Their top-level fixture bindings must therefore be private too. There are five inferred `BotBridgeHistoryPage` bindings, not six: `page`, `bigPage`, `nestedPage`, `aggregatePage`, `conversionPage`; the sixth affected binding across these two fixtures is `lease`.
- The controller helper previously always returned date 21, whereas the candidate date is 20. Its purported nonadvancing slice `(90,4,21,6)` advances from `(90,4,20,6)`. Production correctly compares the entire tuple. Both history and final diagnostics execute this shared controller fixture.

## Exact changes

- `tests/fixtures/botbridge1/lease.swift`: make only `lease` private.
- `tests/fixtures/botbridge1/storage.swift`: make the five page bindings private.
- `tests/fixtures/botbridge1/controller.swift`: add a defaulted `date: Int32 = 21` helper argument; request unchanged date 20 in the nonadvancing case, retaining its terminal/no-mutation assertions. Add an actual-controller scenario where only date advances, verify continued pagination with the saved tuple and next request, then verify later final payload import/completion.

Production source/access levels, extraction drivers, policy, patch, hash manifests, provenance proofs, workflows and all 15 native calls are unchanged.

## Verification

Command (exit 0):

```sh
env JERKGRAM_BOTBRIDGE_SOURCE='/home/pixi/ChatGPT/iOS DEV/jerkgram-next/botbridge1/task3/source' GIT_DIR='/home/pixi/ChatGPT/iOS DEV/jerkgram-next/build177-appfix2-source/.git' python3 tests/run_jg131_botbridge1.py --bot-only
```

Observed output:

```text
BOTBRIDGE1 exact outputs, 16 protected whole modern parents and preference-key scan of 413 product files PASS
BOTBRIDGE1 collision scan scope: supplied source tree only; 413 files
Ran 7 tests ... OK
Ran 9 tests ... OK
Ran 14 tests ... OK (skipped=5)
Ran 24 tests ... OK (skipped=10)
SKIP native final-owner Swift parsing: xcrun unavailable; macOS required
BOTBRIDGE1 portable source gates PASS; native compilation/app/device evidence separate
```

The source proof remains valid. This portable gate checks the supplied 413-file source snapshot; it does not repeat the official full-checkout scan. Native fixtures remain pending macOS because neither `swiftc` nor `xcrun` is available here. All 15 native calls remain present (5 history, 10 diagnostics). The full portable log is `/tmp/botbridge1-ci-fix1-portable.log`.

`git diff --check` passed. No broad suite, heavy build, commit or push was performed by this subtask.
