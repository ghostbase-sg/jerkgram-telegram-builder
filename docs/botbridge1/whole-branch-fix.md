# BOTBRIDGE1 final scoped fix wave

Status: R1 and R2 addressed in the authoritative final Task3 source and terminal patch. Scoped portable evidence PASS. Actual Swift execution/owner parsing, full official generated-source scan, app compilation/IPA and device evidence remain pending. This is the single requested final-review source fix wave; no subagents, commits, publication or heavy builds were performed.

Read the user requirements, decisions, whole-branch review report and the diagnostics/runner extraction plumbing. The review's nine declined-to-judge boundaries remain parent delivery/runtime rulings. No source behavior outside R1/R2 was changed.

## R1: physical record retention

`prune()` retains the existing fail-closed enumeration, mtime/oversize-file cleanup and eight-file cap, then inspects at most eight 256 KiB event files on the sink utility queue. It decodes using the existing export validation bounds (32 KiB line, schema/flags/in-flight limits), removes expired physical records according to their own wall timestamp, and atomically replaces only changed bytes. Consequently a recent active-file mtime cannot extend stale event retention. Successful physical expiry/malformed removals update saturating existing counters only after the replacement succeeds. Enumeration/read/write failure still stops the drain/export and increments storage failure accounting. The export filter remains a final defensive boundary. No polling or main-thread file work was introduced.

The new actual-production fixture seeds stale and recent records into a file with a recent mtime, then separately checks physical disk records after sink initialization/access, a fresh append/drain and export. Recent records remain; three stale records removed on the three accesses produce exactly three retention-expired records. The injectable directory boundary also asserts off-main enumeration. The existing resource/retention and filesystem fail-closed fixtures were not changed.

Cost: lazy access now decodes at most 2 MiB of capped retained event input per prune invocation, plus bounded output for the currently processed file. The work remains off main and has no periodic wakeup. Device timing is unmeasured.

## R2: finite admission loss reasons

The registry now stores three process-local saturating UInt64 counters: `capacity`, `duplicateTarget`, and `invalidGeneration`. Guards classify them separately before returning false, without evicting a live target, creating a rejected-account recorder event or calling the sink. Export reads a locked value copy into `admissionDenied`; no account/record/generation identifiers are exported. Registry mutation does not touch a sink, callbacks or account references, so it adds no inverse sink/registry lock order or recursion. Ordinary-user admission routing is unchanged.

The new actual-production fixture admits 32 live scopes, rejects a duplicate and a 33rd unique target separately, rejects an invalid generation, verifies all original epochs survive, verifies no directory work is scheduled by rejection, and checks each export counter with an otherwise empty report. It also checks no generation UUID appears in the export. These RAM counters reset with the process and are not a durable historical admission ledger.

## Exact artifact/provenance

Final terminal patch SHA256:
`caf968f6071b440ba757977e8eec78f5cef617521c683240230147a36032a5d8`.

All 13 owner before hashes, all non-diagnostics after hashes, upstream/base pins, accepted Task1/Task2 provenance and protected modern proof artifacts are preserved. The other 12 terminal patch sections are byte-for-byte unchanged. The original twelve accepted Swift fixture files remain byte-for-byte unchanged. Task1/Task2 drafts, Task3 `before`, original Build177 source and work pointer were not edited.

The pre-wave full builder snapshot remains at `final-fix-before/`. Initial Task3 reports and exact-stage JSON remain historical evidence and were not overwritten. Final evidence is separate under `final-fix-evidence/`, including exact pre-wave diagnostics reconstructed and digest-checked against the original owner manifest, RED/GREEN output, exact-stage proof, quality checks and final changed-file digests.

## Commands and observed output

From `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder`:

1. Before production edits, ran:
   `JERKGRAM_BOTBRIDGE_SOURCE='/home/pixi/ChatGPT/iOS DEV/jerkgram-next/botbridge1/task3/source' python3 -m unittest discover -s tests -p test_jg131_botbridge1_diagnostics.py -k final_review`.
   Clean RED: four cases; two intended source-guard failures (record TTL absent; separate denial counters absent), two native skips. The first setup invocation happened before the two new fixture files had been written, producing two missing-fixture errors; both files were added and the clean RED was confirmed before production changes. After source edits: four cases, OK, two native skips. The clean RED was also reproduced against the digest-verified exact pre-wave source after patch regeneration; persistent output is `final-fix-evidence/regression-red.log`. This is source-guard evidence, not executed native behavioral evidence.
2. Final covering gate:
   `GIT_DIR='/home/pixi/ChatGPT/iOS DEV/jerkgram-next/build177-appfix2-source/.git' JERKGRAM_BOTBRIDGE_SOURCE='/home/pixi/ChatGPT/iOS DEV/jerkgram-next/botbridge1/task3/source' python3 tests/run_jg131_botbridge1.py --bot-only`.
   Exit 0. Exact outputs, 16 protected whole modern parents and literal preference-key scan of 413 supplied product files PASS. Stage7 + integration9 + history14 + diagnostics24 =54 cases, with15 native skips (5 history,10 diagnostics). Final-owner Swift parse skipped because xcrun is absent. Output is `final-fix-evidence/bot-only-green.log`. The prior 196-case unrelated portable suite was not rerun.
3. `python3 .superpowers/sdd/2026-11-02-botbridge1/final-fix-evidence/exact_stage.py`.
   Exit0. Actual patch application equals every one of415 final product files; reapplication is an exact no-op; corrupting the last existing owner fails before any file mutation; exact reverse-check/application restores every one of413 parent files and removes both new owners. Confirms all13 before hashes, other12 patch sections, portable provenance and all12 accepted native fixtures unchanged. Detailed output is `final-fix-evidence/exact-stage-final.json`. Its sorted file-map digests use compact sorted JSON and are explicitly not Git tree IDs; the older Task3 evidence used a different digest serialization.
4. `python3 -m py_compile tests/test_jg131_botbridge1_diagnostics.py` and `git diff --check`: exit0, no output. Recorded in `final-fix-evidence/quality-checks.json`.

The GIT_DIR is read-only original official Git metadata for existing source/provenance verifiers; it was not copied into portable artifacts or modified.

## Full paths changed by this wave

Product source:

- `/home/pixi/ChatGPT/iOS DEV/jerkgram-next/botbridge1/task3/source/submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift`

Builder delivery/tests:

- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/patches/jg131-botbridge1.patch`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/patches/jg131-botbridge1.sha256.json`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/tests/test_jg131_botbridge1_diagnostics.py`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/tests/fixtures/botbridge1/diagnostic_record_ttl.swift` (new)
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/tests/fixtures/botbridge1/diagnostic_admission_loss.swift` (new)

Local report/evidence:

- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/.superpowers/sdd/2026-11-02-botbridge1/final-fix-report.md`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/.superpowers/sdd/2026-11-02-botbridge1/final-fix-evidence/diagnostics-before.swift.txt`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/.superpowers/sdd/2026-11-02-botbridge1/final-fix-evidence/regression-red.log`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/.superpowers/sdd/2026-11-02-botbridge1/final-fix-evidence/bot-only-green.log`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/.superpowers/sdd/2026-11-02-botbridge1/final-fix-evidence/exact_stage.py`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/.superpowers/sdd/2026-11-02-botbridge1/final-fix-evidence/exact-stage-final.json`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/.superpowers/sdd/2026-11-02-botbridge1/final-fix-evidence/quality-checks.json`
- `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/.superpowers/sdd/2026-11-02-botbridge1/final-fix-evidence/changed-file-digests.json`

No README/cost/scenario/runtime/decisions/audit documents were edited by this agent. Parent documentation should identify the final patch hash above, the54/15 scoped evidence without summing overlapping runs, physical record TTL and the three process-local admission-loss fields. The parent reports those counter descriptions are already present in its runtime/README updates.

## Pending evidence and handoff

The new fixtures execute extracted actual production sink/registry code, but no Swift compiler or xcrun exists here: neither new fixture nor the original native fixtures ran. Required macOS `--require-native --require-full-source`, actual owner compiler/app/IPA and device/server/session checks remain pending. A 413-file supplied-tree scan cannot establish the full official checkout gate. No GREEN app or delivered BOT IPA is claimed.

The scoped fix is ready for review of these source/test/artifact deltas and then the parent's authorized publication/native/app gates. No additional source scope or broad audit is requested.
